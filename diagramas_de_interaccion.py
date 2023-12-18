from scipy.optimize import fsolve
import logging
import math
import matplotlib.pyplot as plt
import numpy as np
import traceback
import os
import warnings
from plotly.subplots import make_subplots
from excel_manager import ExcelManager
from acero_pretensado import BarraAceroPretensado
from acero_pasivo import BarraAceroPasivo
from hormigon import Hormigon
from geometria import Nodo, Contorno, SeccionArbitraria, Segmento, ContornoCircular
from matrices import MatrizAceroPasivo, MatrizAceroActivo
import plotly.graph_objects as go

from plotly_util import PlotlyUtil

diferencia_admisible = 5


class ObtenerDiagramaDeInteraccion2D:
    niveles_mallado_rectangular = {"Muy Gruesa": 6, "Gruesa": 12, "Media": 24, "Fina": 50, "Muy Fina": 100}
    niveles_mallado_circular = {"Muy Gruesa": (3, 45), "Gruesa": (6, 30), "Media": (12, 10),
                                "Fina": (25, 5), "Muy Fina": (50, 2)}
    def __init__(self, file_path, angulo_de_plano_de_carga, mostrar_seccion=True, mostrar_resultado=True, **kwargs):
        self.file_name = file_path
        self.ingreso_datos_wb = ExcelManager(file_path, "Ingreso de Datos")
        try:
            self.angulo_plano_de_carga_esperado = angulo_de_plano_de_carga
            self.armaduras_pasivas_wb = ExcelManager(file_path, "Armaduras Pasivas")
            self.resultados_wb = ExcelManager(file_path, "Resultados")
            self.diagrama_interaccion_wb = ExcelManager(file_path, "Diagrama de Interacción 2D")
            # warnings.filterwarnings("error")

            self.def_de_rotura_a_pasivo = self.obtener_def_de_rotura_a_pasivo()
            self.def_de_pretensado_inicial = self.obtener_def_de_pretensado_inicial()
            self.hormigon = Hormigon(tipo=self.ingreso_datos_wb.get_value("C", "4"))  # TODO mejorar
            self.tipo_estribo = self.ingreso_datos_wb.get_value("E", "10")

            self.setear_propiedades_acero_pasivo()
            self.setear_propiedades_acero_activo()
            self.medir_diferencias = []

            self.seccion_H = self.obtener_matriz_hormigon()
            self.discretizacion = {"ΔX": f"{round(self.seccion_H.dx,2)}cm" if self.seccion_H.dx else None,
                                   "ΔY": f"{round(self.seccion_H.dy,2)}cm" if self.seccion_H.dy else None,
                                   "Δr": f"{round(self.seccion_H.dr,2)}cm" if self.seccion_H.dr else None,
                                   "Δθ": f"{round(self.seccion_H.d_ang,2)}°" if self.seccion_H.d_ang else None}
            self.EEH = self.seccion_H.elementos
            self.XG, self.YG = self.seccion_H.xg, self.seccion_H.yg

            self.EA = self.obtener_matriz_acero_pasivo()
            self.EAP = self.obtener_matriz_acero_pretensado()

            self.deformacion_maxima_de_acero = self.obtener_deformacion_maxima_de_acero()
            self.planos_de_deformacion = self.obtener_planos_de_deformacion()
            # self.mostrar_planos_de_deformacion()
            ec, phix, phiy = self.obtener_plano_deformación_inicial()
            # self.print_result_tridimensional(ec, phix, phiy)
            self.ec_plano_deformacion_elastica_inicial = lambda x, y: ec + math.tan(math.radians(phix)) * (
                y) + math.tan(
                math.radians(phiy)) * (x)
            self.asignar_deformacion_hormigon_a_elementos_pretensados()

            self.lista_planos_sin_solucion = []
            self.construir_grafica_seccion()
            if mostrar_seccion:
                self.mostrar_seccion(**kwargs)

            self.lista_resultados = self.iterar()
            normal_momento_phi = [[-x[0], x[1], x[4]] for x in self.lista_resultados]
            self.diagrama_interaccion_wb.insert_values_vertically("I3", normal_momento_phi)
            print(
                f"Se obtuvieron {len(self.lista_planos_sin_solucion)}/{len(self.lista_resultados)} ({round(len(self.lista_planos_sin_solucion) / len(self.lista_resultados) * 100, 2)}%) "
                f"puntos sin solución,"
                f"\nTotal: {len(self.lista_planos_sin_solucion) + len(self.lista_resultados)}"
                f"\nDetalles:"
                # f"{self.lista_planos_sin_solucion}"
                )
            # if mostrar_resultado:
            #     self.mostrar_resultado()
        except Exception as e:
            traceback.print_exc()
            raise e
        finally:
            logging.log(1, "Se terminó la ejecución")
        # self.medir_diferencias.sort(reverse=True)
        # print(self.medir_diferencias)
        # self.mostrar_resultado(blanco_y_negro=False)

    def coordenadas_de_puntos_en_3d(self):
        X, Y, Z = [], [], []
        color_lista = []
        for resultado in self.lista_resultados:
            sum_f, momento, plano_def, tipo, phi = resultado
            momento = momento / 100
            x = math.cos(math.radians(self.angulo_plano_de_carga_esperado)) * momento
            y = math.sin(math.radians(self.angulo_plano_de_carga_esperado)) * momento
            z = -sum_f  # Negativo para que la compresión quede en cuadrante I y II del diagrama.
            X.append(x)
            Y.append(y)
            Z.append(z)
            color_lista.append(self.numero_a_color_arcoiris(abs(plano_def[3])))
        return (X, Y, Z), color_lista

    def obtener_plano_deformación_inicial(self):
        """Obtiene los parámetros del plano de deformación elástica inicial del hormigón, a partir de la acción del
        pretensado sobre dicha sección."""
        if not self.EAP:  # Caso de Hormigón Armado
            return 0, 0, 0
        print("Se intentará obtener las deformaciones iniciales de pretensado.")
        resultado = fsolve(
            self.función_desplazamiento_a_converger,
            [-self.def_de_pretensado_inicial, 0, 0],
            maxfev=100,
            full_output=1)
        if not (resultado[2]):
            raise Exception("No se encontró deformación inicial que satisfaga las ecuaciones de equilibrio")
        ec, phix, phiy = resultado[0]
        print(f"Deformaciones iniciales (deformación elástica del hormigón)\nec: {ec}\nphix: {phix}\nphiy: {phiy}")
        return ec, phix, phiy

    def función_desplazamiento_a_converger(self, c):
        (ec, phix, phiy) = c
        return self.calcular_sumatoria_de_fuerzas_en_base_a_plano_baricentrico(ec, phix, phiy)

    def obtener_deformacion_maxima_de_acero(self):
        def_max_acero_pasivo = BarraAceroPasivo.eu
        def_max_acero_activo = BarraAceroPretensado.epu
        return min(def_max_acero_pasivo, def_max_acero_activo)

    def obtener_def_de_rotura_a_pasivo(self):
        value = self.armaduras_pasivas_wb.get_value("B", 6)  # TODO mejorar
        return value

    def obtener_def_de_pretensado_inicial(self):
        value = self.ingreso_datos_wb.get_value("E", 8)  # TODO mejorar
        return value / 1000

    def construir_grafica_seccion(self):
        """Muestra la sección obtenida luego del proceso de discretización."""
        plt.rcParams["font.family"] = "Times New Roman"
        fig, ax = plt.subplots()
        self.EA.cargar_barras_como_circulos_para_mostrar(ax)
        self.EAP.cargar_barras_como_circulos_para_mostrar(ax)
        self.seccion_H.mostrar_contornos_2d(ax)
        self.seccion_H.mostrar_discretizacion_2d(ax)
        # self.mostrar_plano_de_carga(ax)
        # plt.suptitle("ACSAHE\nSección y Discretización", fontsize=20, fontweight='bold', horizontalalignment='center')
        plt.title(f"Tamaño Elementos:\n{' '.join([f'{k}={v}' for k,v in self.discretizacion.items() if v])}",
                  fontsize=16, horizontalalignment='center', style='italic')
        plt.axis('equal')
        ax.set_xlabel("Dimensiones en Horizontal [cm]", loc="center", fontsize=8, fontweight='bold')
        ax.set_ylabel("Dimensiones en Vertical [cm]", loc="center", fontsize=8, fontweight='bold')
        plt.xticks(fontsize=8)
        plt.yticks(fontsize=8)
        self.diagrama_interaccion_wb.sh.pictures.add(fig, name="geometria", update=True, left=self.diagrama_interaccion_wb.sh.range("L3").left, top=self.diagrama_interaccion_wb.sh.range("I3").top, export_options={"bbox_inches": "tight", "dpi": 220})

    def construir_grafica_seccion_plotly(self, fig=None):
        """Muestra la sección obtenida luego del proceso de discretización."""
        if not fig:
            fig = go.Figure(layout_template="plotly_dark")
        fig.update_yaxes(
            scaleanchor="x",
            scaleratio=1,
        )
        self.seccion_H.mostrar_contornos_2d_plotly(fig)
        self.seccion_H.mostrar_discretizacion_2d_plotly(fig)
        self.EA.cargar_barras_como_circulos_para_mostrar_plotly(fig)
        self.EAP.cargar_barras_como_circulos_para_mostrar_plotly(fig)

        # self.mostrar_plano_de_carga(ax)
        # plt.title("Sección y Discretización", fontsize=40, fontweight='bold', horizontalalignment='center')
        # plt.axis('equal')
        # ax.set_xlabel("Dimensiones en Horizontal [cm]", loc="center", fontsize=20, fontweight='bold')
        # ax.set_ylabel("Dimensiones en Vertical [cm]", loc="center", fontsize=20, fontweight='bold')
        # plt.xticks(fontsize=16)
        # plt.yticks(fontsize=16)

        fig.update_layout(

            title=dict(
                text=f'<b>SECCIÓN Y DISCRETIZACIÓN<br></b>',
                x=0.5,
                font=dict(size=25, color="rgb(142, 180, 227)",
                          family='Times New Roman')),
            scene=dict(
                xaxis_title='X [cm]',
                yaxis_title='Y [cm]',
                xaxis=dict(
                    title_font=dict(family='Times New Roman'),
                    range=(self.seccion_H.x_min, self.seccion_H.x_max)

                ),
                yaxis=dict(
                    title_font=dict(family='Times New Roman'),
                    range=(self.seccion_H.y_min, self.seccion_H.y_max)

                )),
            # aspectmode='manual',  # Set aspect ratio manually
            # aspectratio=dict(x=1, y=1)
            )
        fig.show()
        return fig


    def construir_grafica_seccion_plotly(self, fig=None):
        """Muestra la sección obtenida luego del proceso de discretización."""
        if not fig:
            fig = go.Figure(layout_template="plotly_dark")
        fig.update_yaxes(
            scaleanchor="x",
            scaleratio=1,
        )
        self.seccion_H.mostrar_contornos_2d_plotly(fig)
        self.seccion_H.mostrar_discretizacion_2d_plotly(fig)
        plotly_util = PlotlyUtil()
        plotly_util.cargar_barras_como_circulos_para_mostrar_plotly(fig, self.EA, self.EAP)


        # self.mostrar_plano_de_carga(ax)
        # plt.title("Sección y Discretización", fontsize=40, fontweight='bold', horizontalalignment='center')
        # plt.axis('equal')
        # ax.set_xlabel("Dimensiones en Horizontal [cm]", loc="center", fontsize=20, fontweight='bold')
        # ax.set_ylabel("Dimensiones en Vertical [cm]", loc="center", fontsize=20, fontweight='bold')
        # plt.xticks(fontsize=16)
        # plt.yticks(fontsize=16)

        fig.update_layout(

            title=dict(
                text=f'<b>SECCIÓN Y DISCRETIZACIÓN<br></b>',
                x=0.5,
                font=dict(size=25, color="rgb(142, 180, 227)",
                          family='Times New Roman')),
            scene=dict(
                xaxis_title='X [cm]',
                yaxis_title='Y [cm]',
                xaxis=dict(
                    title_font=dict(family='Times New Roman'),
                    range=(self.seccion_H.x_min, self.seccion_H.x_max)

                ),
                yaxis=dict(
                    title_font=dict(family='Times New Roman'),
                    range=(self.seccion_H.y_min, self.seccion_H.y_max)

                )),
            # aspectmode='manual',  # Set aspect ratio manually
            # aspectratio=dict(x=1, y=1)
            )
        # fig.show()
        return fig

    def mostrar_seccion(self, usar_plotly=True, **kwargs):
        if usar_plotly is False:
            self.construir_grafica_seccion()
        else:
            self.construir_grafica_seccion_plotly()
        plt.show()

    def guardar_seccion(self):
        print("Construyendo Gráfica de la sección")
        path = f"Resultados/{self.file_name}"
        if not os.path.exists(path):
            os.makedirs(path)
        self.construir_grafica_seccion()
        print(f"Guardando sección en {path}")
        plt.savefig(f"{path}/Sección.png")

    def mostrar_plano_de_carga(self, ax):
        y1, y2 = ax.get_ylim()
        x1, x2 = ax.get_xlim()
        ecuacion_plano_carga = lambda x: math.tan(math.radians(
            90 - self.angulo_plano_de_carga_esperado)) * x if self.angulo_plano_de_carga_esperado != 0 else y1 if x < 0 else y2
        linea_plano_de_carga = Segmento(Nodo(x1, ecuacion_plano_carga(x1)),
                                        Nodo(x2, ecuacion_plano_carga(
                                            x2))) if self.angulo_plano_de_carga_esperado != 0 else Segmento(
            Nodo(0, ecuacion_plano_carga(x1)), Nodo(0, ecuacion_plano_carga(x2)))
        linea_plano_de_carga.plot(linewidth=5, c="k")
        plt.text(linea_plano_de_carga.nodo_2.x + 2,
                 (linea_plano_de_carga.nodo_2.y + linea_plano_de_carga.nodo_1.y) / 2 - 2,
                 f"Plano de Carga λ={self.angulo_plano_de_carga_esperado}°",
                 rotation=90 - self.angulo_plano_de_carga_esperado, fontsize=15)

    def mostrar_planos_de_deformacion(self):
        plt.rcParams["font.family"] = "Times New Roman"
        lista_colores = ["k", "r", "b", "g", "c", "m", "y", "k"]
        fig, ax = plt.subplots()
        ax.plot([0, 0], [1, -1], c="k", linewidth=7, zorder=10, linestyle="dashed")  # Plano 0
        for p_def in self.planos_de_deformacion:
            plt.title("Planos de Deformación Límite", fontsize=16)
            tipo = p_def[2]
            if tipo >= 0:
                c = self.obtener_color_kwargs(p_def, arcoiris=True)
                ax.plot([-p_def[0] * 1000, -p_def[1] * 1000], [1, -1],
                        # c=lista_colores[tipo],
                        linewidth=2, zorder=1, alpha=1, **c)
                # ax.add_patch(Rectangle((3,-1),2,2, facecolor="grey"))
        ax.set_xlabel("Deformación [‰]", loc="center", fontsize=8, fontweight='bold')
        ax.tick_params(axis='x', labelsize=14)
        ax.tick_params(axis='y', labelsize=14)
        ax.set_ylabel("Altura de la sección para el plano estudiado (%H)", loc="center", fontsize=8, fontweight='bold')
        plt.locator_params(axis='y', nbins=2)
        labels = [item.get_text() for item in ax.get_yticklabels()]
        labels[3] = "H/2"
        labels[1] = "-H/2"
        ax.set_yticklabels(labels)
        plt.xticks([3, -self.deformacion_maxima_de_acero*1000], ["Aplastamiento H° 3‰", "Rotura acero pasivo/activo"], rotation='vertical')
        # ax.set_facecolor((0, 0, 0))
        self.diagrama_interaccion_wb.add_plot(fig, "L24", name="planos")

    def mostrar_resultado(self, blanco_y_negro=False):
        fig = self.construir_grafica_resultado(arcoiris=True, blanco_y_negro=blanco_y_negro)
        self.diagrama_interaccion_wb.add_plot(fig, name="di", location="L30")
        plt.show()

    def guardar_resultado(self, blanco_y_negro=False):
        print("Construyendo Gráfica de resultado")
        path = f"Resultados/{self.file_name}"
        if not os.path.exists(path):
            os.makedirs(path)
        self.construir_grafica_resultado(blanco_y_negro)
        print(f"Guardando Diagrama de Interacción en {path}/Diagrama de Interacción")
        plt.savefig(f"{path}/Diagrama de Interacción.png")

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

        self.preparar_eje(ax)

        for resultado in self.lista_resultados:
            sumF, M, plano_def, tipo, phi = resultado
            x = M / 100  # Pasaje de kNcm a kNm
            y = -sumF  # Negativo para que la compresión quede en cuadrante I y II del diagrama.
            X.append(x)
            Y.append(y)
            color_kwargs = self.obtener_color_kwargs(plano_def,
                                                     arcoiris=arcoiris,
                                                     blanco_y_negro=blanco_y_negro)
            plt.scatter(x, y,
                        marker=".",
                        s=100,
                        **color_kwargs
                        # if tipo >= 0 else "x"
                        )
        # for resultado in self.lista_resultados:
        #     sumF, M, plano_def, tipo, phi = resultado
        #     x = M / 100  # kN/m²
        #     y = -sumF  # kN
        #     #     # plt.annotate(str(phi), (x,y))
        #     #     plt.annotate(str(f"{round(plano_def[0]*1000, 3)}/{round(plano_def[1]*1000, 3)}"), (x, y))
        #     plt.annotate(plano_def[3], (x, y))
        # plt.annotate(str(plano_def), (x,y))
        return fig

    def obtener_color_kwargs(self, plano_de_def, arcoiris=False, blanco_y_negro=False):
        lista_colores = ["k", "r", "b", "g", "c", "m", "y", "k"]
        if arcoiris:
            return {"color": self.numero_a_color_arcoiris(abs(plano_de_def[3]))}
        return {"c": lista_colores[abs(plano_de_def[2])] if blanco_y_negro is False else "k"}

    @staticmethod
    def preparar_eje(ax):
        # Mueve al centro del diagrama al eje X e Y (por defecto, se sitúan en el extremo inferior izquierdo).
        ax.yaxis.tick_right()

        ax.spines['left'].set_position('zero')
        ax.spines['bottom'].set_position('zero')

        # Elimina los viejos ejes
        ax.spines['right'].set_color('none')
        ax.spines['top'].set_color('none')

        # Agrega los 'tics' (marcas en el eje) en los trozos de ejes agregados
        ax.xaxis.set_ticks_position('bottom')
        ax.yaxis.set_ticks_position('left')

        # Agregamos las grilla de referencia
        ax.grid(which='major', color='#DDDDDD', linewidth=0.8)
        ax.grid(which='minor', color='#EEEEEE', linestyle=':', linewidth=0.6)
        ax.minorticks_on()

        # Desplazamos los valores de y a la izquierda
        return ax

    def asignar_deformacion_hormigon_a_elementos_pretensados(self):
        ec_plano = self.ec_plano_deformacion_elastica_inicial
        for elemento_pretensado in self.EAP:
            elemento_pretensado.def_elastica_hormigon_perdidas = ec_plano(elemento_pretensado.xg,
                                                                          elemento_pretensado.yg)

    def iterar(self):
        lista_de_puntos = []
        try:
            for plano_de_deformacion in self.planos_de_deformacion:
                sol = fsolve(self.evaluar_diferencia_para_inc_eje_neutro,
                             x0=self.angulo_plano_de_carga_esperado,
                             xtol=0.001,
                             args=plano_de_deformacion,
                             full_output=1,
                             maxfev=100)  # Max fev = número de iteraciones máximo
                theta, diferencia_plano_de_carga, sol_encontrada = sol[0][0], sol[1]['fvec'], sol[2] == 1
                # test = self.evaluar_diferencia_para_inc_eje_neutro(theta, *plano_de_deformacion)
                self.medir_diferencias.append((diferencia_plano_de_carga, plano_de_deformacion))
                if sol_encontrada is True and abs(diferencia_plano_de_carga) < diferencia_admisible:
                    sumF, Mx, My, phi = self.obtener_resultante_para_theta_y_def(theta, *plano_de_deformacion)
                    lista_de_puntos.append(
                        [sumF, self.obtener_momento_resultante(Mx, My), plano_de_deformacion, plano_de_deformacion[2],
                         phi])

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
        if ex == 0 and ey == 0:  # Carga centrada, siempre "pertenece" al plano de carga
            return 0
        angulo_plano_de_carga = self.obtener_angulo_resultante_momento(Mx, My)
        alpha = 90 - self.angulo_plano_de_carga_esperado
        if alpha < 0:
            alpha = 180 + alpha
        diferencia = angulo_plano_de_carga - alpha  # Apuntamos a que esto sea 0
        return diferencia

    @staticmethod
    def obtener_momento_resultante(Mx, My):
        return (1 if Mx >= 0 else -1) * math.sqrt(Mx ** 2 + My ** 2)

    @staticmethod
    def obtener_angulo_resultante_momento(Mx, My):
        M = math.sqrt(Mx ** 2 + My ** 2)
        if M == 0:
            return
        if abs(My) > 10:  # Valores muy cercanos a 0 tienden a desestabilizar esta comparación
            inclinacion_vector_momento = math.degrees(math.acos(My / M))
        elif abs(Mx) > 10:
            inclinacion_vector_momento = math.degrees(math.asin(Mx / M))
        elif My != 0:
            inclinacion_vector_momento = math.degrees(math.atan(Mx / My))
        else:  # My = 0 implica plano de carga vertical
            inclinacion_vector_momento = 0
        return inclinacion_vector_momento

    def obtener_ecuacion_plano_deformacion(self, EEH_girado, EA_girado, EAP_girado, plano_de_deformacion):
        """Construye la ecuación de una recta que pasa por los puntos (y_positivo,def_1) (y_negativo,def_2).
        Y_positivo e y_negativo serán la distancia al eje neutro del elemento de hormigón más comprimido, o
        de la barra de acero (pasivo o activo) más traicionada. Lo positivo o negativo depende de qué lado del
        eje neutro se encuentra el análisis."""
        def_1, def_2 = plano_de_deformacion[0], plano_de_deformacion[1]
        y_positivo = self.obtener_y_determinante_positivo(def_1, EA_girado, EAP_girado, EEH_girado)
        y_negativo = self.obtener_y_determinante_negativo(def_2, EA_girado, EAP_girado, EEH_girado)
        A = (def_1 - def_2) / (y_positivo - y_negativo)
        B = def_2 - A * y_negativo
        return lambda y_girado: y_girado * A + B

    def obtener_y_determinante_positivo(self, def_extrema, EA_girado, EAP_girado, EEH_girado):
        """Lo positivo indica que se encuentra con coordendas y_girado positivas (de un lado del eje neutro)"""
        if def_extrema <= 0 or def_extrema < self.deformacion_maxima_de_acero:  # Compresión
            return EEH_girado[-1].y_girado  # Fibra de Hormigón más alejada
        lista_de_armaduras = []
        lista_de_armaduras.extend(EA_girado)
        lista_de_armaduras.extend(EAP_girado)
        return max(x.y_girado for x in lista_de_armaduras)  # Armadura más traccionada (más alejada del EN)

    def obtener_y_determinante_negativo(self, def_extrema, EA_girado, EAP_girado, EEH_girado):
        """Lo negativo indica que se encuentra con coordenadas y_girado negativas (de un lado del eje neutro)"""
        if def_extrema <= 0 or def_extrema < self.deformacion_maxima_de_acero:
            return EEH_girado[0].y_girado  # Maxima fibra comprimida hormigón

        lista_de_armaduras = []
        lista_de_armaduras.extend(EA_girado)
        lista_de_armaduras.extend(EAP_girado)
        return min(x.y_girado for x in lista_de_armaduras)  # Armadura más traccionada (más alejada del EN)

    def calculo_distancia_eje_neutro_de_elementos(self, theta):
        EEH_girado, EA_girado, EAP_girado = self.EEH.copy(), self.EA.copy(), self.EAP.copy()
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

    # def obtener_angulo_plano_de_carga(self):
    #     rows_n = self.excel_wb.get_n_rows_after_value("INCLINACIÓN DEL PLANO DE CARGA", 5)
    #     return self.excel_wb.get_value("E", rows_n[2])  # TODO mejorar

    @staticmethod
    def numero_a_color_arcoiris(numero):
        if numero < 0 or numero > 350:
            raise ValueError("El número debe estar entre 0 y 350")

        numero_normalizado = numero / 350.0

        rojo = int(max(0, min(255, 255 * (1 - numero_normalizado))))
        verde = int(max(0, min(255, 255 * (1 - abs(numero_normalizado - 0.5) * 2))))
        azul = int(max(0, min(255, 255 * numero_normalizado)))

        return [rojo / 255, verde / 255, azul / 255]

    def obtener_matriz_acero_pasivo(self):
        lista_filas = self.ingreso_datos_wb.get_rows_range_between_values(
            ("ARMADURAS PASIVAS (H°- Armado)", "ARMADURAS ACTIVAS (H°- Pretensado)"))
        resultado = MatrizAceroPasivo()
        for fila in lista_filas[5:-1]:  # TODO mejorar
            x, y, d = self.obtener_valores_acero_tabla(fila)
            if d == 0:
                continue
            xg = round(x - self.XG, 5)
            yg = round(y - self.YG, 5)
            resultado.append(BarraAceroPasivo(xg, yg, d))
        return resultado

    def verificar_tolerancia(self, valor):
        tolerancia = 0.00000000000004
        return 0 if abs(valor) <= tolerancia else valor

    def obtener_valores_acero_tabla(self, fila):
        return self.ingreso_datos_wb.get_value("C", fila), self.ingreso_datos_wb.get_value("E", fila), self.ingreso_datos_wb.get_value("G", fila)

    def setear_propiedades_acero_pasivo(self):
        try:
            tipo = self.ingreso_datos_wb.get_value("C", "6")
            values = BarraAceroPasivo.tipos_de_acero_y_valores.get(tipo)
            for k, v in values.items():
                self.__setattr__(k, v)
            fy = BarraAceroPasivo.tipos_de_acero_y_valores.get(tipo.upper())["fy"]
            BarraAceroPasivo.E = 200000
            BarraAceroPasivo.tipo = tipo
            BarraAceroPasivo.fy = fy
            BarraAceroPasivo.eu = self.def_de_rotura_a_pasivo
        except Exception:
            raise Exception("No se pudieron setear las propiedades del acero pasivo, revise configuración")

    def obtener_matriz_acero_pretensado(self):
        lista_filas = self.ingreso_datos_wb.get_rows_range_between_values(
            ("ARMADURAS ACTIVAS (H°- Pretensado)", "DISCRETIZACIÓN DE LA SECCIÓN"))
        resultado = MatrizAceroActivo()
        for fila in lista_filas[5:-1]:  # TODO mejorar
            x, y, area = self.obtener_valores_acero_tabla(fila)
            if area == 0:
                continue
            xg = round(x - self.XG, 5)
            yg = round(y - self.YG, 5)
            resultado.append(BarraAceroPretensado(xg, yg, area))
        return resultado

    def setear_propiedades_acero_activo(self):
        try:
            tipo = self.ingreso_datos_wb.get_value("C", "8")
            tipo = tipo.upper()
            values = BarraAceroPretensado.tipos_de_acero_y_valores.get(tipo)
            for k, v in values.items():
                setattr(BarraAceroPretensado, k, v)
            BarraAceroPretensado.tipo = tipo
            BarraAceroPretensado.Eps = 20000  # kN/cm²
            BarraAceroPretensado.deformacion_de_pretensado_inicial = self.def_de_pretensado_inicial
        except Exception:
            raise Exception("No se pudieron setear las propiedades del acero activo, revise configuración")

    def obtener_indice(self, contorno):
        value = self.ingreso_datos_wb.get_value("A", contorno[0])
        return value.split()[-1]

    def obtener_signo(self, contorno):
        value = self.ingreso_datos_wb.get_value("C", contorno[0])
        return +1 if "Pos" in value else -1

    def obtener_tipo(self, contorno):
        value = self.ingreso_datos_wb.get_value("E", contorno[0])
        return value

    def get_cantidad_de_nodos(self, contorno):  # TODO mejorar
        return self.ingreso_datos_wb.get_value("G", contorno[0])

    def obtener_matriz_hormigon(self):
        filas_hormigon = self.ingreso_datos_wb.get_rows_range_between_values(
            ("GEOMETRÍA DE LA SECCIÓN DE HORMIGÓN", "ARMADURAS PASIVAS (H°- Armado)"))
        lista_filas_contornos = self.ingreso_datos_wb.subdivide_range_in_contain_word("A", filas_hormigon, "Contorno")
        contornos = {}
        coordenadas_nodos = []
        delta_x = []
        delta_y = []
        for i, filas_contorno in enumerate(lista_filas_contornos):
            signo = self.obtener_signo(filas_contorno)
            tipo = self.obtener_tipo(filas_contorno)
            indice = self.obtener_indice(filas_contorno)
            if tipo == "Poligonal":
                cantidad_de_nodos = int(self.get_cantidad_de_nodos(filas_contorno))
                for fila_n in self.ingreso_datos_wb.get_n_rows_after_value("Nodo Nº", cantidad_de_nodos + 1,
                                                                           rows_range=filas_contorno)[1:]:
                    x = self.ingreso_datos_wb.get_value("C", fila_n)
                    y = self.ingreso_datos_wb.get_value("E", fila_n)
                    coordenadas_nodos.append(Nodo(x, y))  # Medidas en centímetros
                contorno = Contorno(coordenadas_nodos, signo, indice, ordenar=True)
                if signo > 0:  # Solo se utilizan los contornos positivos para definir la discretización
                    delta_x.append(abs(max(contorno.x)-min(contorno.x)))
                    delta_y.append(abs(max(contorno.y)-min(contorno.y)))
                contornos[str(i + 1)] = contorno
                coordenadas_nodos = []
            elif tipo == "Circular":
                x = self.ingreso_datos_wb.get_value_on_the_right("Nodo Centro", filas_contorno, 2)
                y = self.ingreso_datos_wb.get_value_on_the_right("Nodo Centro", filas_contorno, 4)
                r_int = self.ingreso_datos_wb.get_value_on_the_right("Radio Interno [cm]", filas_contorno, 2)
                r_ext = self.ingreso_datos_wb.get_value_on_the_right("Radio Externo [cm]", filas_contorno, 2)
                if signo > 0:
                    delta_x.append(r_ext-r_int)
                    delta_y.append(r_ext-r_int)
                contornos[str(i + 1)] = ContornoCircular(nodo_centro=Nodo(x, y),indice=indice, radios=(r_int, r_ext), signo=signo)
            else:
                pass
        EEH = SeccionArbitraria(contornos, discretizacion=self.get_discretizacion(delta_x, delta_y, contornos))
        return EEH

    def get_discretizacion(self, delta_x, delta_y, contornos):
        hay_contorno_circular = any(isinstance(x, ContornoCircular) for x in contornos)
        hay_contorno_rectangular = any(not isinstance(x, ContornoCircular) for x in contornos)
        rows_range = self.ingreso_datos_wb.get_n_rows_after_value("DISCRETIZACIÓN DE LA SECCIÓN", 20)
        nivel_discretizacion = self.ingreso_datos_wb.get_value_on_the_right("Nivel de Discretización", rows_range, 2)
        if nivel_discretizacion == "Avanzada (Ingreso Manual)":
            dx = self.ingreso_datos_wb.get_value_on_the_right("ΔX [cm] =", rows_range, 2)
            dy = self.ingreso_datos_wb.get_value_on_the_right("ΔY [cm] =", rows_range, 2)
            d_ang = self.ingreso_datos_wb.get_value_on_the_right("Δθ [°] =", rows_range, 2)
            return (dx if hay_contorno_rectangular else None,
                    dy if hay_contorno_rectangular else None,
                    min(dx, dy) if hay_contorno_circular else None,
                    d_ang if hay_contorno_circular else None)
        factor_rectangular = 1/self.niveles_mallado_rectangular.get(nivel_discretizacion)
        factor_circular = self.niveles_mallado_circular.get(nivel_discretizacion)

        return (factor_rectangular * max(delta_x) if hay_contorno_rectangular else None,
                factor_rectangular * max(delta_y) if hay_contorno_rectangular else None,
                factor_circular[0] if hay_contorno_circular else None,
                factor_circular[1] if hay_contorno_circular else None)

    def obtener_factor_minoracion_de_resistencia(self, EA_girado, EAP_girado, ecuacion_plano_de_def, tipo_estribo):
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

    def calcular_sumatoria_de_fuerzas_en_base_a_eje_neutro_girado(
            self, EEH_girado, EA_girado, EAP_girado, ecuacion_plano_deformacion):
        y_max, y_min = EEH_girado[-1].y_girado, EEH_girado[0].y_girado
        sumFA = sumFP = sumFH = 0
        MxA = MxAP = MxH = 0
        MyA = MyAP = MyH = 0
        e1, e2 = ecuacion_plano_deformacion(y_max), ecuacion_plano_deformacion(y_min)

        def_max_comp = min(e1, e2)

        # c = def_max_comp*(y_max-y_min)/(-e1+e2)

        for barra in EA_girado:
            dist_eje_neutro, def_elemento, area = barra.y_girado, ecuacion_plano_deformacion(barra.y_girado), barra.area
            FA = barra.relacion_constitutiva(def_elemento) * area
            sumFA = sumFA + FA
            MxA = FA * barra.yg + MxA
            MyA = -FA * barra.xg + MyA

        deformaciones_pp = []
        for barra_p in EAP_girado:
            dist_eje_neutro, deformacion_neta, area = barra_p.y_girado, ecuacion_plano_deformacion(
                barra_p.y_girado), barra_p.area
            deformacion_hormigon = barra_p.def_elastica_hormigon_perdidas
            deformacion_pretensado_inicial = barra_p.deformacion_de_pretensado_inicial
            deformacion_total = deformacion_neta + deformacion_hormigon + deformacion_pretensado_inicial

            deformaciones_pp.append(
                {
                    "elastica": deformacion_hormigon,
                    "inicial": deformacion_pretensado_inicial,
                    "neta": deformacion_neta,
                    "total": deformacion_total
                }
            )

            Fp = barra_p.relacion_constitutiva(deformacion_total) * area
            sumFP = sumFP + Fp
            MxAP = Fp * barra_p.yg + MxAP
            MyAP = -Fp * barra_p.xg + MyAP

        for elemento in EEH_girado:
            def_elemento, area = ecuacion_plano_deformacion(elemento.y_girado), elemento.area
            F_hor = self.hormigon.relacion_constitutiva_simplificada(def_elemento, e_max_comp=def_max_comp) * area
            sumFH = sumFH + F_hor
            MxH = F_hor * elemento.yg + MxH
            MyH = -F_hor * elemento.xg + MyH

        factor_minoracion_de_resistencia = self.obtener_factor_minoracion_de_resistencia(
            EA_girado, EAP_girado, ecuacion_plano_deformacion, self.tipo_estribo)
        # factor_minoracion_de_resistencia = 1
        resultados_parciales = {
            "H": {"F": sumFH,
                  "Mx": MxH,
                  "My": MyH},
            "A": {"F": sumFA,
                  "Mx": MxA,
                  "My": MyA},
            "AP": {"F": sumFP,
                   "Mx": MxAP,
                   "My": MyAP}
        }

        sumF = sumFA + sumFP + sumFH
        Mx = round(MxA + MxAP + MxH, 8)
        My = round(MyA + MyAP + MyH, 8)

        sumF = factor_minoracion_de_resistencia * sumF
        Mx = factor_minoracion_de_resistencia * Mx
        My = factor_minoracion_de_resistencia * My
        return sumF, Mx, My, factor_minoracion_de_resistencia

    def print_result_tridimensional(self, ec, phix, phiy):
        ec_plano = lambda x, y: ec + math.tan(math.radians(phix)) * y + math.tan(math.radians(phiy)) * x
        self.seccion_H.mostrar_contornos_3d(ecuacion_plano_a_desplazar=ec_plano)


