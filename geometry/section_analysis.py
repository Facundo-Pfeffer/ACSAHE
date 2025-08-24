import traceback
from tkinter import messagebox

import math
import numpy as np

import plotly.graph_objects as go
from scipy.optimize import fsolve

from materials.acero_pasivo import BarraAceroPasivo
from materials.acero_pretensado import BarraAceroPretensado
from build.utils.excel_manager import ExcelManager
from geometry.section_geometry_engine import Node, Region, ArbitraryCrossSection, CircularRegion
from materials.hormigon import Hormigon
from materials.matrices import MatrizAceroPasivo, MatrizAceroActivo
from build.utils.plotly_engine import ACSAHEPlotlyEngine


def show_message(message, titulo="Mensaje"):
    messagebox.showinfo(titulo, message)


class ACSAHEGeometricSolution:
    #  Both dimensions will be divided in N equal parts.
    rectangular_element_partition_dict = {"Muy Gruesa": 6, "Gruesa": 12, "Media": 30, "Fina": 50, "Muy Fina": 100}
    #  Discretization levels
    niveles_mallado_circular = {"Muy Gruesa": (3, 45), "Gruesa": (6, 30), "Media": (12, 10),
                                "Fina": (25, 5), "Muy Fina": (50, 2)}

    def __init__(self, file_path, read_only=True):
        self.ingreso_datos_sheet, self.armaduras_pasivas_sheet, self.armaduras_activas_sheet, self.diagrama_interaccion_sheet, self.diagrama_interaccion_3D_sheet = None, None, None, None, None
        self.max_x_seccion, self.min_x_seccion, self.max_y_seccion, self.min_y_seccion = None, None, None, None
        self.lista_ang_plano_de_carga = set()
        self.file_name = file_path
        self.read_only = read_only
        self.build()


    def build(self):
        self.excel_manager = ExcelManager(self.file_name, read_only=self.read_only, visible=False)
        self._load_excel_sheets(self.excel_manager)
        self.problema = self._get_result_params()

        self.hormigon, self.acero_pasivo, self.acero_activo, self.estribo = None, None, None, None
        self._load_material_properties()
        try:
            self.seccion_H = self.get_concrete_array()

            self.XG, self.YG = self.seccion_H.xg, self.seccion_H.yg

            self.EEH = self.seccion_H.elements_list  # Matriz Hormigón
            self.EA = self._get_rebar_array()
            self.EAP = self.get_prestressed_bars_array()
            self.seccion_H.Ast = sum([x.area for x in self.EA])
            self.seccion_H.Apt = sum([x.area for x in self.EAP])

            self.deformacion_maxima_de_acero = self._get_max_steel_strain()
            self.planos_de_deformacion = self.get_strain_planes()

            self.ec, self.phix, self.phiy = self._get_initial_prestressed_plain()
            self.ec_plano_deformacion_elastica_inicial = lambda x, y: self.ec + math.tan(math.radians(self.phix)) * (
                y) + math.tan(
                math.radians(self.phiy)) * x
            self.assign_elastic_strains_to_prestressed_bars()
            # self.excel_manager.close()
            # if self.problema["tipo"] == "2D":
                # self.construir_grafica_seccion()  #TODO redo
        except Exception as e:
            traceback.print_exc()
            message = f"Error en la generación de la geometría:\n {e}"
            show_message(message)
            self.excel_manager.close()
            raise e

    def _load_excel_sheets(self, excel_manager):
        self.ingreso_datos_sheet = excel_manager.get_sheet("Ingreso de Datos")
        self.armaduras_pasivas_sheet = excel_manager.get_sheet("Armaduras Pasivas")
        self.armaduras_activas_sheet = excel_manager.get_sheet("Armaduras Activas")
        self.diagrama_interaccion_sheet = excel_manager.get_sheet("Resultados 2D")
        self.diagrama_interaccion_3D_sheet = excel_manager.get_sheet("Resultados 3D")

    def _append_uniaxial_angle(self, ang):
        if ang is not None:
            self.lista_ang_plano_de_carga.add(round(ang, 2))  # Two decimals in degrees.

    def _get_result_params(self):
        rows_range = self.ingreso_datos_sheet.get_n_rows_after_value("RESULTADOS",
                                                                     number_of_rows_after_value=20, columns_range="A")

        type_of_result = self.ingreso_datos_sheet.get_value_on_the_right("Tipo", rows_range, 2)
        verifies_design_loads = self.ingreso_datos_sheet.get_value_on_the_right("Verificación de Estados", rows_range, 2)
        pastes_results_in_wb = self.ingreso_datos_sheet.get_value_on_the_right("Pegar resultados en planilla", rows_range, 2)
        phi_handling_str = self.ingreso_datos_sheet.get_value_on_the_right("ϕ\nFactor de Minoración de Resistencia", rows_range, 2)
        phi_handling_cell = self.ingreso_datos_sheet.get_cell_address_on_the_right("ϕ\nFactor de Minoración de Resistencia", rows_range, 2)
        self._get_uniaxial_angles_list(type_of_result, rows_range)
        puntos_a_verificar = self._get_loading_combinations_points(type_of_result)
        self.lista_ang_plano_de_carga = list(self.lista_ang_plano_de_carga)
        return {
            "tipo": type_of_result,
            "verificacion": isinstance(verifies_design_loads, str) and verifies_design_loads == "Sí",
            "lista_planos_de_carga": list(self.lista_ang_plano_de_carga),
            "puntos_a_verificar": puntos_a_verificar,
            "resultados_en_wb": isinstance(pastes_results_in_wb, str) and pastes_results_in_wb == "Sí",
            "phi_variable": self._get_phi_criteria(phi_handling_str, phi_handling_cell)
        }

    @staticmethod
    def _get_phi_criteria(tratado_de_phi, phi_handling_cell):
        exception = Exception("Valor incorrecto en la celda 'Factor de Minoración de Resistencia ϕ'.\n"
                              "Por favor, ingresar alguno de los valores disponibles en el menú desplegable.")
        try:
            if isinstance(tratado_de_phi, str):
                tratado_de_phi = tratado_de_phi.replace(",", ".")
                tratado_de_phi = tratado_de_phi.replace("\n", " ")
            return float(tratado_de_phi)  # Not float
        except ValueError:
            if isinstance(tratado_de_phi, str):
                if "SELECCIONAR CRITERIO" in tratado_de_phi.upper():
                    cell_address_str = f"Debe seleccionar su valor en el menú desplegable de la celda: {phi_handling_cell[0]}{phi_handling_cell[1]}." if phi_handling_cell is not None else ""
                    raise ValueError(f"ERROR: No ha seleccionado un criterio para el valor de tratado de ϕ. {cell_address_str}")
                elif "CIRSOC 201-2024" in tratado_de_phi.upper():
                    return "según CIRSOC 201-2024"
                elif "CIRSOC 201" in tratado_de_phi.upper():
                    return "según CIRSOC 201-2005"
                else:
                    raise exception
            raise exception

    def _get_uniaxial_angles_list(self, tipo, rows_range):
        if tipo == "2D": # Uniaxial bending, result in 2D.
            self._append_uniaxial_angle(self.ingreso_datos_sheet.get_value_on_the_right("Ángulo plano de carga λ =", rows_range, 2))
        else:  # Biaxial bending, result in 3D.
            cantidad_planos_de_carga = int(
                self.ingreso_datos_sheet.get_value_on_the_right("Cantidad de Planos de Carga", rows_range, 2))
            planos_de_carga_fila = self.ingreso_datos_sheet.get_n_rows_after_value(
                "Cantidad de Planos de Carga",
                cantidad_planos_de_carga + 2,
            )
            for ang in [self.ingreso_datos_sheet.get_value("C", row_n) for row_n in planos_de_carga_fila[2:]]:
                self._append_uniaxial_angle(ang)

    def _get_loading_combinations_points(self, type_of_problem):
        rows_range = tuple(range(46, self.ingreso_datos_sheet.default_rows_range_value[-1]))
        load_combinations_count = self.ingreso_datos_sheet.get_value_on_the_right(
            "Cantidad de Estados", n_column=2, rows_range=rows_range)
        if not load_combinations_count:
            return []
        load_combinations_count = int(load_combinations_count)
        load_combination_row_list = self.ingreso_datos_sheet.get_n_rows_after_value(
            "Cantidad de Estados",
            load_combinations_count + 3,
        )
        load_combinations_list = []
        for combination_row in load_combination_row_list[3:]:
            if type_of_problem == "2D":
                load_combination = {
                    "nombre": self.ingreso_datos_sheet.get_value("A", combination_row),
                    "P": self.ingreso_datos_sheet.get_value("C", combination_row),
                    "M": self.ingreso_datos_sheet.get_value("E", combination_row),
                }
            else:
                plano_de_carga = self.ingreso_datos_sheet.get_value("H", combination_row)
                load_combination = {
                    "nombre": self.ingreso_datos_sheet.get_value("A", combination_row),
                    "P": self.ingreso_datos_sheet.get_value("C", combination_row),
                    "Mx": self.ingreso_datos_sheet.get_value("E", combination_row),
                    "My": self.ingreso_datos_sheet.get_value("G", combination_row),
                    "plano_de_carga": plano_de_carga if plano_de_carga is not None else 0  # se fuerza 0 para estado de solo esfuerzo normal, en el cual en rigor corresponde considerar infinitos planos de carga.
                }
                self._append_uniaxial_angle(load_combination["plano_de_carga"])
            load_combinations_list.append(load_combination)
        if type_of_problem == "3D":
            load_combinations_list = sorted(load_combinations_list, key=lambda x: x["plano_de_carga"])
        return load_combinations_list

    def _load_material_properties(self):

        self.hormigon = Hormigon(tipo=self.ingreso_datos_sheet.get_value("C", "4"))
        self.tipo_estribo = self.ingreso_datos_sheet.get_value("C", "10")

        def_de_rotura_a_pasivo = self.obtener_def_de_rotura_a_pasivo()
        self.set_rebar_properties(def_de_rotura_a_pasivo)

        def_de_pretensado_inicial = self._get_initial_prestressed_strain()
        self.def_de_pretensado_inicial = def_de_pretensado_inicial
        self.setear_propiedades_acero_activo(def_de_pretensado_inicial)

    def _get_initial_prestressed_plain(self):
        """Gets the paratemers of the initial section elastic deformation, based on the prestressing action."""
        if not self.EAP:  # Caso de Hormigón Armado
            return 0, 0, 0
        non_linear_solution = fsolve(
            self.strain_function_to_converge, [-BarraAceroPretensado.deformacion_de_pretensado_inicial, 0, 0],
            maxfev=50, full_output=1)

        if not (non_linear_solution[2]):
            raise Exception("No se encontró deformación inicial que satisfaga las ecuaciones de equilibrio")
        ec, phix, phiy = non_linear_solution[0]
        return ec, phix, phiy

    def strain_function_to_converge(self, strains):
        (ec, phix, phiy) = strains
        return self.get_baricentric_section_forces(ec, phix, phiy)

    def _get_max_steel_strain(self):
        def_max_acero_pasivo = BarraAceroPasivo.eu
        def_max_acero_activo = BarraAceroPretensado.epu
        return min(def_max_acero_pasivo, def_max_acero_activo)

    def obtener_def_de_rotura_a_pasivo(self):
        problem_type = self.ingreso_datos_sheet.get_value("C", "6")
        possible_reinforcement_options = {"ADN 420": "B", "ADN 500": "C", "AL 220": "D", "Provisto por Usuario": "E"}
        value = self.armaduras_pasivas_sheet.get_value(possible_reinforcement_options.get(problem_type, "B"), 5)
        return value

    def _get_initial_prestressed_strain(self):
        value = self.ingreso_datos_sheet.get_value("E", 8)
        return value / 1000

    def _get_mesh_characteristics(self):
        return {
            "ΔX": f"{round(self.seccion_H.dx, 2)} cm" if self.seccion_H.dx else None,
            "ΔY": f"{round(self.seccion_H.dy, 2)} cm" if self.seccion_H.dy else None,
            "Δr": f"{round(self.seccion_H.dr, 2)} cm" if self.seccion_H.dr else None,
            "Δθ": f"{round(self.seccion_H.d_ang, 2)}°" if self.seccion_H.d_ang else None}

    def _get_colors_kwargs(self, plano_de_def, arcoiris=False, blanco_y_negro=False):
        lista_colores = ["k", "r", "b", "g", "c", "m", "y", "k"]
        if arcoiris:
            return {"color": self.numero_a_color_arcoiris(abs(plano_de_def[3]))}
        return {"c": lista_colores[abs(plano_de_def[2])] if blanco_y_negro is False else "k"}

    def get_strain_planes(self):
        """Obtiene una lista de los planos de deformación últimos a utilizarse para determinar los estados de resistencia
        últimos, cada element de esta lista representa, en principio, un punto sobre el diagrama de interacción.
        Este puede no ser el caso si hay puntos para los cuales no se encuentra una convergencia, en ese caso será
        descartado."""
        plane_list = []
        try:
            for j in range(350):
                if j <= 25:
                    final_strain = -0.5
                    top_strain = -3
                    bottom_strain = -3 + (final_strain + 3) * j / (25)  # Hasta -0.3
                    plane_index = 1
                elif 25 < j <= 100:
                    def_inicial = -0.5
                    final_strain = 0
                    top_strain = -3
                    bottom_strain = def_inicial + (final_strain - def_inicial) * (j - 25) / (100 - 25)  # Hasta 0
                    plane_index = 2
                elif 100 < j <= 200:
                    top_strain = -3
                    bottom_strain = 10 * (j - 100) / (200 - 100)
                    plane_index = 3
                elif 200 < j <= 275:  # Hasta la deformación máxima del acero.
                    top_strain = -3
                    bottom_strain = 10 + (j - 200) * (self.deformacion_maxima_de_acero * 1000 - 10) / (275 - 200)
                    plane_index = 4
                elif j <= 325:
                    top_strain = -3 + (6 + 3) * (j - 275) / (325 - 275)
                    bottom_strain = self.deformacion_maxima_de_acero * 1000
                    plane_index = 5
                else:
                    top_strain = 6 + (self.deformacion_maxima_de_acero * 1000 - 6) * (j - 325) / (350 - 326)
                    bottom_strain = self.deformacion_maxima_de_acero * 1000
                    plane_index = 6
                plane_list.append((top_strain / 1000, bottom_strain / 1000, plane_index, j))
        except AttributeError as e:
            pass
        inverted_plane_list = [(x[1], x[0], -x[2], -x[3]) for x in plane_list]  # Misma lista, invertida de sign
        return plane_list + inverted_plane_list

    def assign_elastic_strains_to_prestressed_bars(self):
        ec_plano = self.ec_plano_deformacion_elastica_inicial
        for elemento_pretensado in self.EAP:
            elemento_pretensado.def_elastica_hormigon_perdidas = ec_plano(elemento_pretensado.xg,
                                                                          elemento_pretensado.yg)

    def _get_rebar_array(self):
        rows_list = self.ingreso_datos_sheet.get_rows_range_between_values(
            ("ARMADURAS PASIVAS (H°- Armado)", "ARMADURAS ACTIVAS (H°- Pretensado)"),
            columns_range=["A"])
        result_array = MatrizAceroPasivo()
        for row_number in rows_list[5:-1]:
            x, y, d, i = self._get_rebar_excel_values(row_number)
            if d == 0:
                continue
            xg = round(x - self.XG, 3)
            yg = round(y - self.YG, 3)
            result_array.append(BarraAceroPasivo(xg, yg, d, i))
        return result_array

    def _get_rebar_excel_values(self, row_number):
        return (self.ingreso_datos_sheet.get_value("C", row_number),
                self.ingreso_datos_sheet.get_value("E", row_number),
                self.ingreso_datos_sheet.get_value("G", row_number),
                self.ingreso_datos_sheet.get_value("A", row_number))

    def set_rebar_properties(self, def_de_rotura_a_pasivo):
        try:
            tipo = self.ingreso_datos_sheet.get_value("C", "6")
            self.acero_pasivo = tipo
            if tipo == "Provisto por usuario":
                valores = {
                    "tipo": "Provisto por usuario",
                    "fy": self.armaduras_pasivas_sheet.get_value("E", "3")/10,
                    "E": self.armaduras_pasivas_sheet.get_value("E", "4")/10,
                    "eu": self.armaduras_pasivas_sheet.get_value("E", "5")
                }

                if not all(bool(v) for k, v in valores.items()):
                    raise Exception("Usted ha seleccionado Acero Pasivo tipo 'Provisto por usuario'\n"
                                    "Pero no ha ingresado todos los parámetros necesarios. Por favor,"
                                    " diríjase a pestaña 'Armaduras Pasivas' e intentelo de nuevo.")

            else:
                values = BarraAceroPasivo.default_strain_stress_relation_vars.get(tipo)
                for k, v in values.items():
                    self.__setattr__(k, v)
                fy = BarraAceroPasivo.default_strain_stress_relation_vars.get(tipo.upper())["fy"]
                BarraAceroPasivo.E = 20000
                BarraAceroPasivo.tipo = tipo
                BarraAceroPasivo.fy = fy/10
                BarraAceroPasivo.eu = def_de_rotura_a_pasivo
        except Exception:
            raise Exception("No se pudieron setear las propiedades del acero pasivo, revise configuración")

    def get_prestressed_bars_array(self):
        lista_filas = self.ingreso_datos_sheet.get_rows_range_between_values(
            ("ARMADURAS ACTIVAS (H°- Pretensado)", "DISCRETIZACIÓN DE LA SECCIÓN"),
            columns_range=["A"])
        resultado = MatrizAceroActivo()
        for fila in lista_filas[5:-1]:
            x, y, area, i = self._get_rebar_excel_values(fila)
            if area == 0:
                continue
            xg = round(x - self.XG, 3)
            yg = round(y - self.YG, 3)
            resultado.append(BarraAceroPretensado(xg, yg, area, i))
        return resultado

    def setear_propiedades_acero_activo(self, def_de_pretensado_inicial):
        try:
            tipo = self.ingreso_datos_sheet.get_value("C", "8")
            tipo = tipo
            self.acero_activo = tipo
            if tipo == "Provisto por usuario":
                valores = {
                    "tipo": "Provisto por usuario",
                    "Eps": self.armaduras_activas_sheet.get_value("E", "3"),
                    "fpy": self.armaduras_activas_sheet.get_value("E", "4"),
                    "fpu": self.armaduras_activas_sheet.get_value("E", "5"),
                    "epu": self.armaduras_activas_sheet.get_value("E", "6"),
                    "N": self.armaduras_activas_sheet.get_value("E", "7"),
                    "K": self.armaduras_activas_sheet.get_value("E", "8"),
                    "Q": self.armaduras_activas_sheet.get_value("E", "9"),
                    "deformacion_de_pretensado_inicial": def_de_pretensado_inicial
                }

                if not all(bool(v) for k, v in valores.items()):
                    raise Exception("Usted ha seleccionado Acero Pasivo tipo 'Provisto por usuario'\n"
                                    "Pero no ha ingresado todos los parámetros necesarios. Por favor,"
                                    " diríjase a pestaña 'Armaduras Pasivas' e intentelo de nuevo.")

                for k, v in valores.items():
                    if k in ["fpy", "fpu", "Eps"]:
                        v = v / 10  # kN/cm²
                    setattr(BarraAceroPretensado, k, v)

            else:
                values = BarraAceroPretensado.default_strain_stress_relation_vars.get(tipo.upper())
                for k, v in values.items():
                    setattr(BarraAceroPretensado, k, v)
                BarraAceroPretensado.tipo = tipo
                BarraAceroPretensado.Eps = 20000  # kN/cm²
                BarraAceroPretensado.deformacion_de_pretensado_inicial = def_de_pretensado_inicial
            temp_bar = BarraAceroPretensado(0, 0, 0, 0)
            BarraAceroPretensado.fse = temp_bar.stress_strain_eq(temp_bar.deformacion_de_pretensado_inicial)
        except Exception as e:
            raise Exception("No se pudieron establecer las propiedades del acero activo, revise configuración")

    def _get_index(self, region):
        value = self.ingreso_datos_sheet.get_value("A", region[0])
        return value.split()[-1]

    def _get_sign(self, region):
        value = self.ingreso_datos_sheet.get_value("C", region[0])
        return +1 if "Pos" in value else -1

    def _get_section_type(self, region):
        value = self.ingreso_datos_sheet.get_value("E", region[0])
        return value

    def _get_number_of_nodes(self, region):
        return self.ingreso_datos_sheet.get_value("G", region[0])

    def get_concrete_array(self):
        filas_hormigon = self.ingreso_datos_sheet.get_rows_range_between_values(
            ("GEOMETRÍA DE LA SECCIÓN DE HORMIGÓN", "ARMADURAS PASIVAS (H°- Armado)"),
            columns_range=["A"])
        concrete_shapes_list = self.ingreso_datos_sheet.subdivide_range_in_contain_word("A", filas_hormigon, "Contorno")
        concrete_polygons = {}
        node_coordinates_list = []
        max_x, min_x = [], []
        max_y, min_y = [], []
        delta_x = []
        delta_y = []
        for i, filas_region in enumerate(concrete_shapes_list):
            sign = self._get_sign(filas_region)
            shape_type = self._get_section_type(filas_region)
            indice = self._get_index(filas_region)
            if shape_type == "Poligonal":
                cantidad_de_nodos = int(self._get_number_of_nodes(filas_region))
                for fila_n in self.ingreso_datos_sheet.get_n_rows_after_value("Nodo Nº", cantidad_de_nodos + 1,
                                                                              rows_range=filas_region)[1:]:
                    x = self.ingreso_datos_sheet.get_value("C", fila_n)
                    y = self.ingreso_datos_sheet.get_value("E", fila_n)
                    node_coordinates_list.append(Node(round(x, 3), round(y, 3)))  # Medidas en centímetros
                concrete_shape = Region(node_coordinates_list, sign, indice, sort_nodes=True)
                if sign > 0:  # Solo se utilizan los regions positivos para definir la discretización
                    max_x.append(max(concrete_shape.x))
                    min_x.append(min(concrete_shape.x))
                    max_y.append(max(concrete_shape.y))
                    min_y.append(min(concrete_shape.y))
                    delta_x.append(abs(max(concrete_shape.x) - min(concrete_shape.x)))
                    delta_y.append(abs(max(concrete_shape.y) - min(concrete_shape.y)))
                concrete_polygons[str(i + 1)] = concrete_shape
                node_coordinates_list = []
            elif shape_type == "Circular":
                x = self.ingreso_datos_sheet.get_value_on_the_right("Nodo Centro", filas_region, 2)
                y = self.ingreso_datos_sheet.get_value_on_the_right("Nodo Centro", filas_region, 4)
                r_int = self.ingreso_datos_sheet.get_value_on_the_right("Radio Interno [cm]", filas_region, 2)
                r_ext = self.ingreso_datos_sheet.get_value_on_the_right("Radio Externo [cm]", filas_region, 2)
                if sign > 0:
                    max_x.append(x + r_ext)
                    min_x.append(x - r_ext)
                    max_y.append(y + r_ext)
                    min_y.append(y - r_ext)
                    delta_x.append(r_ext - r_int)
                    delta_y.append(r_ext - r_int)
                concrete_polygons[str(i + 1)] = CircularRegion(centroid_node=Node(x, y), indice=indice, boundary_radii_list=(r_int, r_ext),
                                                                 sign=sign)
            else:
                pass
        self.max_x_seccion = max(max_x)
        self.min_x_seccion = min(min_x)
        self.max_y_seccion = max(max_y)
        self.min_y_seccion = min(min_y)
        EEH = ArbitraryCrossSection(concrete_polygons, mesh_data=self.get_discretizacion(delta_x, delta_y, concrete_polygons))
        return EEH

    def get_discretizacion(self, delta_x, delta_y, regions):
        hay_region_circular = any(isinstance(v, CircularRegion) for k, v in regions.items())
        hay_region_rectangular = any(not isinstance(x, CircularRegion) for x in regions)
        rows_range = self.ingreso_datos_sheet.get_n_rows_after_value("DISCRETIZACIÓN DE LA SECCIÓN",
                                                                     number_of_rows_after_value=20, columns_range="A")
        nivel_discretizacion = self.ingreso_datos_sheet.get_value_on_the_right("Nivel de Discretización", rows_range, 2)
        self.nivel_disc = nivel_discretizacion
        if nivel_discretizacion == "Avanzada (Ingreso Manual)":
            dx = self.ingreso_datos_sheet.get_value_on_the_right("ΔX [cm] =", rows_range, 2)
            dy = self.ingreso_datos_sheet.get_value_on_the_right("ΔY [cm] =", rows_range, 2)
            d_ang = self.ingreso_datos_sheet.get_value_on_the_right("Δθ [°] =", rows_range, 2)
            return (dx if hay_region_rectangular else None,
                    dy if hay_region_rectangular else None,
                    min(dx, dy) if hay_region_circular else None,
                    d_ang if hay_region_circular else None)
        factor_rectangular = 1 / self.rectangular_element_partition_dict.get(nivel_discretizacion)
        factor_circular = self.niveles_mallado_circular.get(nivel_discretizacion)

        return (factor_rectangular * max(delta_x) if hay_region_rectangular else None,
                factor_rectangular * max(delta_y) if hay_region_rectangular else None,
                factor_circular[0] if hay_region_circular else None,
                factor_circular[1] if hay_region_circular else None)

    def get_baricentric_section_forces(self, ec, phix, phiy):
        ecuacion_plano_deformacion = lambda x, y: ec + math.tan(math.radians(phix)) * (y) + math.tan(
            math.radians(phiy)) * (x)
        sumFA = sumFP = sumFH = 0
        MxA = MxAP = MxH = 0
        MyA = MyAP = MyH = 0
        for barra in self.EA:
            def_elemento, area = ecuacion_plano_deformacion(barra.xg, barra.yg), barra.area
            FA = barra.stress_strain_eq(def_elemento) * area
            sumFA = sumFA + FA
            MxA = FA * barra.yg + MxA
            MyA = -FA * barra.xg + MyA
        for barra_p in self.EAP:
            deformacion_elastica_hormingon, area = ecuacion_plano_deformacion(barra_p.xg, barra_p.yg), barra_p.area
            deformacion_pretensado_inicial = barra_p.deformacion_de_pretensado_inicial
            deformacion_total = deformacion_elastica_hormingon + deformacion_pretensado_inicial

            Fp = barra_p.stress_strain_eq(deformacion_total) * area
            sumFP = sumFP + Fp
            MxAP = Fp * barra_p.yg + MxAP
            MyAP = -Fp * barra_p.xg + MyAP

        for element in self.EEH:
            def_elemento, area = ecuacion_plano_deformacion(element.xg, element.yg), element.area
            F_hor = self.hormigon.elastic_stress_strain_eq(def_elemento) * area
            sumFH = sumFH + F_hor
            MxH = F_hor * element.yg + MxH
            MyH = -F_hor * element.xg + MyH

        sumF = sumFA + sumFP + sumFH
        Mx = round(MxA + MxAP + MxH, 8)
        My = round(MyA + MyAP + MyH, 8)

        return [sumF, Mx, My]

    def print_result_tridimensional(self, ec, phix, phiy):
        ec_plano = lambda x, y: ec + math.tan(math.radians(phix)) * y + math.tan(math.radians(phiy)) * x
        self.seccion_H.mostrar_regions_3d(ecuacion_plano_a_desplazar=ec_plano)

    def construir_grafica_seccion_plotly(self, fig=None):
        """Muestra la sección obtenida luego del proceso de discretización."""

        x_range = self.seccion_H.x_max - self.seccion_H.x_min
        y_range = self.seccion_H.y_max - self.seccion_H.y_min
        common_range = max(x_range, y_range) * 1.1

        # Center the common range around the midpoints of the original ranges
        x_mid = (self.seccion_H.x_max + self.seccion_H.x_min) / 2
        y_mid = (self.seccion_H.y_max + self.seccion_H.y_min) / 2

        if not fig:
            fig = go.Figure(layout_template="plotly_white")
        fig.update_yaxes(
            scaleanchor="x",
            scaleratio=1,
        )

        plotly_util = ACSAHEPlotlyEngine(fig)
        plotly_util.plot_reinforcement_bars_as_circles(self.EA, self.EAP)

        self.seccion_H.plotly(fig, self.lista_ang_plano_de_carga)

        fig.update_layout(
            xaxis=dict(
                title='<span style="font-size: 20px;">X</span><span style="font-size: 14px;"> baricéntrica</span><span style="font-size: 20px;"> [cm]</span>',
                title_font=dict(family='Times New Roman'),
                showticklabels=True, showgrid=True,
                zeroline=True,
                range=[x_mid - common_range / 2, x_mid + common_range / 2]
            ),
            yaxis=dict(
                title='<span style="font-size: 20px;">Y</span><span style="font-size: 14px;"> baricéntrica</span><span style="font-size: 20px;"> [cm]</span>',
                title_font=dict(family='Times New Roman', size=12),
                zeroline=True,
                showticklabels=True, showgrid=True,
                range=[y_mid - common_range / 2, y_mid + common_range / 2]
            )
        )
        return fig

    @staticmethod
    def get_3d_coordinates(list_of_results_2d):
        X, Y, Z = [], [], []
        color_list = []
        phi_list = []
        plano_def = []
        is_capped_list = []
        if not list_of_results_2d:
            return None
        for result in list_of_results_2d:
            x = -result["Mx"] / 100
            y = -result["My"] / 100
            z = -result["sumF"]  # Negative so compression points lye on quadrants I and II
            X.append(x)
            Y.append(y)
            Z.append(z)
            phi_list.append(result["phi"])
            plano_def.append(result["plano_de_deformacion"])
            color = result["color"]
            color_list.append(f"rgb({color[0]},{color[1]},{color[2]})")
            is_capped_list.append(result["is_capped"])

        return (X, Y, Z, phi_list), color_list, is_capped_list

    def insertar_valores_2D(self, data_subset, lista_puntos_a_verificar):
        self.excel_manager = ExcelManager(self.file_name, read_only=False, visible=True)
        self._load_excel_sheets(self.excel_manager)
        diagrama_de_interaccion_sheet = self.diagrama_interaccion_sheet
        for k, v in data_subset.items():
            lista_x_total = [(1 if x > 0 else -1 if x!=0 else 1 if y>=0 else -1) * math.sqrt(x ** 2 + y ** 2) for x, y in
                             zip(v["x"], v["y"])].copy()
            list_values = np.array([v["z"], lista_x_total, v["phi"]])
            list_values = list_values.transpose().tolist()

            diagrama_de_interaccion_sheet.change_cell_value_by_range("G1", k)
            diagrama_de_interaccion_sheet.insert_values_vertically("I3", list_values, columns_to_clean=["I", "J", "K"], start_row=3)

            X = [x["M"] for x in lista_puntos_a_verificar]
            Y = [x["P"] for x in lista_puntos_a_verificar]

            puntos_a_verificar = np.array([Y, X]).transpose().tolist()
            diagrama_de_interaccion_sheet.insert_values_vertically("N3", puntos_a_verificar, columns_to_clean=["N", "O"], start_row=3)
            self.excel_manager.close()

    def insertar_valores_3D(self, data_subset):
        excel_manager = ExcelManager(self.file_name, read_only=False)
        diagrama_de_interaccion_sheet = excel_manager.get_sheet("Resultados 3D")

        i = 0  # contador
        for k, v in data_subset.items():
            list_values = np.array([v["x"], v["y"], v["z"], v["phi"]])
            list_values = list_values.transpose().tolist()
            if i == 0:  # Poniendo el valor de lambda en la primera celda
                diagrama_de_interaccion_sheet.change_cell_value_by_range("A1", f"λ= {k}°")
                diagrama_de_interaccion_sheet.delete_contents_from_column(6)
                diagrama_de_interaccion_sheet.insert_values_vertically("A4", list_values, start_row=4)
                i = i + 1
                continue
            new_range = diagrama_de_interaccion_sheet.calculate_new_range_by_coll_offset("A1:D3", column_offset=5 * i)
            diagrama_de_interaccion_sheet.copy_paste_range("A1:D3", new_range)
            top_bottom_cell = new_range.split(":")[0]
            diagrama_de_interaccion_sheet.change_cell_value_by_range(top_bottom_cell, f"λ= {k} °")
            diagrama_de_interaccion_sheet.insert_values_vertically(
                diagrama_de_interaccion_sheet.shift_cell_by_offset(top_bottom_cell, col_offset=0, row_offset=3),
                list_values,
                start_row=4)
            i = i + 1
        self.excel_manager.close()
