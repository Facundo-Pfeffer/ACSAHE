from acero_pasivo import BarraAceroPasivo
import matplotlib.pyplot as plt

class MatrizAceroPasivo(list):
    def __init__(self):
        super().__init__()

    def cargar_barras_como_circulos_para_mostrar(self):
        fig, ax = plt.subplots()
        for barra in self:
            circ = plt.Circle(xy=(barra.xg, barra.yg), radius=barra.diametro/2000, color='r')
            ax.add_patch(circ)
