import plotly.graph_objects as go
import hashlib
import math
import numpy as np


class PlotlyUtil(object):
    def __init__(self, fig=None, indice_color=0):
        self.fig = self.obtener_fig(fig)
        self.indice_color = indice_color
        self.strings_y_color = {}

    @staticmethod
    def obtener_fig(fig):
        if fig is not None:
            return fig
        fig = go.Figure(layout_template="plotly_dark")
        fig.update_yaxes(
            scaleanchor="x",
            scaleratio=1,
        )
        return fig

    def colores_random_por_string(self, string):
        crimson_scale_colors = [
            "rgb(255, 0, 0)",  # Pure Red
            "rgb(255, 255, 0)",  # Yellow
            "rgb(0, 0, 255)",  # Blue
            "rgb(0, 128, 0)",  # Green
            "rgb(255, 0, 255)",  # Magenta
            "rgb(255, 140, 0)",  # Dark Orange
            "rgb(0, 255, 255)",  # Cyan
            "rgb(128, 0, 128)",  # Purple
            "rgb(255, 165, 0)",  # Orange
            "rgb(139, 0, 0)"  # Dark Red
        ]

        if not self.strings_y_color.get(string):
            self.strings_y_color.update({string: crimson_scale_colors[min(self.indice_color, len(crimson_scale_colors))]})
            self.indice_color = self.indice_color + 1
        return crimson_scale_colors[self.indice_color-1]

    def plot_poligono(self, elemento, color, espesor, transparencia):
        x_borde = []
        y_borde = []
        for segmento in elemento.segmentos_borde:
            x_borde.extend([segmento.nodo_1.x, segmento.nodo_2.x])
            y_borde.extend([segmento.nodo_1.y, segmento.nodo_2.y])
        self.fig.add_trace(go.Scatter(
            x=x_borde, y=y_borde,
            showlegend=False,
            opacity=transparencia,
            line=dict(width=espesor),
            hoverinfo='skip',
            marker=dict(
                size=0.1,
                color=color,
            )))

    def plot_seccion(self, seccion):

        for contorno in seccion.contornos_positivos+seccion.contornos_negativos:
            if contorno.tipo == "Poligonal":
                self.plot_poligono(contorno, color="Cyan", transparencia=1, espesor=4)
            else:
                self.plot_trapecio_circular(contorno,
                                            arc_division=150,
                                            color="Cyan", transparencia=1, espesor=4)

        x_centroide = []
        y_centroide = []
        for elemento in seccion.elementos:
            if elemento.tipo == "Poligonal":
                self.plot_poligono(elemento, color="Cyan", transparencia=0.2, espesor=1)
            else:
                self.plot_trapecio_circular(elemento,
                                            arc_division=100,
                                            color="Cyan",
                                            transparencia=0.2,
                                            espesor=1)

            x_centroide.append(elemento.xg)
            y_centroide.append(elemento.yg)

        self.fig.add_trace(
            go.Scatter(
                dict(x=x_centroide, y=y_centroide, mode="markers", marker=dict(color="Cyan", size=2),
                     hoverinfo='skip',
                     showlegend=False,
                     )))

    @staticmethod
    def generar_color_unico_variantes(input_string):
        # Utiliza hashlib para crear un objeto de hash a partir de la cadena de entrada
        mapeo_de_colores = {
            "BARRA 16mm ADN420": "rgb(220, 20, 60)",  # Crimson
            "BARRA 8mm ADN420": "rgb(255, 165, 0)",  # Orange
            # Agrega más entradas de mapeo según sea necesario
        }

        # Comprueba si la cadena tiene una correspondencia predefinida en el mapeo
        if input_string in mapeo_de_colores:
            return mapeo_de_colores[input_string]

        # Utiliza hashlib para crear un objeto de hash a partir de la cadena de entrada
        objeto_hash = hashlib.sha256(input_string.encode())

        # Convierte el resumen hexadecimal del hash a un número entero
        entero_hash = int(objeto_hash.hexdigest(), 16)

        # Mapea el entero del hash a una gama amplia de tonos de rojo y naranja cercanos al carmesí
        color_value = (entero_hash % 60) + 180  # Ajusta el rango (180-240) según sea necesario

        # Asegura que el valor del color no supere FF (255)
        color_value = min(color_value, 255)

        # Determina la cantidad de rojo y naranja
        red_value = color_value
        orange_value = 255 - color_value

        # Crea un código de color RGB en la forma "rgb(r, g, b)" donde r es el valor de rojo, g es el valor de naranja y b es 0
        color_code = "rgb({}, {}, 0)".format(red_value, orange_value)

        return color_code

    def cargar_barras_como_circulos_para_mostrar_plotly(self, barras_pasivo, barras_activo):
        lista_de_diametros = set()
        shapes_list = []
        x_for_hover_text = []
        y_for_hover_text = []
        text_for_hover_text = []
        for barra in barras_pasivo:
            radio = barra.diametro/20
            acero_y_diamtro_string = f"{barra.tipo} Ø{barra.diametro}mm"
            default_kwargs = dict(type="circle",
                                  xref="x", yref="y",
                                  x0=barra.xg - radio, y0=barra.yg - radio,
                                  x1=barra.xg + radio, y1=barra.yg + radio,
                                  legendgroup="group",
                                  legendgrouptitle_text="ACERO PASIVO",
                                  # legend="legend",
                                  fillcolor=self.colores_random_por_string(acero_y_diamtro_string),
                                  line_color=self.colores_random_por_string(acero_y_diamtro_string),
                                  name=acero_y_diamtro_string,
                                  )
            shapes_list.append(dict(showlegend=acero_y_diamtro_string not in lista_de_diametros, **default_kwargs))
            lista_de_diametros.add(acero_y_diamtro_string)
            x_for_hover_text.append(barra.xg)
            y_for_hover_text.append(barra.yg)
            text_for_hover_text.append(f"x: {barra.xg} cm<br>y: {barra.yg} cm<br>Ø: {barra.diametro} mm")
        for barra in barras_activo:
            radio_equivalente = (barra.area / math.pi) ** 0.5
            acero_y_diamtro_string = f"{barra.tipo}: {barra.area}cm²"
            default_kwargs = dict(type="circle",
                                  xref="x", yref="y",
                                  x0=barra.xg - radio_equivalente, y0=barra.yg - radio_equivalente,
                                  x1=barra.xg + radio_equivalente, y1=barra.yg + radio_equivalente,
                                  legendgroup="group2",
                                  legendgrouptitle_text="ACERO ACTIVO",
                                  fillcolor=self.colores_random_por_string(acero_y_diamtro_string),
                                  line_color=self.colores_random_por_string(acero_y_diamtro_string),
                                  name=acero_y_diamtro_string,
                                  )
            shapes_list.append(dict(showlegend=acero_y_diamtro_string not in lista_de_diametros, **default_kwargs))
            lista_de_diametros.add(acero_y_diamtro_string)
        self.fig.update_layout(shapes=shapes_list)

    @staticmethod
    def plotly_arc(xc, yc, radio, angulo_inicial, angulo_final, arc_division=50, color="Cyan", espesor=1, transparencia=1.00):
        theta = np.linspace(np.radians(angulo_inicial), np.radians(angulo_final), arc_division)
        x = xc + radio * np.cos(theta)
        y = yc + radio * np.sin(theta)

        return go.Scatter(x=x, y=y, mode='lines',
                          line=dict(color=color, width=espesor, dash='solid'),
                          hoverinfo='skip',
                          opacity=transparencia)

    @staticmethod
    def plotly_segmento(nodo1, nodo2, color, espesor, transparencia):
        x = [nodo1.x, nodo2.x]
        y = [nodo1.y, nodo2.y]

        return go.Scatter(x=x, y=y, mode='lines', line=dict(color=color, width=espesor, dash='solid'),
                          hoverinfo='skip',
                          opacity=transparencia)

    def plot_trapecio_circular(self, trapecio_circular, arc_division=100, color="Cyan", espesor=None, mostrar_centroide=False, transparencia=1.00):
        self.fig.add_trace(
            self.plotly_arc(trapecio_circular.xc,
                            trapecio_circular.yc,
                            trapecio_circular.radio_externo,
                            trapecio_circular.angulo_inicial,
                            trapecio_circular.angulo_final,
                            arc_division,
                            color,
                            espesor,
                            transparencia))

        # Plot internal arc if needed
        if trapecio_circular.radio_interno > 0:
            self.fig.add_trace(
                self.plotly_arc(trapecio_circular.xc,
                                trapecio_circular.yc,
                                trapecio_circular.radio_interno,
                                trapecio_circular.angulo_inicial,
                                trapecio_circular.angulo_final,
                                arc_division,
                                color,
                                espesor,
                                transparencia))

        # Plot straight segments
        if trapecio_circular.segmentos_rectos is not None:
            for segmento in trapecio_circular.segmentos_rectos:
                self.fig.add_trace(self.plotly_segmento(segmento.nodo_1, segmento.nodo_2, color, espesor, transparencia))

        # Plot centroid if required
        if mostrar_centroide:
            self.fig.add_trace(
                go.Scatter(x=[trapecio_circular.xg], y=[trapecio_circular.yg], mode='markers',
                           marker=dict(color=color, size=trapecio_circular.area / 300),
                           opacity=transparencia))  # Adjust size as needed

        self.fig.update_layout(showlegend=False)
