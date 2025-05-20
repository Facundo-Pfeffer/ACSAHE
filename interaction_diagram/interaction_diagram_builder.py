import colorsys
import logging
import traceback
from tkinter import messagebox
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import math
import numpy as np
from scipy.optimize import fsolve
from functools import lru_cache
import copy

from geometry.section_analysis import ACSAHEGeometricSolution

diferencia_admisible = 0.5


def show_message(message, titulo="Mensaje"):
    messagebox.showinfo(titulo, message)


class UniaxialInteractionDiagram:

    def __init__(self, uniaxial_angle, geometric_solution: ACSAHEGeometricSolution):
        self.geometric_solution = geometric_solution
        self.concrete_element_array = self.get_concrete_element_array()
        self.rebar_array = self.get_rebar_array()
        self.prestressed_reinforcement_array = self.get_prestressed_reinforcement_array()
        self.uniaxial_angle = uniaxial_angle
        self.phi_strength_reduction_factor = geometric_solution.problema["phi_variable"]
        try:
            self.no_solution_points_list = []
            self.interaction_diagram_points_list = self.iterate_solution()
            self.review_capped_points()
        except Exception as e:
            traceback.print_exc()
            show_message(e)
            raise e
        finally:
            logging.log(1, "Se terminó la ejecución")

    def get_concrete_element_array(self):
        return np.array([
            (element.xg, element.yg, element.area, 0.0, 0.0) for element in self.geometric_solution.EEH],
            dtype=[('xg', float), ('yg', float), ('area', float), ("neutral_axis_distance", float), ('strain', float)])

    def get_rebar_array(self):
        return np.array([
            (rebar.xg, rebar.yg, rebar.area, 0.0, 0.0, rebar.ey) for rebar in self.geometric_solution.EA],
            dtype=[('xg', float), ('yg', float), ('area', float), ("neutral_axis_distance", float),
                   ('strain', float),
                   ('ey', float)  # ey is later used for computing the strength reduction factor Φ (Table 21.2.2)
                   ])

    def get_prestressed_reinforcement_array(self):
        return np.array([
            (rebar.xg, rebar.yg, rebar.area, 0.0,
             0.0, rebar.def_elastica_hormigon_perdidas, rebar.deformacion_de_pretensado_inicial, 0.0)
            for rebar in self.geometric_solution.EAP],
            dtype=[('xg', float), ('yg', float), ('area', float), ("neutral_axis_distance", float),
                   ('flexural_strain', float), ('concrete_shortening_strain', float), ('effective_strain', float), ('total_strain', float)])

    def iterate_solution(self):
        """Método principal para la obtención de los diagramas de interacción."""
        interaction_diagram_points = []
        try:
            with ThreadPoolExecutor(max_workers=int(os.cpu_count())) as executor:
                futures = [executor.submit(self.solve_limit_planes, plano) for plano in
                           self.geometric_solution.planos_de_deformacion]
                for future in as_completed(futures):
                    result = future.result()
                    if result is not None:
                        interaction_diagram_points.append(result)
        except Exception as e:
            traceback.print_exc()
            raise(e)
        return interaction_diagram_points

    def solve_limit_planes(self, plano_de_deformacion):
        try:
            sol = fsolve(
                self.evaluar_diferencia_para_inc_eje_neutro,
                x0=-self.uniaxial_angle,
                xtol=0.005,  # ~20 seconds.
                args=plano_de_deformacion,
                full_output=1,
                maxfev=50
            )
            theta, precision, is_success = sol[0][0], sol[1]['fvec'], sol[2] == 1
            theta = np.radians(theta[0] if isinstance(theta, np.ndarray) else theta)
            if is_success and abs(precision) < diferencia_admisible:
                sumF, Mx, My, phi = self.get_solution_for_theta_and_strain_plane(theta, *plano_de_deformacion)
                return {
                    "sumF": sumF,
                    "M": self.get_resulting_uniaxial_moment(Mx, My),
                    "plano_de_deformacion": plano_de_deformacion,
                    "color": self.transform_number_in_rainbow_color(abs(plano_de_deformacion[3])),
                    "phi": phi,
                    "Mx": Mx,
                    "My": My,
                    "is_capped": False  # Some compression points will later be capped according to 22.4.2.
                }
            else:  # Used only for debugging solution-less points
                pass
        except Exception as e:
            traceback.print_exc()
            raise(e)

    def evaluar_diferencia_para_inc_eje_neutro(self, theta, *plano_de_deformacion):
        theta = np.radians(theta[0] if isinstance(theta, np.ndarray) else theta)
        sumF, Mx, My, phi = self.get_solution_for_theta_and_strain_plane(theta, *plano_de_deformacion)
        ex = round(My / sumF, 5)
        ey = round(Mx / sumF, 5)
        if ex == 0 and ey == 0:  # Carga centrada, siempre "pertenece" al plano de carga.
            return 0
        angulo_momento_con_x = self.obtener_angulo_resultante_momento(Mx, My)
        angulo_momento_esperado_con_x = 180 - abs(self.uniaxial_angle)
        if angulo_momento_esperado_con_x >= 180:
            angulo_momento_esperado_con_x = angulo_momento_esperado_con_x - 180  # Para que se encuentre en rango [0, 180]
        diferencia = angulo_momento_con_x - angulo_momento_esperado_con_x  # Apuntamos a que esto sea 0
        diferencia = diferencia if abs(diferencia) > diferencia_admisible else 0
        diferencia = diferencia if abs(180-diferencia) > diferencia_admisible else 0  # Se observó que en algunos casos,
        # la función scipy.fsolve se traba cuando obtiene el mismo resultado sucesivas veces, por lo que toma válida
        return diferencia

    def calculo_distancia_eje_neutro_de_elements_list(self, theta_rad):
        sin_theta, cos_theta = self.sincos_cached(theta_rad)

        concrete_rotated = self.concrete_element_array.copy()
        rebar_rotated = self.rebar_array.copy()
        prestressed_rotated = self.prestressed_reinforcement_array.copy()

        concrete_rotated["neutral_axis_distance"] = -concrete_rotated['xg'] * sin_theta + concrete_rotated[
            'yg'] * cos_theta
        rebar_rotated["neutral_axis_distance"] = -rebar_rotated['xg'] * sin_theta + rebar_rotated['yg'] * cos_theta
        prestressed_rotated["neutral_axis_distance"] = -prestressed_rotated['xg'] * sin_theta + prestressed_rotated[
            'yg'] * cos_theta

        return concrete_rotated, rebar_rotated, prestressed_rotated

    @staticmethod
    @lru_cache(maxsize=512)
    def sincos_cached(theta_rad):
        return np.sin(theta_rad), np.cos(theta_rad)

    @lru_cache(maxsize=1024)
    def get_solution_for_theta_and_strain_plane(self, theta, *plano_de_deformacion):
        rot_concrete_array, rot_rebar_array, rot_prestressed_array = self.calculo_distancia_eje_neutro_de_elements_list(theta)
        rot_concrete_array.sort(order="neutral_axis_distance")
        rot_rebar_array.sort(order="neutral_axis_distance")
        rot_prestressed_array.sort(order="neutral_axis_distance")
        ecuacion_plano_deformacion = self._get_strain_plane_equation(
            rot_concrete_array, rot_rebar_array, rot_prestressed_array, plano_de_deformacion)
        sumF, Mx, My, phi = self.get_section_forces_for_rotated_neutral_axis(
            rot_concrete_array, rot_rebar_array, rot_prestressed_array, ecuacion_plano_deformacion)
        return sumF, Mx, My, phi

    @staticmethod
    def get_resulting_uniaxial_moment(Mx, My):
        return (1 if Mx >= 0 else -1) * math.sqrt(Mx ** 2 + My ** 2)

    @staticmethod
    def obtener_angulo_resultante_momento(Mx, My):
        angulo_x = math.degrees(math.atan2(My, Mx))
        if angulo_x == 180:
            return 0
        return angulo_x if angulo_x >= 0 else angulo_x + 180  # Para que se encuentre comprendido en el rango [0, 180]

    def _get_strain_plane_equation(self, rot_concrete_array, rot_rebar_array, rot_prestressed_array,
                                   plano_de_deformacion):
        extreme_strain_y_positive, exteme_strain_y_negative = plano_de_deformacion[0], plano_de_deformacion[1]
        y_extreme_positive = self._get_extreme_positive_y(
            extreme_strain_y_positive, rot_rebar_array, rot_prestressed_array, rot_concrete_array)
        y_extreme_negative = self.get_extreme_negative_y(
            exteme_strain_y_negative, rot_rebar_array, rot_prestressed_array, rot_concrete_array)

        if y_extreme_positive == y_extreme_negative and extreme_strain_y_positive == exteme_strain_y_negative:
            return lambda y: extreme_strain_y_positive

        slope = (extreme_strain_y_positive - exteme_strain_y_negative) / (y_extreme_positive - y_extreme_negative)
        y_intercept = exteme_strain_y_negative - slope * y_extreme_negative
        return lambda rotated_y: rotated_y * slope + y_intercept  # linear equation on rotated axis.

    def _get_extreme_positive_y(self, extreme_strain, rebar_array, prestressed_array, concrete_array):
        if extreme_strain <= 0 or extreme_strain < self.geometric_solution.deformacion_maxima_de_acero:
            return concrete_array["neutral_axis_distance"][-1]  # Most compressed concrete fiber

        neutral_axis_distances = np.concatenate([rebar_array["neutral_axis_distance"], prestressed_array["neutral_axis_distance"]])
        return np.max(neutral_axis_distances)  # Most distant (traction) steel fiber

    def get_extreme_negative_y(self, extreme_strain, rebar_array, prestressed_array, concrete_array):
        if extreme_strain <= 0 or extreme_strain < self.geometric_solution.deformacion_maxima_de_acero:
            return concrete_array["neutral_axis_distance"][0]  # Distance to compressed concrete fiber.

        neutral_axis_distances = np.concatenate([rebar_array["neutral_axis_distance"], prestressed_array["neutral_axis_distance"]])
        return np.min(neutral_axis_distances)  # Most distant (traction) steel fiber

    def get_section_forces_for_rotated_neutral_axis(
            self, rot_concrete_array, rot_rebar_array, rot_prestressed_array, strain_plane_eq):

        # -------------------- 1. Compute flexural strain fields --------------------
        rot_concrete_array['strain'] = strain_plane_eq(rot_concrete_array["neutral_axis_distance"])
        rot_rebar_array['strain'] = strain_plane_eq(rot_rebar_array["neutral_axis_distance"])
        rot_prestressed_array['flexural_strain'] = strain_plane_eq(
            rot_prestressed_array["neutral_axis_distance"])


        # -------------------- 2. Concrete --------------------
        max_compression_strain = min(rot_concrete_array['strain'][0], rot_concrete_array['strain'][-1])
        concrete_forces = np.array([
            self.geometric_solution.hormigon.simplified_stress_strain_eq(e, e_max_comp=max_compression_strain) * a
            for e, a in zip(rot_concrete_array['strain'], rot_concrete_array['area'])
        ])
        sumFH = np.sum(concrete_forces)
        MxH = np.sum(concrete_forces * rot_concrete_array['yg'])
        MyH = np.sum(-concrete_forces * rot_concrete_array['xg'])

        # -------------------- 3. Passive Rebar --------------------
        rebar_forces = np.array([
            self.geometric_solution.EA[0].stress_strain_eq(e) * a for e, a in zip(
                rot_rebar_array['strain'],
                rot_rebar_array['area']
            )
        ])
        sumFA = np.sum(rebar_forces)
        MxA = np.sum(rebar_forces * rot_rebar_array['yg'])
        MyA = np.sum(-rebar_forces * rot_rebar_array['xg'])

        # -------------------- 4. Prestressed Rebar --------------------
        # Shortening and prestress already defined — total strain
        rot_prestressed_array['total_strain'] = (
                rot_prestressed_array['flexural_strain'] +
                rot_prestressed_array['concrete_shortening_strain'] +
                rot_prestressed_array['effective_strain']
        )

        prestressed_forces = np.array([
            self.geometric_solution.EAP[0].stress_strain_eq(e) * a for e, a in zip(
                rot_prestressed_array['total_strain'],
                rot_prestressed_array['area']
            )
        ])
        sumFP = np.sum(prestressed_forces)
        MxAP = np.sum(prestressed_forces * rot_prestressed_array['yg'])
        MyAP = np.sum(-prestressed_forces * rot_prestressed_array['xg'])

        # -------------------- 5. Strength Reduction Factor --------------------

        phi = self.get_strength_reduction_factor(
            rot_rebar_array=rot_rebar_array,
            rot_prestressed_array=rot_prestressed_array,
            transverse_reinf_type=self.geometric_solution.tipo_estribo
        )

        # -------------------- 6. Totals --------------------
        sumF = phi * (sumFA + sumFP + sumFH)
        Mx = round(phi * (MxA + MxAP + MxH), 8)
        My = round(phi * (MyA + MyAP + MyH), 8)

        return sumF, Mx, My, phi

    def get_strength_reduction_factor(self, **kwargs):
        if isinstance(self.phi_strength_reduction_factor, float):
            return self.phi_strength_reduction_factor
        elif "CIRSOC 201-2005" in self.phi_strength_reduction_factor:
            return self.get_strength_reduction_factor_2005(**kwargs)
        elif "CIRSOC 201-2024" in self.phi_strength_reduction_factor:
            return self.get_strength_reduction_factor_2024(**kwargs)
        else:
            return 1.0

    def get_strength_reduction_factor_2005(self, rot_rebar_array, rot_prestressed_array, transverse_reinf_type):
        # Manual override
        if isinstance(self.phi_strength_reduction_factor, float):
            return self.phi_strength_reduction_factor

        phi_min = 0.65 if "ZUNCHOS" not in transverse_reinf_type.upper() else 0.70

        if len(rot_rebar_array) == 0 and len(rot_prestressed_array) == 0:
            return 0.55  # Plain concrete

        # Concatenate strains
        all_strains = np.concatenate([
            rot_rebar_array["strain"],
            rot_prestressed_array["flexural_strain"]
        ])
        max_strain = np.max(all_strains)

        # Interpolation logic
        if max_strain >= 0.005:
            return 0.9
        elif max_strain <= 0.002:
            return phi_min
        else:
            return (
                    phi_min * (0.005 - max_strain) / 0.003 +
                    0.9 * (max_strain - 0.002) / 0.003
            )

    def get_strength_reduction_factor_2024(self, rot_rebar_array, rot_prestressed_array, transverse_reinf_type):
        # Manual override
        if isinstance(self.phi_strength_reduction_factor, float):
            return self.phi_strength_reduction_factor

        phi_min = 0.65 if "ZUNCHOS" not in transverse_reinf_type.upper() else 0.75
        phi_max = 0.90

        if len(rot_rebar_array) == 0 and len(rot_prestressed_array) == 0:
            return 0.60  # Plain concrete

        # Get most distant bars for each type
        extreme_tension_rebar = np.sort(rot_rebar_array, order="strain")[-1] if len(rot_rebar_array) > 0 else None
        extreme_tension_prestressed_bar = np.sort(rot_prestressed_array, order="flexural_strain")[-1] if len(rot_prestressed_array) > 0 else None

        # Get most distant bars for each type
        if extreme_tension_rebar is not None and extreme_tension_prestressed_bar is not None:
            if extreme_tension_rebar["strain"] >= extreme_tension_prestressed_bar["flexural_strain"]:
                max_steel_strain = extreme_tension_rebar["strain"]
                ety = extreme_tension_rebar["ey"]
            else:
                max_steel_strain = extreme_tension_prestressed_bar["flexural_strain"]
                ety = 2/1000
        elif extreme_tension_prestressed_bar is None:
            max_steel_strain = extreme_tension_rebar["strain"]
            ety = extreme_tension_rebar["ey"]
        else:
            max_steel_strain = extreme_tension_prestressed_bar["flexural_strain"]
            ety = 2/1000

        # Interpolation logic
        if max_steel_strain >= ety + 0.003:
            return phi_max
        elif max_steel_strain <= ety:
            return phi_min
        else:
            return phi_min + (phi_max-phi_min)/(3/1000)*(max_steel_strain-ety)

    @staticmethod
    def transform_number_in_rainbow_color(numero):
        if numero < 0 or numero > 350:
            raise ValueError("El número debe estar entre 0 y 350")

        adjusted_input = (numero / 350.0)
        if adjusted_input < 0.5:  # Esto es aproximadamente la transición del rojo al verde
            # A la primera mitad del espectro, le aplicamos una función que crece más lentamente
            adjusted_input = pow(adjusted_input * 2, 1.5) / 2
        else:
            # Después le aplica esta progresión un poco más rápida
            adjusted_input = 0.5 + (pow((adjusted_input - 0.5) * 2, 0.85) / 2)

        non_linear_factor = math.sin(adjusted_input * math.pi / 2)

        # Mapeando al rango de la librería hue (que va de 0 a 360)
        hue = non_linear_factor * 330  # 330 controla que el color máximo sea púrpura (como un arcoíris)

        # Para que los colores sean pseudo neón
        saturation = 1.0  # 100%
        lightness = 0.5  # 50%

        rojo, verde, azul = colorsys.hls_to_rgb(hue / 360.0, lightness, saturation)

        rojo = int(rojo * 255)
        verde = int(verde * 255)
        azul = int(azul * 255)

        return [rojo, verde, azul]

    def _get_maximum_compression_value(self):
        """"Getting maximum nominal value for Pn according to 22.4.2.1"""
        transverse_reinf_factor = 0.80 if self.geometric_solution.tipo_estribo == "Estribos" else 0.85
        gross_area = self.geometric_solution.seccion_H.area
        fc = self.geometric_solution.hormigon.fc / 10
        if len(self.geometric_solution.EA) == 0 and len(self.geometric_solution.EAP) == 0:
            return transverse_reinf_factor * 0.85 * fc * gross_area
        elif len(self.geometric_solution.EAP) == 0:
            fy = self.geometric_solution.EA[0].fy
            Ast = self.geometric_solution.seccion_H.Ast
            po = 0.85*fc*(gross_area-Ast) + fy * Ast  # 22.4.2.2
            return transverse_reinf_factor * po
        else:
            fy = self.geometric_solution.EA[0].fy
            Ast = self.geometric_solution.seccion_H.Ast
            fse = self.geometric_solution.EAP[0].fse
            Ep = self.geometric_solution.EAP[0].Eps
            Apt = self.geometric_solution.seccion_H.Apt
            Apd = Apt  # Revisar
            po = 0.85*fc*(gross_area-Ast-Apd)+fy*Ast-(fse-0.003*Ep)*Apt  # 22.4.2.3
            return transverse_reinf_factor * po

    def review_capped_points(self):
        compression_force_limit = self._get_maximum_compression_value()
        solution_copy = self.interaction_diagram_points_list.copy()
        for index, interaction_diagram_point in enumerate(solution_copy):
            if -interaction_diagram_point["sumF"]/interaction_diagram_point["phi"] > compression_force_limit:
                copy_point = copy.deepcopy(self.interaction_diagram_points_list[index])
                copy_point["sumF"] = -compression_force_limit*copy_point["phi"]
                self.interaction_diagram_points_list.append(copy_point)
                self.interaction_diagram_points_list[index]["is_capped"] = True  # Overwriting original point.
