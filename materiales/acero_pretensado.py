import matplotlib.pyplot as plt
from functools import lru_cache
import math


class BarraAceroPretensado():
    tipos_de_acero_y_valores = {
        "BARRAS 1050":
            {
                "fpu": 1050/10,  # kN/cm²
                "fpy": 952/10,  # kN/cm²
                "epu": 0.041,
                "N": 7.1,
                "K": 1.0041,
                "Q": 0.0175
            },
        "TRENZAS C1650":
            {
                "fpu": 1650/10,  # kN/cm²
                "fpy": 1505/10,  # kN/cm²
                "epu": 0.087,
                "N": 6.060,
                "K": 1.0325,
                "Q": 0.00625
            },
        "TRENZAS C1900":
            {
                "fpu": 1860/10,  # kN/cm²
                "fpy": 1665/10,  # kN/cm²
                "epu": 0.069,
                "N": 7.344,
                "K": 1.0618,
                "Q": 0.01174
            }
    }
    fpu = None
    fpy = None
    epu = None
    N = None
    K = None
    Q = None
    Eps = None
    deformacion_de_pretensado_inicial = 0.00

    def __init__(self, x, y, area, identificador):
        try:
            self.identificador = int(identificador)
        except Exception:
            self.identificador = identificador
        self.x = x
        self.xg = x
        self.y = y
        self.yg = y
        self.area = area
        self.y_girado = None
        self.x_girado = None
        self.def_elastica_hormigon_perdidas = None

    @lru_cache(maxsize=512)
    def relacion_constitutiva(self, e):
        """Relación constitutiva propuesta por Menegotto y Pinto, se recomienda que este método sea sobrescrito
        con la relación constitutiva que quiera utilizarse para el acero de pretensado, como la del fabricante."""
        return self.Eps * e * (self.Q + (1-self.Q)/((1+(self.Eps*abs(e)/(self.K*self.fpy))**(self.N))**(1/self.N)))  #  kN/cm²

    def mostrar_relacion_constitutiva(self):
        particion_e = range(1100)
        x = []
        y = []
        min_delta = 8000
        for x_v in particion_e:
            x.append(x_v/100000)
            y_v = self.relacion_constitutiva(x_v/100000)
            if abs(y_v - 1000) < abs(min_delta):
                min_delta = y_v - 1000
            y.append(y_v)
        plt.scatter(x, y, color="r", s=3, label="")
        plt.show()


