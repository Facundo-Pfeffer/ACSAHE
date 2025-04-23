import os
import traceback
from tkinter import messagebox

import math
import numpy as np

import plotly.graph_objects as go
from scipy.optimize import fsolve

from materials.acero_pasivo import BarraAceroPasivo
from materials.acero_pretensado import BarraAceroPretensado
from build.utils.excel_manager import ExcelManager, ExcelSheetManager
from geometry.section_geometry_engine import Node, Contorno, SeccionArbitraria, Segment, ContornoCircular
from materials.hormigon import Hormigon
from materials.matrices import MatrizAceroPasivo, MatrizAceroActivo
from build.utils.plotly_engine import ACSAHEPlotlyEngine


def show_message(message, titulo="Mensaje"):
    messagebox.showinfo(titulo, message)


class ACSAHEGeometricSolution:
    #  Cantidades de partes en las cuales se divide
    niveles_mallado_rectangular = {"Muy Gruesa": 6, "Gruesa": 12, "Media": 30, "Fina": 50, "Muy Fina": 100}
    #  Los niveles de discretizacion: ([parámetro en función logaritmica (ver ],
    niveles_mallado_circular = {"Muy Gruesa": (3, 45), "Gruesa": (6, 30), "Media": (12, 10),
                                "Fina": (25, 5), "Muy Fina": (50, 2)}

    def __init__(self, file_path):
        self.ingreso_datos_sheet, self.armaduras_pasivas_sheet, self.armaduras_activas_sheet, self.diagrama_interaccion_sheet, self.diagrama_interaccion_3D_sheet = None, None, None, None, None
        self.max_x_seccion, self.min_x_seccion, self.max_y_seccion, self.min_y_seccion = None, None, None, None
        self.lista_ang_plano_de_carga = set()
        self.file_name = file_path
        try:
            self.build()
        except Exception as e:
            traceback.print_exc()
            message = f"Error en la generación de la geometría:\n{e}"
            show_message(message)
            raise e

    def build(self):
        with ExcelManager(self.file_name) as excel_manager:
            self.cargar_hojas_de_calculo(excel_manager)
            self.problema = self.obtener_problema_a_resolver()

            self.hormigon, self.acero_pasivo, self.acero_activo, self.estribo = None, None, None, None
            self.cargar_propiedades_materiales()

            self.seccion_H = self.obtener_matriz_hormigon()

            self.XG, self.YG = self.seccion_H.xg, self.seccion_H.yg

            self.EEH = self.seccion_H.elementos  # Matriz Hormigón
            self.EA = self.obtener_matriz_acero_pasivo()
            self.EAP = self.obtener_matriz_acero_pretensado()
            self.seccion_H.Ast = sum([x.area for x in self.EA])
            self.seccion_H.Apt = sum([x.area for x in self.EAP])

            self.deformacion_maxima_de_acero = self.obtener_deformacion_maxima_de_acero()
            self.planos_de_deformacion = self.obtener_planos_de_deformacion()

            self.ec, self.phix, self.phiy = self.obtener_plano_deformación_inicial_pretensado()
            # self.print_result_tridimensional(ec, phix, phiy)
            self.ec_plano_deformacion_elastica_inicial = lambda x, y: self.ec + math.tan(math.radians(self.phix)) * (
                y) + math.tan(
                math.radians(self.phiy)) * x
            self.asignar_deformacion_hormigon_a_elementos_pretensados()
            # if self.problema["tipo"] == "2D":
                # self.construir_grafica_seccion()  #TODO redo

    def cargar_hojas_de_calculo(self, excel_manager):
        """Inicializa las hojas de cálculo a partir de ExcelManager."""
        self.ingreso_datos_sheet = excel_manager.get_sheet("Ingreso de Datos")
        self.armaduras_pasivas_sheet = excel_manager.get_sheet("Armaduras Pasivas")
        self.armaduras_activas_sheet = excel_manager.get_sheet("Armaduras Activas")
        self.diagrama_interaccion_sheet = excel_manager.get_sheet("Resultados 2D")
        self.diagrama_interaccion_3D_sheet = excel_manager.get_sheet("Resultados 3D")

    def agregar_ang(self, ang):
        """Normaliza a 2 decimales para que no haya incompatibilidades entre los elementos."""
        if ang is not None:
            self.lista_ang_plano_de_carga.add(round(ang, 2))

    def obtener_problema_a_resolver(self):
        rows_range = self.ingreso_datos_sheet.get_n_rows_after_value("RESULTADOS",
                                                                     number_of_rows_after_value=20, columns_range="A")

        tipo = self.ingreso_datos_sheet.get_value_on_the_right("Tipo", rows_range, 2)
        verificacion = self.ingreso_datos_sheet.get_value_on_the_right("Verificación de Estados", rows_range, 2)
        resultados_en_wb = self.ingreso_datos_sheet.get_value_on_the_right("Pegar resultados en planilla", rows_range, 2)
        tratado_de_phi = self.ingreso_datos_sheet.get_value_on_the_right("ϕ\nFactor de Minoración de Resistencia", rows_range, 2)
        self.obtener_planos_de_cargados(tipo, rows_range)
        puntos_a_verificar = self.obtener_puntos_a_verificar(tipo)
        self.lista_ang_plano_de_carga = list(self.lista_ang_plano_de_carga)
        return {
            "tipo": tipo,
            "verificacion": isinstance(verificacion, str) and verificacion == "Sí",
            "resultados_en_wb": isinstance(resultados_en_wb, str) and resultados_en_wb == "Sí",
            "lista_planos_de_carga": list(self.lista_ang_plano_de_carga),
            "puntos_a_verificar": puntos_a_verificar,
            "phi_variable": self.get_phi_variable(tratado_de_phi)
        }

    @staticmethod
    def get_phi_variable(tratado_de_phi):
        exception = Exception("Valor incorrecto en la celda 'Factor de Minoración de Resistencia'.\n"
                            "Por favor, ingresar solo numeros o el valor predeterminado Variable según CIRSOC 201")
        try:
            if isinstance(tratado_de_phi, str):
                tratado_de_phi.replace(",", ".")  # Adaptación a más de un tipo de input.
            return float(tratado_de_phi)
        except ValueError:
            if isinstance(tratado_de_phi, str):
                if "CIRSOC 201-2024" in tratado_de_phi.upper():
                    return "según CIRSOC 201-2024"
                elif "CIRSOC 201" in tratado_de_phi.upper():
                    return "según CIRSOC 201-2005"
                else:
                    raise exception
            raise exception

    def obtener_planos_de_cargados(self, tipo, rows_range):
        if tipo == "2D":
            self.agregar_ang(self.ingreso_datos_sheet.get_value_on_the_right("Ángulo plano de carga λ =", rows_range, 2))
        else:  # 3D
            cantidad_planos_de_carga = int(
                self.ingreso_datos_sheet.get_value_on_the_right("Cantidad de Planos de Carga", rows_range, 2))
            planos_de_carga_fila = self.ingreso_datos_sheet.get_n_rows_after_value(
                "Cantidad de Planos de Carga",
                cantidad_planos_de_carga + 2,
            )
            for ang in [self.ingreso_datos_sheet.get_value("C", row_n) for row_n in planos_de_carga_fila[2:]]:
                self.agregar_ang(ang)

    def obtener_puntos_a_verificar(self, tipo):
        rows_range = tuple(range(46, self.ingreso_datos_sheet.default_rows_range_value[-1]))
        cantidad_de_estados = self.ingreso_datos_sheet.get_value_on_the_right(
            "Cantidad de Estados", n_column=2, rows_range=rows_range)
        if not cantidad_de_estados:
            return []
        cantidad_de_estados = int(cantidad_de_estados)
        estados_fila_lista = self.ingreso_datos_sheet.get_n_rows_after_value(
            "Cantidad de Estados",
            cantidad_de_estados + 3,
        )
        lista_estados = []
        for estado_fila in estados_fila_lista[3:]:
            if tipo == "2D":
                estado = {
                    "nombre": self.ingreso_datos_sheet.get_value("A", estado_fila),
                    "P": self.ingreso_datos_sheet.get_value("C", estado_fila),
                    "M": self.ingreso_datos_sheet.get_value("E", estado_fila),
                }
            else:
                plano_de_carga = self.ingreso_datos_sheet.get_value("H", estado_fila)
                estado = {
                    "nombre": self.ingreso_datos_sheet.get_value("A", estado_fila),
                    "P": self.ingreso_datos_sheet.get_value("C", estado_fila),
                    "Mx": self.ingreso_datos_sheet.get_value("E", estado_fila),
                    "My": self.ingreso_datos_sheet.get_value("G", estado_fila),
                    "plano_de_carga": plano_de_carga if plano_de_carga is not None else 0  # se fuerza 0 para estado de solo esfuerzo normal, en el cual en rigor corresponde considerar infinitos planos de carga.
                }
                self.agregar_ang(estado["plano_de_carga"])
            lista_estados.append(estado)
        if tipo == "3D":
            lista_estados = sorted(lista_estados, key=lambda x: x["plano_de_carga"])
        return lista_estados

    def cargar_propiedades_materiales(self):

        self.hormigon = Hormigon(tipo=self.ingreso_datos_sheet.get_value("C", "4"))
        self.tipo_estribo = self.ingreso_datos_sheet.get_value("C", "10")

        def_de_rotura_a_pasivo = self.obtener_def_de_rotura_a_pasivo()
        self.setear_propiedades_acero_pasivo(def_de_rotura_a_pasivo)

        def_de_pretensado_inicial = self.obtener_def_de_pretensado_inicial()
        self.def_de_pretensado_inicial = def_de_pretensado_inicial
        self.setear_propiedades_acero_activo(def_de_pretensado_inicial)

    def obtener_plano_deformación_inicial_pretensado(self):
        """Obtiene los parámetros del plano de deformación elástica inicial del
        hormigón, a partir de la acción del
        pretensado sobre dicha sección."""
        if not self.EAP:  # Caso de Hormigón Armado
            return 0, 0, 0
        resultado = fsolve(
            self.función_desplazamiento_a_converger,
            [-BarraAceroPretensado.deformacion_de_pretensado_inicial, 0, 0],
            maxfev=50,
            full_output=1)

        if not (resultado[2]):
            raise Exception("No se encontró deformación inicial que satisfaga las ecuaciones de equilibrio")
        ec, phix, phiy = resultado[0]
        return ec, phix, phiy

    def mostrar_informacion_pretensado(self):
        if not self.EAP:
            return ''
        return f"ec: {self.ec:.2e}<br>φx: {self.phix:.2e}<br>φy: {self.phiy:.2e}"

    def función_desplazamiento_a_converger(self, c):
        (ec, phix, phiy) = c
        return self.calcular_sumatoria_de_fuerzas_en_base_a_plano_baricentrico(ec, phix, phiy)

    def obtener_deformacion_maxima_de_acero(self):
        def_max_acero_pasivo = BarraAceroPasivo.eu
        def_max_acero_activo = BarraAceroPretensado.epu
        return min(def_max_acero_pasivo, def_max_acero_activo)

    def obtener_def_de_rotura_a_pasivo(self):
        tipo = self.ingreso_datos_sheet.get_value("C", "6")
        posibles_opciones = {"ADN 420": "B", "ADN 500": "C", "AL 220": "D", "Provisto por Usuario": "E"}
        value = self.armaduras_pasivas_sheet.get_value(posibles_opciones.get(tipo, "B"), 5)
        return value

    def obtener_def_de_pretensado_inicial(self):
        value = self.ingreso_datos_sheet.get_value("E", 8)
        return value / 1000

    def obtener_discretizacion(self):
        return {
            "ΔX": f"{round(self.seccion_H.dx, 2)} cm" if self.seccion_H.dx else None,
            "ΔY": f"{round(self.seccion_H.dy, 2)} cm" if self.seccion_H.dy else None,
            "Δr": f"{round(self.seccion_H.dr, 2)} cm" if self.seccion_H.dr else None,
            "Δθ": f"{round(self.seccion_H.d_ang, 2)}°" if self.seccion_H.d_ang else None}

    def plano_de_carga(self):
        xmin, xmax, ymin, ymax = self.min_x_seccion - self.XG, self.max_x_seccion - self.XG, self.min_y_seccion - self.YG, self.max_y_seccion - self.YG

        # Adjust limits to include a margin
        margin = 0.05  # 5% of each axis range
        xmin_margin = xmin - (xmax - xmin) * margin
        xmax_margin = xmax + (xmax - xmin) * margin
        ymin_margin = ymin - (ymax - ymin) * margin
        ymax_margin = ymax + (ymax - ymin) * margin

        angulo_rad = np.radians(self.angulo_plano_de_carga_esperado)
        x_intersect_min = xmin_margin
        x_intersect_max = xmax_margin
        if angulo_rad != 0:
            m = np.tan(np.pi / 2 - angulo_rad)  # Slope of the line
            y_intersec_xmin = m * (xmin_margin - (xmin + xmax) / 2) + (ymin + ymax) / 2
            y_intersec_xmax = m * (xmax_margin - (xmin + xmax) / 2) + (ymin + ymax) / 2

            if abs(y_intersec_xmin) > abs(ymin_margin):
                x_intersect_min = ymin_margin / m
                x_intersect_max = ymax_margin / m
                y_intersec_xmax = ymax_margin
                y_intersec_xmin = ymin_margin

            puntos = (x_intersect_min, y_intersec_xmin, x_intersect_max, y_intersec_xmax)
        else:
            puntos = (0, ymin_margin, 0, ymax_margin)
        return puntos

    def obtener_color_kwargs(self, plano_de_def, arcoiris=False, blanco_y_negro=False):
        lista_colores = ["k", "r", "b", "g", "c", "m", "y", "k"]
        if arcoiris:
            return {"color": self.numero_a_color_arcoiris(abs(plano_de_def[3]))}
        return {"c": lista_colores[abs(plano_de_def[2])] if blanco_y_negro is False else "k"}

    def obtener_planos_de_deformacion(self):
        """Obtiene una lista de los planos de deformación últimos a utilizarse para determinar los estados de resistencia
        últimos, cada elemento de esta lista representa, en principio, un punto sobre el diagrama de interacción.
        Este puede no ser el caso si hay puntos para los cuales no se encuentra una convergencia, en ese caso será
        descartado."""
        lista_de_planos = []
        try:
            for j in range(350):
                if j <= 25:
                    def_final = -0.5
                    def_superior = -3
                    def_inferior = -3 + (def_final + 3) * j / (25)  # Hasta -0.3
                    tipo = 1
                elif 25 < j <= 100:
                    def_inicial = -0.5
                    def_final = 0
                    def_superior = -3
                    def_inferior = def_inicial + (def_final - def_inicial) * (j - 25) / (100 - 25)  # Hasta 0
                    tipo = 2
                elif 100 < j <= 200:
                    def_superior = -3
                    def_inferior = 10 * (j - 100) / (200 - 100)
                    tipo = 3
                elif 200 < j <= 275:  # Hasta la deformación máxima del acero.
                    def_superior = -3
                    def_inferior = 10 + (j - 200) * (self.deformacion_maxima_de_acero * 1000 - 10) / (275 - 200)
                    tipo = 4
                elif j <= 325:
                    def_superior = -3 + (6 + 3) * (j - 275) / (325 - 275)
                    def_inferior = self.deformacion_maxima_de_acero * 1000
                    tipo = 5
                else:
                    def_superior = 6 + (self.deformacion_maxima_de_acero * 1000 - 6) * (j - 325) / (350 - 326)
                    def_inferior = self.deformacion_maxima_de_acero * 1000
                    tipo = 6
                lista_de_planos.append((def_superior / 1000, def_inferior / 1000, tipo, j))
        except AttributeError as e:
            pass
        lista_invertida = [(x[1], x[0], -x[2], -x[3]) for x in lista_de_planos]  # Misma lista, invertida de signo
        return lista_de_planos + lista_invertida

    def asignar_deformacion_hormigon_a_elementos_pretensados(self):
        ec_plano = self.ec_plano_deformacion_elastica_inicial
        for elemento_pretensado in self.EAP:
            elemento_pretensado.def_elastica_hormigon_perdidas = ec_plano(elemento_pretensado.xg,
                                                                          elemento_pretensado.yg)

    def obtener_matriz_acero_pasivo(self):
        lista_filas = self.ingreso_datos_sheet.get_rows_range_between_values(
            ("ARMADURAS PASIVAS (H°- Armado)", "ARMADURAS ACTIVAS (H°- Pretensado)"),
            columns_range=["A"])
        resultado = MatrizAceroPasivo()
        for fila in lista_filas[5:-1]:
            x, y, d, i = self.obtener_valores_acero_tabla(fila)
            if d == 0:
                continue
            xg = round(x - self.XG, 3)
            yg = round(y - self.YG, 3)
            resultado.append(BarraAceroPasivo(xg, yg, d, i))
        return resultado

    def verificar_tolerancia(self, valor):
        tolerancia = 0.00000000000004
        return 0 if abs(valor) <= tolerancia else valor

    def obtener_valores_acero_tabla(self, fila):
        return (self.ingreso_datos_sheet.get_value("C", fila),
                self.ingreso_datos_sheet.get_value("E", fila),
                self.ingreso_datos_sheet.get_value("G", fila),
                self.ingreso_datos_sheet.get_value("A", fila))

    def setear_propiedades_acero_pasivo(self, def_de_rotura_a_pasivo):
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
                values = BarraAceroPasivo.tipos_de_acero_y_valores.get(tipo)
                for k, v in values.items():
                    self.__setattr__(k, v)
                fy = BarraAceroPasivo.tipos_de_acero_y_valores.get(tipo.upper())["fy"]
                BarraAceroPasivo.E = 20000
                BarraAceroPasivo.tipo = tipo
                BarraAceroPasivo.fy = fy/10
                BarraAceroPasivo.eu = def_de_rotura_a_pasivo
        except Exception:
            raise Exception("No se pudieron setear las propiedades del acero pasivo, revise configuración")

    def obtener_matriz_acero_pretensado(self):
        lista_filas = self.ingreso_datos_sheet.get_rows_range_between_values(
            ("ARMADURAS ACTIVAS (H°- Pretensado)", "DISCRETIZACIÓN DE LA SECCIÓN"),
            columns_range=["A"])
        resultado = MatrizAceroActivo()
        for fila in lista_filas[5:-1]:
            x, y, area, i = self.obtener_valores_acero_tabla(fila)
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
                values = BarraAceroPretensado.tipos_de_acero_y_valores.get(tipo.upper())
                for k, v in values.items():
                    setattr(BarraAceroPretensado, k, v)
                BarraAceroPretensado.tipo = tipo
                BarraAceroPretensado.Eps = 20000  # kN/cm²
                BarraAceroPretensado.deformacion_de_pretensado_inicial = def_de_pretensado_inicial
            temp_bar = BarraAceroPretensado(0, 0, 0, 0)
            BarraAceroPretensado.fse = temp_bar.relacion_constitutiva(temp_bar.deformacion_de_pretensado_inicial)
        except Exception as e:
            raise Exception("No se pudieron establecer las propiedades del acero activo, revise configuración")

    def obtener_indice(self, contorno):
        value = self.ingreso_datos_sheet.get_value("A", contorno[0])
        return value.split()[-1]

    def obtener_signo(self, contorno):
        value = self.ingreso_datos_sheet.get_value("C", contorno[0])
        return +1 if "Pos" in value else -1

    def obtener_tipo(self, contorno):
        value = self.ingreso_datos_sheet.get_value("E", contorno[0])
        return value

    def get_cantidad_de_nodos(self, contorno):
        return self.ingreso_datos_sheet.get_value("G", contorno[0])

    def obtener_matriz_hormigon(self):
        filas_hormigon = self.ingreso_datos_sheet.get_rows_range_between_values(
            ("GEOMETRÍA DE LA SECCIÓN DE HORMIGÓN", "ARMADURAS PASIVAS (H°- Armado)"),
            columns_range=["A"])
        lista_filas_contornos = self.ingreso_datos_sheet.subdivide_range_in_contain_word("A", filas_hormigon, "Contorno")
        contornos = {}
        coordenadas_nodos = []
        max_x, min_x = [], []
        max_y, min_y = [], []
        delta_x = []
        delta_y = []
        for i, filas_contorno in enumerate(lista_filas_contornos):
            signo = self.obtener_signo(filas_contorno)
            tipo = self.obtener_tipo(filas_contorno)
            indice = self.obtener_indice(filas_contorno)
            if tipo == "Poligonal":
                cantidad_de_nodos = int(self.get_cantidad_de_nodos(filas_contorno))
                for fila_n in self.ingreso_datos_sheet.get_n_rows_after_value("Nodo Nº", cantidad_de_nodos + 1,
                                                                              rows_range=filas_contorno)[1:]:
                    x = self.ingreso_datos_sheet.get_value("C", fila_n)
                    y = self.ingreso_datos_sheet.get_value("E", fila_n)
                    coordenadas_nodos.append(Node(round(x, 3), round(y, 3)))  # Medidas en centímetros
                contorno = Contorno(coordenadas_nodos, signo, indice, ordenar=True)
                if signo > 0:  # Solo se utilizan los contornos positivos para definir la discretización
                    max_x.append(max(contorno.x))
                    min_x.append(min(contorno.x))
                    max_y.append(max(contorno.y))
                    min_y.append(min(contorno.y))
                    delta_x.append(abs(max(contorno.x) - min(contorno.x)))
                    delta_y.append(abs(max(contorno.y) - min(contorno.y)))
                contornos[str(i + 1)] = contorno
                coordenadas_nodos = []
            elif tipo == "Circular":
                x = self.ingreso_datos_sheet.get_value_on_the_right("Nodo Centro", filas_contorno, 2)
                y = self.ingreso_datos_sheet.get_value_on_the_right("Nodo Centro", filas_contorno, 4)
                r_int = self.ingreso_datos_sheet.get_value_on_the_right("Radio Interno [cm]", filas_contorno, 2)
                r_ext = self.ingreso_datos_sheet.get_value_on_the_right("Radio Externo [cm]", filas_contorno, 2)
                if signo > 0:
                    max_x.append(x + r_ext)
                    min_x.append(x - r_ext)
                    max_y.append(y + r_ext)
                    min_y.append(y - r_ext)
                    delta_x.append(r_ext - r_int)
                    delta_y.append(r_ext - r_int)
                contornos[str(i + 1)] = ContornoCircular(nodo_centro=Node(x, y), indice=indice, radios=(r_int, r_ext),
                                                         signo=signo)
            else:
                pass
        self.max_x_seccion = max(max_x)
        self.min_x_seccion = min(min_x)
        self.max_y_seccion = max(max_y)
        self.min_y_seccion = min(min_y)
        EEH = SeccionArbitraria(contornos, discretizacion=self.get_discretizacion(delta_x, delta_y, contornos))
        return EEH

    def get_discretizacion(self, delta_x, delta_y, contornos):
        hay_contorno_circular = any(isinstance(v, ContornoCircular) for k, v in contornos.items())
        hay_contorno_rectangular = any(not isinstance(x, ContornoCircular) for x in contornos)
        rows_range = self.ingreso_datos_sheet.get_n_rows_after_value("DISCRETIZACIÓN DE LA SECCIÓN",
                                                                     number_of_rows_after_value=20, columns_range="A")
        nivel_discretizacion = self.ingreso_datos_sheet.get_value_on_the_right("Nivel de Discretización", rows_range, 2)
        self.nivel_disc = nivel_discretizacion
        if nivel_discretizacion == "Avanzada (Ingreso Manual)":
            dx = self.ingreso_datos_sheet.get_value_on_the_right("ΔX [cm] =", rows_range, 2)
            dy = self.ingreso_datos_sheet.get_value_on_the_right("ΔY [cm] =", rows_range, 2)
            d_ang = self.ingreso_datos_sheet.get_value_on_the_right("Δθ [°] =", rows_range, 2)
            return (dx if hay_contorno_rectangular else None,
                    dy if hay_contorno_rectangular else None,
                    min(dx, dy) if hay_contorno_circular else None,
                    d_ang if hay_contorno_circular else None)
        factor_rectangular = 1 / self.niveles_mallado_rectangular.get(nivel_discretizacion)
        factor_circular = self.niveles_mallado_circular.get(nivel_discretizacion)

        return (factor_rectangular * max(delta_x) if hay_contorno_rectangular else None,
                factor_rectangular * max(delta_y) if hay_contorno_rectangular else None,
                factor_circular[0] if hay_contorno_circular else None,
                factor_circular[1] if hay_contorno_circular else None)

    def calcular_sumatoria_de_fuerzas_en_base_a_plano_baricentrico(self, ec, phix, phiy):
        ecuacion_plano_deformacion = lambda x, y: ec + math.tan(math.radians(phix)) * (y) + math.tan(
            math.radians(phiy)) * (x)
        sumFA = sumFP = sumFH = 0
        MxA = MxAP = MxH = 0
        MyA = MyAP = MyH = 0
        for barra in self.EA:
            def_elemento, area = ecuacion_plano_deformacion(barra.xg, barra.yg), barra.area
            FA = barra.relacion_constitutiva(def_elemento) * area
            sumFA = sumFA + FA
            MxA = FA * barra.yg + MxA
            MyA = -FA * barra.xg + MyA
        for barra_p in self.EAP:
            deformacion_elastica_hormingon, area = ecuacion_plano_deformacion(barra_p.xg, barra_p.yg), barra_p.area
            deformacion_pretensado_inicial = barra_p.deformacion_de_pretensado_inicial
            deformacion_total = deformacion_elastica_hormingon + deformacion_pretensado_inicial

            Fp = barra_p.relacion_constitutiva(deformacion_total) * area
            sumFP = sumFP + Fp
            MxAP = Fp * barra_p.yg + MxAP
            MyAP = -Fp * barra_p.xg + MyAP

        for elemento in self.EEH:
            def_elemento, area = ecuacion_plano_deformacion(elemento.xg, elemento.yg), elemento.area
            F_hor = self.hormigon.relacion_constitutiva_elastica(def_elemento) * area
            sumFH = sumFH + F_hor
            MxH = F_hor * elemento.yg + MxH
            MyH = -F_hor * elemento.xg + MyH

        sumF = sumFA + sumFP + sumFH
        Mx = round(MxA + MxAP + MxH, 8)
        My = round(MyA + MyAP + MyH, 8)

        return [sumF, Mx, My]

    def print_result_tridimensional(self, ec, phix, phiy):
        ec_plano = lambda x, y: ec + math.tan(math.radians(phix)) * y + math.tan(math.radians(phiy)) * x
        self.seccion_H.mostrar_contornos_3d(ecuacion_plano_a_desplazar=ec_plano)

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
        for k, v in data_subset.items():
            lista_x_total = [(1 if x > 0 else -1 if x!=0 else 1 if y>=0 else -1) * math.sqrt(x ** 2 + y ** 2) for x, y in
                             zip(v["x"], v["y"])].copy()
            list_values = np.array([v["z"], lista_x_total, v["phi"]])
            list_values = list_values.transpose().tolist()
            self.diagrama_interaccion_sheet.change_cell_value_by_range("G1", k)
            self.diagrama_interaccion_sheet.insert_values_vertically("I3", list_values, columns_to_clean=["I", "J", "K"], start_row=3)

            X = [x["M"] for x in lista_puntos_a_verificar]
            Y = [x["P"] for x in lista_puntos_a_verificar]

            puntos_a_verificar = np.array([Y, X]).transpose().tolist()
            self.diagrama_interaccion_sheet.insert_values_vertically("N3", puntos_a_verificar, columns_to_clean=["N", "O"], start_row=3)

    def insertar_valores_3D(self, data_subset):
        i = 0  # contador
        for k, v in data_subset.items():
            list_values = np.array([v["x"], v["y"], v["z"], v["phi"]])
            list_values = list_values.transpose().tolist()
            if i == 0:  # Poniendo el valor de lambda en la primera celda
                self.diagrama_interaccion_3D_sheet.change_cell_value_by_range("A1", f"λ= {k} °")
                self.diagrama_interaccion_3D_sheet.clear_contents_from_column(6)
                self.diagrama_interaccion_3D_sheet.insert_values_vertically("A4", list_values, start_row=4)
                i = i + 1
                continue
            new_range = self.diagrama_interaccion_3D_sheet.calculate_new_range_by_coll_offset("A1:D3", column_offset=5 * i)
            self.diagrama_interaccion_3D_sheet.copy_paste_range("A1:D3", new_range)
            top_bottom_cell = new_range.split(":")[0]
            self.diagrama_interaccion_3D_sheet.change_cell_value_by_range(top_bottom_cell, f"λ= {k} °")
            self.diagrama_interaccion_3D_sheet.insert_values_vertically(
                self.diagrama_interaccion_3D_sheet.shift_cell_by_offset(top_bottom_cell, col_offset=0, row_offset=3),
                list_values,
                start_row=4)
            i = i + 1
