import colorsys
import logging
import traceback
from tkinter import messagebox


import matplotlib.pyplot as plt
import math
import numpy as np
from scipy.optimize import fsolve


from geometria.resolvedor_geometria import ResolucionGeometrica


diferencia_admisible = 0.5


def show_message(message, titulo="Mensaje"):
    messagebox.showinfo(titulo, message)


class DiagramaInteraccion2D:
    def __init__(self, angulo_plano_de_carga, solucion_geometrica: ResolucionGeometrica):
        self.geometria = solucion_geometrica
        self.medir_diferencias = []
        self.angulo_plano_de_carga_esperado = angulo_plano_de_carga
        self.phi_variable = solucion_geometrica.problema["phi_variable"]
        try:
            self.lista_planos_sin_solucion = []
            self.lista_resultados = self.iterar()
        except Exception as e:
            traceback.print_exc()
            show_message(e)
            raise e
        finally:
            logging.log(1, "Se terminó la ejecución")

    def iterar(self):
        """Método principal para la obtención de los diagramas de interacción.
        Se itera en la inclinación del eje neutro para cada plano de deformación límite planteado.
        Pudiendo obtenerse (o no) 1 punto en el diagrama de interacción por cada plano límite."""
        lista_de_puntos = []
        try:
            for plano_de_deformacion in self.geometria.planos_de_deformacion:
                sol = fsolve(self.evaluar_diferencia_para_inc_eje_neutro,
                             x0=-self.angulo_plano_de_carga_esperado,  # Estimación inicial como si fuese flexión recta
                             xtol=0.005,
                             args=plano_de_deformacion,
                             full_output=1,
                             maxfev=50)  # Max fev = número de iteraciones máximo
                theta, diferencia_plano_de_carga, sol_encontrada = sol[0][0], sol[1]['fvec'], sol[2] == 1
                # test = self.evaluar_diferencia_para_inc_eje_neutro(theta, *plano_de_deformacion)
                self.medir_diferencias.append((diferencia_plano_de_carga, plano_de_deformacion))
                if sol_encontrada is True and abs(diferencia_plano_de_carga) < diferencia_admisible:
                    sumF, Mx, My, phi = self.obtener_resultante_para_theta_y_def(theta, *plano_de_deformacion)
                    lista_de_puntos.append(
                        {"sumF": sumF,
                         "M": self.obtener_momento_resultante(Mx, My),
                         "plano_de_deformacion": plano_de_deformacion,
                         "color": self.numero_a_color_arcoiris(abs(plano_de_deformacion[3])),
                         "phi": phi,
                         "Mx": Mx,
                         "My": My
                         })

                else:  # Punto Descartado, no se encontró solución.
                    self.lista_planos_sin_solucion.append((plano_de_deformacion, sol))
        except Exception as e:
            traceback.print_exc()
            print(e)

        return lista_de_puntos

    def obtener_resultante_para_theta_y_def(self, theta, *plano_de_deformacion):
        EEH_girado, EA_girado, EAP_girado = self.calculo_distancia_eje_neutro_de_elementos(theta)
        EEH_girado.sort(key=lambda elemento_h: elemento_h.y_girado)
        EA_girado.sort(key=lambda elemento_a: elemento_a.y_girado)
        EAP_girado.sort(key=lambda elemento_ap: elemento_ap.y_girado)
        ecuacion_plano_deformacion = self.obtener_ecuacion_plano_deformacion(EEH_girado, EA_girado, EAP_girado,
                                                                             plano_de_deformacion)
        sumF, Mx, My, phi = self.calcular_sumatoria_de_fuerzas_en_base_a_eje_neutro_girado(EEH_girado, EA_girado,
                                                                                           EAP_girado,
                                                                                           ecuacion_plano_deformacion)
        return sumF, Mx, My, phi

    def evaluar_diferencia_para_inc_eje_neutro(self, theta, *plano_de_deformacion):
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

    @staticmethod
    def obtener_momento_resultante(Mx, My):
        return (1 if Mx >= 0 else -1) * math.sqrt(Mx ** 2 + My ** 2)

    @staticmethod
    def obtener_angulo_resultante_momento(Mx, My):
        angulo_x = math.degrees(math.atan2(My, Mx))
        if angulo_x == 180:
            return 0
        return angulo_x if angulo_x >= 0 else angulo_x + 180  # Para que se encuentre comprendido en el rango [0, 180]

    def obtener_ecuacion_plano_deformacion(self, EEH_girado, EA_girado, EAP_girado, plano_de_deformacion):
        """Construye la ecuación de una recta que pasa por los puntos (y_positivo,def_1) (y_negativo,def_2).
        Y_positivo e y_negativo serán la distancia al eje neutro del elemento de hormigón más comprimido, o
        de la barra de acero (pasivo o activo) más traicionada. Lo positivo o negativo depende de qué lado del
        eje neutro se encuentra el análisis."""
        def_1, def_2 = plano_de_deformacion[0], plano_de_deformacion[1]
        y_positivo = self.obtener_y_determinante_positivo(def_1, EA_girado, EAP_girado, EEH_girado)
        y_negativo = self.obtener_y_determinante_negativo(def_2, EA_girado, EAP_girado, EEH_girado)
        if y_positivo == y_negativo and def_1 == def_2:
            return lambda y_girado: def_1
        A = (def_1 - def_2) / (y_positivo - y_negativo)
        B = def_2 - A * y_negativo
        return lambda y_girado: y_girado * A + B

    def obtener_y_determinante_positivo(self, def_extrema, EA_girado, EAP_girado, EEH_girado):
        """Lo positivo indíca que se encuentra con coordendas y_girado positívas (de un lado del eje neutro)"""
        if def_extrema <= 0 or def_extrema < self.geometria.deformacion_maxima_de_acero:  # Compresión
            return EEH_girado[-1].y_girado  # Fibra de Hormigón más alejada
        lista_de_armaduras = []
        lista_de_armaduras.extend(EA_girado)
        lista_de_armaduras.extend(EAP_girado)
        return max(x.y_girado for x in lista_de_armaduras)  # Armadura más traccionada (más alejada del EN)

    def obtener_y_determinante_negativo(self, def_extrema, EA_girado, EAP_girado, EEH_girado):
        """Lo negativo indíca que se encuentra con coordenadas y_girado negatívas (de un lado del eje neutro)"""
        if def_extrema <= 0 or def_extrema < self.geometria.deformacion_maxima_de_acero:
            return EEH_girado[0].y_girado  # Maxima fibra comprimida hormigón

        lista_de_armaduras = []
        lista_de_armaduras.extend(EA_girado)
        lista_de_armaduras.extend(EAP_girado)
        return min(x.y_girado for x in lista_de_armaduras)  # Armadura más traccionada (más alejada del EN)

    def calculo_distancia_eje_neutro_de_elementos(self, theta):
        EEH_girado, EA_girado, EAP_girado = self.geometria.EEH.copy(), self.geometria.EA.copy(), self.geometria.EAP.copy()
        for elemento_hormigon in EEH_girado:
            elemento_hormigon.y_girado = self.distancia_eje_rotado(elemento_hormigon, angulo=theta)
        for elemento_acero in EA_girado:
            elemento_acero.y_girado = self.distancia_eje_rotado(elemento_acero, angulo=theta)
        for elemento_acero_p in EAP_girado:
            elemento_acero_p.y_girado = self.distancia_eje_rotado(elemento_acero_p, angulo=theta)
        return EEH_girado, EA_girado, EAP_girado

    def distancia_eje_rotado(self, elemento, angulo):
        angulo_rad = math.radians(angulo[0] if type(
            angulo) == np.ndarray else angulo)  # Transformación interna, por las librerías utilizadas.
        value = -elemento.xg * math.sin(angulo_rad) + elemento.yg * math.cos(angulo_rad)
        return value

    def calcular_sumatoria_de_fuerzas_en_base_a_eje_neutro_girado(self, EEH_girado, EA_girado, EAP_girado,
                                                                  ecuacion_plano_deformacion):

        y_max, y_min = EEH_girado[-1].y_girado, EEH_girado[0].y_girado
        sumFA = sumFP = sumFH = 0
        MxA = MxAP = MxH = 0
        MyA = MyAP = MyH = 0
        e1, e2 = ecuacion_plano_deformacion(y_max), ecuacion_plano_deformacion(y_min)

        def_max_comp = min(e1, e2)

        for barra in EA_girado:
            dist_eje_neutro, def_elemento, area = barra.y_girado, ecuacion_plano_deformacion(barra.y_girado), barra.area
            FA = barra.relacion_constitutiva(def_elemento) * area
            sumFA = sumFA + FA
            MxA = FA * barra.yg + MxA
            MyA = -FA * barra.xg + MyA

        for barra_p in EAP_girado:
            dist_eje_neutro, deformacion_neta, area = barra_p.y_girado, ecuacion_plano_deformacion(
                barra_p.y_girado), barra_p.area
            deformacion_hormigon = barra_p.def_elastica_hormigon_perdidas
            deformacion_pretensado_inicial = barra_p.deformacion_de_pretensado_inicial
            deformacion_total = deformacion_neta + deformacion_hormigon + deformacion_pretensado_inicial

            Fp = barra_p.relacion_constitutiva(deformacion_total) * area
            sumFP = sumFP + Fp
            MxAP = Fp * barra_p.yg + MxAP
            MyAP = -Fp * barra_p.xg + MyAP

        for elemento in EEH_girado:
            def_elemento, area = ecuacion_plano_deformacion(elemento.y_girado), elemento.area
            F_hor = self.geometria.hormigon.relacion_constitutiva_simplificada(
                def_elemento, e_max_comp=def_max_comp) * area
            sumFH = sumFH + F_hor
            MxH = F_hor * elemento.yg + MxH
            MyH = -F_hor * elemento.xg + MyH

        factor_minoracion_de_resistencia = self.obtener_factor_minoracion_de_resistencia(
            EA_girado, EAP_girado, ecuacion_plano_deformacion, self.geometria.tipo_estribo)

        sumF = sumFA + sumFP + sumFH
        Mx = round(MxA + MxAP + MxH, 8)
        My = round(MyA + MyAP + MyH, 8)

        sumF = factor_minoracion_de_resistencia * sumF
        Mx = factor_minoracion_de_resistencia * Mx
        My = factor_minoracion_de_resistencia * My
        return sumF, Mx, My, factor_minoracion_de_resistencia

    def obtener_factor_minoracion_de_resistencia(self, EA_girado, EAP_girado, ecuacion_plano_de_def, tipo_estribo):
        if isinstance(self.phi_variable, float):
            phi_constante = self.phi_variable
            return phi_constante
        phi_min = 0.65 if tipo_estribo != "Zunchos en espiral" else 0.7
        if len(EA_girado) == 0 and len(EAP_girado) == 0:  # Hormigón Simple
            return 0.55
        lista_def_girado = [ecuacion_plano_de_def(barra.y_girado) for barra in EA_girado + EAP_girado]
        y_girado_max = max(lista_def_girado)
        if y_girado_max >= 5 / 1000:
            return 0.9
        elif y_girado_max < 2 / 1000:
            return phi_min
        else:
            return phi_min * (0.005 - y_girado_max) / 0.003 + 0.9 * (
                    y_girado_max - 0.002) / 0.003  # Interpolación lineal

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
