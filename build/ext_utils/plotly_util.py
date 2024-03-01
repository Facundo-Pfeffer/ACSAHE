import plotly.graph_objects as go
from plotly.graph_objs.scatter.legendgrouptitle import Font
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
        fig = go.Figure(layout_template="plotly_white")
        fig.update_yaxes(
            scaleanchor="x",
            scaleratio=1,
        )
        return fig

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

    def plot_seccion(self, seccion, lista_de_angulos_plano_de_carga):

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

        self.plot_angulos_planos_de_carga_y_ejes(seccion, lista_de_angulos_plano_de_carga)


    def plot_angulos_planos_de_carga_y_ejes(self, seccion, lista_ang_planos_de_carga):
        lista_ang_planos_de_carga.sort()
        xmin, xmax, ymin, ymax = seccion.x_min, seccion.x_max, seccion.y_min, seccion.y_max

        line_styles = ['solid', 'dash', 'dot', 'dashdot']
        line_colors = ['grey', 'black']

        # Adjust limits to include a margin
        margin = 0.05  # 5% of each axis range
        xmin_margin = xmin - (xmax - xmin) * margin
        xmax_margin = xmax + (xmax - xmin) * margin
        ymin_margin = ymin - (ymax - ymin) * margin
        ymax_margin = ymax + (ymax - ymin) * margin

        for i, angulo in enumerate(lista_ang_planos_de_carga):

            angulo_rad = np.radians(angulo)
            x_intersect_min = xmin_margin
            x_intersect_max = xmax_margin
            if angulo != 0:
                m = np.tan(np.pi / 2 - angulo_rad)  # Slope of the line
                y_at_xmin_margin = m * xmin_margin
                y_at_xmax_margin = m * xmax_margin
                x_at_ymin_margin = ymin_margin / m if m != 0 else float('inf')  # Check for division by zero
                x_at_ymax_margin = ymax_margin / m if m != 0 else float('inf')
                puntos = []
                if ymin_margin <= y_at_xmin_margin <= ymax_margin:
                    puntos.append((xmin_margin, y_at_xmin_margin))
                if ymin_margin <= y_at_xmax_margin <= ymax_margin:
                    puntos.append((xmax_margin, y_at_xmax_margin))
                if xmin_margin <= x_at_ymin_margin <= xmax_margin:
                    puntos.append((x_at_ymin_margin, ymin_margin))
                if xmin_margin <= x_at_ymax_margin <= xmax_margin:
                    puntos.append((x_at_ymax_margin, ymax_margin))
            else:
                puntos = [(0, ymin_margin), (0, ymax_margin)]

            # Choose line style based on index, cycling through the list of styles
            line_style = line_styles[i % len(line_styles)]
            line_color = line_colors[i // len(line_styles) % len(line_colors)]

            # Add line to the figure
            x_puntos, y_puntos = zip(*puntos)
            self.fig.add_trace(go.Scatter(x=x_puntos, y=y_puntos, mode='lines',
                                          line=dict(color=line_color, width=3, dash=line_style),
                                          visible=True,
                                          legendgroup="group0",
                                          legendgrouptitle={"text": "PLANOS DE CARGA"},
                                          name=f"λ: {angulo}°"))


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

    def colores_random_por_string(self, string):
        crimson_scale_colors = [
            "rgb(255, 0, 0)",  # Pure Red
            "rgb(241, 196, 15)",  # Gold: Stands out against cyan, less harsh than pure yellow
            "rgb(46, 204, 113)",  # Emerald
            "rgb(0, 0, 255)",  # Blue
            "rgb(255, 0, 255)",  # Magenta
            "rgb(255, 140, 0)",  # Dark Orange
            "rgb(0, 255, 255)",  # Cyan
            "rgb(128, 0, 128)",  # Purple
            "rgb(255, 165, 0)",  # Orange,
            "rgb(139, 0, 0)",  # Dark Red

        ]

        if string not in self.strings_y_color:
            color = crimson_scale_colors[self.indice_color % len(crimson_scale_colors)]
            self.strings_y_color[string] = color
            # Incrementamos el índice para la próxima asignación
            self.indice_color += 1
        return self.strings_y_color[string]

    def cargar_barras_como_circulos_para_mostrar_plotly(self, barras_pasivo, barras_activo):
        lista_de_diametros = set()
        shapes_list = []
        x_for_hover_text = []
        y_for_hover_text = []
        text_for_hover_text = []
        color = []
        for barra in barras_pasivo + barras_activo:  # Combine for simplicity
            # Determine if it's pasivo or activo based on the type of 'barra'
            tipo = "ACERO PASIVO" if barra in barras_pasivo else "ACERO ACTIVO"
            if barra in barras_pasivo:
                radio = barra.diametro / 20
                acero_y_diamtro_string = f"{barra.tipo}<br>Ø{barra.diametro}mm"
                hover_text = f"<b>Barra {barra.identificador}</b><br>x: {barra.xg} cm<br>y: {barra.yg} cm<br>Tipo: {barra.tipo}<br>Ø{barra.diametro}mm"

            else:
                radio = (barra.area / math.pi) ** 0.5  # Equivalente
                acero_y_diamtro_string = f"{barra.tipo}: {barra.area}cm²"
                hover_text = f"<b>Barra {barra.identificador}</b><br>x: {barra.xg} cm<br>y: {barra.yg} cm<br>Tipo: {barra.tipo}<br>Área efectiva: {barra.area}cm²"

            # Add shapes for circles
            shapes_list.append(dict(
                type="circle",
                xref="x", yref="y",
                x0=barra.xg - radio, y0=barra.yg - radio,
                x1=barra.xg + radio, y1=barra.yg + radio,
                fillcolor=self.colores_random_por_string(acero_y_diamtro_string),
                line_color=self.colores_random_por_string(acero_y_diamtro_string),
                legendgroup=f"group{1 if tipo=='ACERO PASIVO' else 2}",
                legendgrouptitle_text=tipo,
                name=acero_y_diamtro_string,
                showlegend=acero_y_diamtro_string not in lista_de_diametros
            ))
            lista_de_diametros.add(acero_y_diamtro_string)

            # Prepare hover text data
            x_for_hover_text.append(barra.xg)
            y_for_hover_text.append(barra.yg)
            text_for_hover_text.append(hover_text)
            color.append(self.colores_random_por_string(acero_y_diamtro_string))

        self.fig.update_layout(shapes=shapes_list)

        self.fig.add_trace(go.Scatter(
            x=x_for_hover_text,
            y=y_for_hover_text,
            mode='markers',
            marker=dict(size=0),
            hoverinfo='text',
            text=text_for_hover_text,
            showlegend=False,
            hoverlabel=dict(bgcolor=color),
        ))

    @staticmethod
    def plotly_arc(xc, yc, radio, angulo_inicial, angulo_final, arc_division=50, color="Cyan", espesor=1, transparencia=1.00):
        theta = np.linspace(np.radians(angulo_inicial), np.radians(angulo_final), arc_division)
        x = xc + radio * np.cos(theta)
        y = yc + radio * np.sin(theta)

        return go.Scatter(x=x, y=y, mode='lines',
                          line=dict(color=color, width=espesor, dash='solid'),
                          hoverinfo='skip',
                          showlegend=False,
                          opacity=transparencia)

    @staticmethod
    def plotly_segmento(nodo1, nodo2, color, espesor, transparencia, **kwargs):
        x = [nodo1.x, nodo2.x]
        y = [nodo1.y, nodo2.y]

        return go.Scatter(x=x, y=y, mode='lines', line=dict(color=color, width=espesor, dash='solid'),
                          hoverinfo='skip',
                          opacity=transparencia,
                          **kwargs)

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

        # Plotear el arco interno (si hay)
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

        # Segmentos rectos
        if trapecio_circular.segmentos_rectos is not None:
            for segmento in trapecio_circular.segmentos_rectos:
                self.fig.add_trace(self.plotly_segmento(
                    segmento.nodo_1, segmento.nodo_2, color, espesor, transparencia, showlegend=False))

        # Centroide de los elementos
        if mostrar_centroide:
            self.fig.add_trace(
                go.Scatter(x=[trapecio_circular.xg], y=[trapecio_circular.yg], mode='markers',
                           marker=dict(color=color, size=trapecio_circular.area / 300),
                           opacity=transparencia, showlegend=False))  # Adjust size as needed

        self.fig.update_layout(showlegend=True)
