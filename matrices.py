import matplotlib.pyplot as plt
import math
import plotly
from plotly_util import PlotlyUtil
import plotly.graph_objs as go
from matplotlib.lines import Line2D


class MatrizAceroPasivo(list):
    def __init__(self):
        super().__init__()

    def cargar_barras_como_circulos_para_mostrar_plotly(self, fig):
        plotly_util = PlotlyUtil()
        lista_de_diametros = set()
        shapes_list = []
        for barra in self:
            radio = barra.diametro/20
            acero_y_diamtro_string = f"{barra.tipo} Ø{barra.diametro}mm"
            default_kwargs = dict(type="circle",
                                  xref="x", yref="y",
                                  x0=barra.xg - radio, y0=barra.yg - radio,
                                  x1=barra.xg + radio, y1=barra.yg + radio,
                                  legend="legend",
                                  fillcolor=plotly_util.colores_random_por_string(acero_y_diamtro_string),
                                  line_color=plotly_util.colores_random_por_string(acero_y_diamtro_string),
                                  name=acero_y_diamtro_string,
                                  )
            shapes_list.append(dict(showlegend=acero_y_diamtro_string not in lista_de_diametros, **default_kwargs))
            lista_de_diametros.add(acero_y_diamtro_string)
        fig.update_layout(shapes=shapes_list, legend = {
            "title": "ACERO PASIVO",
            "xref": "container",
            "yref": "container",
            "y": 0.85,
            "groupclick": "toggleitem"},showlegend="true")

    def cargar_barras_como_circulos_para_mostrar(self, ax):
        lista_de_diametros = set()
        for barra in self:
            lista_de_diametros.add(barra.diametro)
            circ = plt.Circle(xy=(barra.xg, barra.yg), radius=barra.diametro / 20, color='r', zorder=21)
            ax.add_patch(circ)
        return ax


class MatrizAceroActivo(list):
    def __init__(self):
        super().__init__()

    def cargar_barras_como_circulos_para_mostrar_plotly(self, fig):

        plotly_util = PlotlyUtil(indice_color=3)
        lista_de_diametros = set()
        shapes_list = []
        for barra in self:
            radio_equivalente = (barra.area / math.pi) ** 0.5
            acero_y_diamtro_string = f"{barra.tipo}: {barra.area}cm²"
            default_kwargs = dict(type="circle",
                                  xref="x", yref="y",
                                  x0=barra.xg - radio_equivalente, y0=barra.yg - radio_equivalente,
                                  x1=barra.xg + radio_equivalente, y1=barra.yg + radio_equivalente,
                                  fillcolor=plotly_util.colores_random_por_string(acero_y_diamtro_string),
                                  # legendgroup=acero_y_diamtro_string,
                                  line_color=plotly_util.colores_random_por_string(acero_y_diamtro_string),
                                  name=acero_y_diamtro_string,
                                  legend="legend2"
                                  )
            shapes_list.append(dict(showlegend=acero_y_diamtro_string not in lista_de_diametros, **default_kwargs))
            lista_de_diametros.add(acero_y_diamtro_string)
        fig.update_layout(shapes=shapes_list)
        fig.update_layout(
            legend2={
            "title": "Acero Activo",
            "xref": "container",
            "yref": "container",
            "y": 0.45,
            "groupclick": "toggleitem"})

    def cargar_barras_como_circulos_para_mostrar(self, ax):
        lista_de_areas = set()
        for barra in self:
            lista_de_areas.add(barra.area)
            radio_equivalente = (barra.area / math.pi) ** 0.5
            circ = plt.Circle(xy=(barra.xg, barra.yg), radius=radio_equivalente, color='b', zorder=20)
            ax.add_patch(circ)
