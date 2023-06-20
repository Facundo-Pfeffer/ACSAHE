import matplotlib.pyplot as plt
import math
from matplotlib.lines import Line2D


class MatrizAceroPasivo(list):
    def __init__(self):
        super().__init__()

    def cargar_barras_como_circulos_para_mostrar(self, ax):
        lista_de_diametros = set()
        for barra in self:
            lista_de_diametros.add(barra.diametro)
            circ = plt.Circle(xy=(barra.xg, barra.yg), radius=barra.diametro / 20, color='r', zorder=21)
            ax.add_patch(circ)
        for diametro in lista_de_diametros:
            legenda = Line2D([-10], [-10], marker='o', color='w', label=f"Armadura Pasiva Ø{diametro}mm",
                             markerfacecolor='r', markersize=diametro/2),
            plt.legend(handles=legenda)
        return ax


class MatrizAceroActivo(list):
    def __init__(self):
        super().__init__()

    def cargar_barras_como_circulos_para_mostrar(self, ax):
        lista_de_areas = set()
        for barra in self:
            lista_de_areas.add(barra.area)
            radio_equivalente = (barra.area / math.pi) ** 0.5
            circ = plt.Circle(xy=(barra.xg, barra.yg), radius=radio_equivalente, color='b', zorder=20)
            ax.add_patch(circ)
        for area in lista_de_areas:
            radio = (area / math.pi) ** 0.5
            legenda = Line2D([0], [0], marker='o', color='w', label=f"Armadura Activa A={area}cm²",
                             markerfacecolor='b', markersize=radio * 10),
            plt.legend(handles=legenda)
