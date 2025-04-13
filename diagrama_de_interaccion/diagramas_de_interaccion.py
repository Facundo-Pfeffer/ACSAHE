import colorsys
import logging
import traceback
from tkinter import messagebox
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

import matplotlib.pyplot as plt
import math
import numpy as np
from scipy.optimize import fsolve


from functools import lru_cache
from geometry.section_analysis import ResolucionGeometrica


diferencia_admisible = 0.5


def show_message(message, titulo="Mensaje"):
    messagebox.showinfo(titulo, message)


class DiagramaInteraccion2D:

    def __init__(self, angulo_plano_de_carga, solucion_geometrica: ResolucionGeometrica):
        self.geometria = solucion_geometrica
        self.concrete_element_array = self.get_concrete_element_array()
        self.rebar_array = self.get_rebar_array()
        self.prestressed_reinforcement_array = self.get_prestressed_reinforcement_array()
        self.angulo_plano_de_carga_esperado = angulo_plano_de_carga
        self.phi_minoriacion_resistencia = solucion_geometrica.problema["phi_variable"]
        try:
            self.lista_planos_sin_solucion = []
            self.lista_resultados = self.iterar()
        except Exception as e:
            traceback.print_exc()
            show_message(e)
            raise e
        finally:
            logging.log(1, "Se terminó la ejecución")

    def get_concrete_element_array(self):
        return np.array([
            (element.xg, element.yg, element.area, 0.0, 0.0) for element in self.geometria.EEH],
            dtype=[('xg', float), ('yg', float), ('area', float), ("neutral_axis_distance", float), ('strain', float)])

    def get_rebar_array(self):
        return np.array([
            (rebar.xg, rebar.yg, rebar.area, 0.0, 0.0, rebar.relacion_constitutiva) for rebar in self.geometria.EA],
            dtype=[('xg', float), ('yg', float), ('area', float), ("neutral_axis_distance", float),
                   ('strain', float), ('relacion_constitutiva', object)])

    def get_prestressed_reinforcement_array(self):
        return np.array([
            (rebar.xg, rebar.yg, rebar.area, 0.0,
             0.0, rebar.def_elastica_hormigon_perdidas, rebar.deformacion_de_pretensado_inicial, 0.0,
             rebar.relacion_constitutiva) for rebar in self.geometria.EAP],
            dtype=[('xg', float), ('yg', float), ('area', float), ("neutral_axis_distance", float),
                   ('flexural_strain', float), ('concrete_shortening_strain', float), ('effective_strain', float), ('total_strain', float),
                   ('relacion_constitutiva', object)
                   ])

    def iterar(self):
        """Método principal para la obtención de los diagramas de interacción."""
        lista_de_puntos = []
        try:
            with ThreadPoolExecutor(max_workers=int(os.cpu_count())) as executor:
                futures = [executor.submit(self.resolver_plano, plano) for plano in
                           self.geometria.planos_de_deformacion]
                for future in as_completed(futures):
                    resultado = future.result()
                    if resultado is not None:
                        lista_de_puntos.append(resultado)
        except Exception as e:
            traceback.print_exc()
            print(e)
        return lista_de_puntos

    def resolver_plano(self, plano_de_deformacion):
        try:
            sol = fsolve(
                self.evaluar_diferencia_para_inc_eje_neutro,
                x0=-self.angulo_plano_de_carga_esperado,
                xtol=0.005,  # ~20 seconds.
                args=plano_de_deformacion,
                full_output=1,
                maxfev=50
            )
            theta, diferencia, success = sol[0][0], sol[1]['fvec'], sol[2] == 1
            theta = np.radians(theta[0] if isinstance(theta, np.ndarray) else theta)
            if success and abs(diferencia) < diferencia_admisible:
                sumF, Mx, My, phi = self.obtener_resultante_para_theta_y_def(theta, *plano_de_deformacion)
                return {
                    "sumF": sumF,
                    "M": self.obtener_momento_resultante(Mx, My),
                    "plano_de_deformacion": plano_de_deformacion,
                    "color": self.numero_a_color_arcoiris(abs(plano_de_deformacion[3])),
                    "phi": phi,
                    "Mx": Mx,
                    "My": My
                }
            else:  # Used only for debugging solution-less points
                pass
        except Exception as e:
            traceback.print_exc()
            print(e)

    def evaluar_diferencia_para_inc_eje_neutro(self, theta, *plano_de_deformacion):
        theta = np.radians(theta[0] if isinstance(theta, np.ndarray) else theta)
        sumF, Mx, My, phi = self.obtener_resultante_para_theta_y_def(theta, *plano_de_deformacion)
        ex = round(My / sumF, 5)
        ey = round(Mx / sumF, 5)
        if ex == 0 and ey == 0:  # Carga centrada, siempre "pertenece" al plano de carga.
            return 0
        angulo_momento_con_x = self.obtener_angulo_resultante_momento(Mx, My)
        angulo_momento_esperado_con_x = 180 - abs(self.angulo_plano_de_carga_esperado)
        if angulo_momento_esperado_con_x >= 180:
            angulo_momento_esperado_con_x = angulo_momento_esperado_con_x - 180  # Para que se encuentre en rango [0, 180]
        diferencia = angulo_momento_con_x - angulo_momento_esperado_con_x  # Apuntamos a que esto sea 0
        diferencia = diferencia if abs(diferencia) > diferencia_admisible else 0
        diferencia = diferencia if abs(180-diferencia) > diferencia_admisible else 0  # Se observó que en algunos casos,
        # la función scipy.fsolve se traba cuando obtiene el mismo resultado sucesivas veces, por lo que toma válida
        return diferencia

    def calculo_distancia_eje_neutro_de_elementos(self, theta_rad):
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
    def obtener_resultante_para_theta_y_def(self, theta, *plano_de_deformacion):
        rot_concrete_array, rot_rebar_array, rot_prestressed_array = self.calculo_distancia_eje_neutro_de_elementos(theta)
        rot_concrete_array.sort(order="neutral_axis_distance")
        rot_rebar_array.sort(order="neutral_axis_distance")
        rot_prestressed_array.sort(order="neutral_axis_distance")
        ecuacion_plano_deformacion = self.obtener_ecuacion_plano_deformacion(
            rot_concrete_array, rot_rebar_array, rot_prestressed_array, plano_de_deformacion)
        sumF, Mx, My, phi = self.calcular_sumatoria_de_fuerzas_en_base_a_eje_neutro_girado(
            rot_concrete_array, rot_rebar_array, rot_prestressed_array, ecuacion_plano_deformacion)
        return sumF, Mx, My, phi

    @staticmethod
    def obtener_momento_resultante(Mx, My):
        return (1 if Mx >= 0 else -1) * math.sqrt(Mx ** 2 + My ** 2)

    @staticmethod
    def obtener_angulo_resultante_momento(Mx, My):
        angulo_x = math.degrees(math.atan2(My, Mx))
        if angulo_x == 180:
            return 0
        return angulo_x if angulo_x >= 0 else angulo_x + 180  # Para que se encuentre comprendido en el rango [0, 180]

    def obtener_ecuacion_plano_deformacion(self, rot_concrete_array, rot_rebar_array, rot_prestressed_array,
                                           plano_de_deformacion):
        def_1, def_2 = plano_de_deformacion[0], plano_de_deformacion[1]
        y_positivo = self.obtener_y_determinante_positivo(def_1, rot_rebar_array, rot_prestressed_array,
                                                          rot_concrete_array)
        y_negativo = self.obtener_y_determinante_negativo(def_2, rot_rebar_array, rot_prestressed_array,
                                                          rot_concrete_array)

        if y_positivo == y_negativo and def_1 == def_2:
            return lambda y: def_1

        A = (def_1 - def_2) / (y_positivo - y_negativo)
        B = def_2 - A * y_negativo
        return lambda rotated_y: rotated_y * A + B

    def obtener_y_determinante_positivo(self, def_extrema, rebar_array, prestressed_array, concrete_array):
        if def_extrema <= 0 or def_extrema < self.geometria.deformacion_maxima_de_acero:
            return concrete_array["neutral_axis_distance"][-1]  # Most compressed concrete fiber

        neutral_axis_distances = np.concatenate([rebar_array["neutral_axis_distance"], prestressed_array["neutral_axis_distance"]])
        return np.max(neutral_axis_distances)  # Most distant (traction) steel fiber

    def obtener_y_determinante_negativo(self, def_extrema, rebar_array, prestressed_array, concrete_array):
        if def_extrema <= 0 or def_extrema < self.geometria.deformacion_maxima_de_acero:
            return concrete_array["neutral_axis_distance"][0]  # Distance to compressed concrete fiber.

        neutral_axis_distances = np.concatenate([rebar_array["neutral_axis_distance"], prestressed_array["neutral_axis_distance"]])
        return np.min(neutral_axis_distances)  # Most distant (traction) steel fiber

    def calcular_sumatoria_de_fuerzas_en_base_a_eje_neutro_girado(
            self, rot_concrete_array, rot_rebar_array, rot_prestressed_array, ecuacion_plano_deformacion):

        # -------------------- 1. Compute flexural strain fields --------------------
        rot_concrete_array['strain'] = ecuacion_plano_deformacion(rot_concrete_array["neutral_axis_distance"])
        rot_rebar_array['strain'] = ecuacion_plano_deformacion(rot_rebar_array["neutral_axis_distance"])
        rot_prestressed_array['flexural_strain'] = ecuacion_plano_deformacion(
            rot_prestressed_array["neutral_axis_distance"])


        # -------------------- 2. Concrete --------------------
        def_max_comp = min(rot_concrete_array['strain'][0], rot_concrete_array['strain'][-1])
        fuerzas_concreto = np.array([
            self.geometria.hormigon.relacion_constitutiva_simplificada(e, e_max_comp=def_max_comp) * a
            for e, a in zip(rot_concrete_array['strain'], rot_concrete_array['area'])
        ])
        sumFH = np.sum(fuerzas_concreto)
        MxH = np.sum(fuerzas_concreto * rot_concrete_array['yg'])
        MyH = np.sum(-fuerzas_concreto * rot_concrete_array['xg'])

        # -------------------- 3. Passive Rebar --------------------
        fuerzas_rebar = np.array([
            rel(e) * a for rel, e, a in zip(
                rot_rebar_array['relacion_constitutiva'],
                rot_rebar_array['strain'],
                rot_rebar_array['area']
            )
        ])
        sumFA = np.sum(fuerzas_rebar)
        MxA = np.sum(fuerzas_rebar * rot_rebar_array['yg'])
        MyA = np.sum(-fuerzas_rebar * rot_rebar_array['xg'])

        # -------------------- 4. Prestressed Rebar --------------------
        # Shortening and prestress already defined — total strain
        rot_prestressed_array['total_strain'] = (
                rot_prestressed_array['flexural_strain'] +
                rot_prestressed_array['concrete_shortening_strain'] +
                rot_prestressed_array['effective_strain']
        )

        fuerzas_prestressed = np.array([
            rel(e) * a for rel, e, a in zip(
                rot_prestressed_array['relacion_constitutiva'],
                rot_prestressed_array['total_strain'],
                rot_prestressed_array['area']
            )
        ])
        sumFP = np.sum(fuerzas_prestressed)
        MxAP = np.sum(fuerzas_prestressed * rot_prestressed_array['yg'])
        MyAP = np.sum(-fuerzas_prestressed * rot_prestressed_array['xg'])

        # -------------------- 5. Strength Reduction Factor --------------------
        phi = self.obtener_factor_minoracion_de_resistencia(
            rot_rebar_array, rot_prestressed_array, ecuacion_plano_deformacion, self.geometria.tipo_estribo
        )

        # -------------------- 6. Totals --------------------
        sumF = phi * (sumFA + sumFP + sumFH)
        Mx = round(phi * (MxA + MxAP + MxH), 8)
        My = round(phi * (MyA + MyAP + MyH), 8)

        return sumF, Mx, My, phi

    def obtener_factor_minoracion_de_resistencia(self, rot_rebar_array, rot_prestressed_array, ecuacion_plano_de_def,
                                                 tipo_estribo):
        # Manual override
        if isinstance(self.phi_minoriacion_resistencia, float):
            return self.phi_minoriacion_resistencia

        phi_min = 0.65 if tipo_estribo != "Zunchos en espiral" else 0.7

        if len(rot_rebar_array) == 0 and len(rot_prestressed_array) == 0:
            return 0.55  # Hormigón simple

        # Concatenate distances from both arrays
        all_neutral_axis_distances = np.concatenate([
            rot_rebar_array["neutral_axis_distance"],
            rot_prestressed_array["neutral_axis_distance"]
        ])

        # Compute strains from deformation plane
        all_strains = ecuacion_plano_de_def(all_neutral_axis_distances)
        max_strain = np.max(all_strains)

        # Interpolation logic
        if max_strain >= 0.005:
            return 0.9
        elif max_strain < 0.002:
            return phi_min
        else:
            return (
                    phi_min * (0.005 - max_strain) / 0.003 +
                    0.9 * (max_strain - 0.002) / 0.003
            )

    @staticmethod
    def numero_a_color_arcoiris(numero):
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

    def construir_grafica_resultado(self, arcoiris=True, blanco_y_negro=False):
        plt.rcParams["font.family"] = "Times New Roman"
        X = []
        Y = []
        fig = plt.figure()
        ax = fig.add_subplot(1, 1, 1)
        plt.title(f"DIAGRAMA DE INTERACCIÓN\nPara ángulo de plano de carga λ={self.angulo_plano_de_carga_esperado}°",
                  fontsize=12, fontweight='bold')
        plt.xticks(ha='right', fontsize=10)
        ax.tick_params(axis='both', which='major', labelsize=10)
        ax.set_xlabel("M[kNm]", loc="right", fontsize=10, fontweight='bold')
        ax.set_ylabel("N[kN]", loc="top", rotation=0, rotation_mode="anchor", fontsize=10,
                      fontweight='bold')
        self.preparar_eje_pyplot(ax)

        for resultado in self.lista_resultados:
            sumF = resultado["sumF"]
            M = resultado["M"]
            plano_def = resultado["plano_deformacion"]

            x = M / 100  # Pasaje de kNcm a kNm
            y = -sumF  # Negativo para que la compresión quede en cuadrante I y II del diagrama.
            X.append(x)
            Y.append(y)
            color_kwargs = self.geometria.obtener_color_kwargs(plano_def,
                                                               arcoiris=arcoiris,
                                                               blanco_y_negro=blanco_y_negro)
            plt.scatter(x, y,
                        marker=".",
                        s=100,
                        **color_kwargs)
        return fig

    def mostrar_resultado(self, blanco_y_negro=False):
        fig = self.construir_grafica_resultado(arcoiris=True, blanco_y_negro=blanco_y_negro)
        self.geometria.diagrama_interaccion_wb.add_plot(fig, name="di", location="L30")
        plt.show()

    @staticmethod
    def preparar_eje_pyplot(ax):
        # Mueve al centro del diagrama al eje X e Y (por defecto, se sitúan en el extremo inferior izquierdo).
        ax.yaxis.tick_right()

        ax.spines['left'].set_position('zero')
        ax.spines['bottom'].set_position('zero')

        # Elimina los viejos ejes
        ax.spines['right'].set_color('none')
        ax.spines['top'].set_color('none')

        # 'Tics' (marcas en el eje) en los ejes.
        ax.xaxis.set_ticks_position('bottom')
        ax.yaxis.set_ticks_position('left')

        # Grilla de referencia
        ax.grid(which='major', color='#DDDDDD', linewidth=0.8)
        ax.grid(which='minor', color='#EEEEEE', linestyle=':', linewidth=0.6)
        ax.minorticks_on()

        # Desplazamos los valores de y a la izquierda
        return ax
