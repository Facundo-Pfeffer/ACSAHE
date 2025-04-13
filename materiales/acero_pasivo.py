import matplotlib.pyplot as plt
import math
from functools import lru_cache


class BarraAceroPasivo():
    tipos_de_acero_y_valores = {"ADN 420": {"fy": 420}, "ADN 500": {"fy": 500}, "AL 220": {"fy": 220}}
    E = None
    fy = None
    ey = None
    eu = None

    def __init__(self, x, y, d, identificador):
        """IMPORTANTE
        Antes de inicializar una instancia de esta clase, los valores de fy [tensión de fluencia del acero] y
        E [módulo de elasticidad del material] deben ser inicializados."""
        try:
            self.identificador = int(identificador)
        except Exception:
            self.identificador = identificador
        self.ey = self.fy/self.E
        self.x = x
        self.xg = x
        self.y = y
        self.yg = y
        self.diametro = d  # mm
        self.area = math.pi*(d/20)**2  # cm²
        self.y_girado = None

    @lru_cache(maxsize=512)
    def relacion_constitutiva(self, e):
        """Relación bilineal."""
        if abs(e) > self.ey:
            sign = +1 if e >= 0 else -1
            return self.fy * sign / 10  # kN/cm²
        else:
            return self.E * e / 10  # kN/cm²

    def mostrar_relacion_constitutiva(self):
        particion_e = range(-1000, 1000)
        x = []
        y = []
        for x_v in particion_e:
            x.append(x_v/100000)
            y.append(self.relacion_constitutiva(x_v/100000))
        plt.scatter(x, y, color="r", s=3, label="")
        plt.show()