class ObtenerDiagramaDeInteraccion3D:

    def __init__(self, file_path, usar_plotly=False, **kwargs):
        # self.lista_de_angulos_de_carga = [0, 45*1/4, 45*0.5,45*3/4, 45,45*5/4, 45*1.5, 45*7/4, 90,45*9/4, 45*2.5, 45*11/4, 135, 45*13/4, 45*14/4, 45*16/4]
        self.lista_de_angulos_de_carga = [0, 45, 90,135]
        lista_x_total, lista_y_total, lista_z_total, lista_color = [], [], [], []
        for angulo_plano_de_carga in self.lista_de_angulos_de_carga:
            warnings.simplefilter(action='ignore', category=UserWarning)
            solucion_parcial = ObtenerDiagramaDeInteraccion2D(file_path, angulo_plano_de_carga, mostrar_resultado=False, mostrar_seccion=False, **kwargs)
            coordenadas, color = solucion_parcial.coordenadas_de_puntos_en_3d()
            lista_x_parcial, lista_y_parcial, lista_z_parcial = coordenadas
            lista_x_total.extend(lista_x_parcial)
            lista_y_total.extend(lista_y_parcial)
            lista_z_total.extend(lista_z_parcial)
            lista_color.extend(color)

        if usar_plotly is False:
            fig = plt.figure()
            ax = fig.add_subplot(111, projection='3d')
            ax.set_xlabel("My [kNm]", loc="center", fontsize=12, fontweight='bold')
            ax.set_ylabel("Mx [kNm]", loc="center", rotation=0, rotation_mode="anchor", fontsize=12,
                          fontweight='bold')
            ax.set_zlabel("N [kN]", fontsize=12, fontweight='bold')

            ax.scatter(lista_x_total, lista_y_total, lista_z_total, color=lista_color, marker=".", alpha=0.8)
            plt.suptitle("    DIAGRAMA DE INTERACCIÓN", fontsize=20, fontweight='bold', horizontalalignment='center')
            # plt.savefig("test.pdf")
            plt.show()
        else:
            fig_1 = go.Scatter3d(
                    name="Data 1",
                    x=lista_x_total,
                    y=lista_y_total,
                    z=lista_z_total,
                    mode='markers',
                    marker=dict(
                        size=2,  # Adjust marker size as needed
                        color=lista_z_total,  # Map colors to the Z values
                        colorscale='Rainbow',  # Choose a color scale ('Rainbow' in this case)
                    ),
                    showlegend=False
                )
            fig2 = solucion_parcial.construir_grafica_seccion_plotly()

            fig = make_subplots(rows=2, cols=1,
                                specs=[
                                [{"type": "scatter"}], [{"type": "scene"}]],
                                subplot_titles=(f'Sección y Discretización<br>dx={solucion_parcial.dx}, dy={solucion_parcial.dx}', 'Diagrama de Interacción 3D'))
            fig_1 = go.Figure(data=fig_1, layout_template="plotly_dark")
            fig.update_layout(**fig2.layout.to_plotly_json())
            for x in fig2["data"]:
                fig.add_trace(
                    x, row=1, col=1
                )
            fig.add_trace(fig_1["data"][0], row=2, col=1)
            fig.update_layout(
                           title=dict(
                               text=f"<b>{kwargs.get('titulo')}<br>ACSAHE V.1.0.0</b>",
                               x=0.5,
                               font=dict(size=25, color="rgb(142, 180, 227)",
                                         family='Times New Roman')),
                           scene=dict(
                               xaxis_title='My [kNm]',
                               yaxis_title='Mx [kNm]',
                               zaxis_title='N [kN]',
                               xaxis=dict(
                                   title_font=dict(family='Times New Roman'),

                                   range=[min(lista_x_total), max(lista_x_total)]
                               ),
                               yaxis=dict(
                                   title_font=dict(family='Times New Roman'),
                                   range=[min(lista_y_total), max(lista_y_total)]
                               ),
                               zaxis=dict(
                                   title_font=dict(family='Times New Roman'),
                                   range=[min(lista_z_total), max(lista_z_total)]),
                               aspectmode='manual',  # Set aspect ratio manually
                               aspectratio=dict(x=1, y=1, z=1)
                           ))
            # fig.update_scenes(aspectmode='data')

            fig.write_html(f"{kwargs.get('titulo')} 1.html")
            fig.show()
