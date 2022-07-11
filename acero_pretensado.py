import matplotlib.pyplot as plt
import numpy as np

class AceroPretensado():

    def __init__(self, tipo):
        self.fpu = None
        self.fpy = None
        self.epu = None
        self.N = None
        self.K = None
        self.Q = None
        self.Eps = 200000

        tipos_de_acero_y_valores = {
            "BARRAS 1050":
                {
                    "fpu": 1050,
                    "fpy": 952,
                    "epu": 0.041,
                    "N": 7.1,
                    "K": 1.0041,
                    "Q": 0.0175
                },
            "TRENZAS C1650":
                {
                    "fpu": 1650,
                    "fpy": 1505,
                    "epu": 0.087,
                    "N": 6.060,
                    "K": 1.0325,
                    "Q": 0.00625
                },
            "TRENZAS C1900":
                {
                    "fpu": 1860,
                    "fpy": 1665,
                    "epu": 0.069,
                    "N": 7.344,
                    "K": 1.0618,
                    "Q": 0.01174
                }
        }

        tipo = tipo.upper()
        values = tipos_de_acero_y_valores.get(tipo)
        for k, v in values.items():
            self.__setattr__(k, v)

    def relacion_constitutiva(self, e):
        return self.Eps * e * (self.Q + (1-self.Q)/((1+(self.Eps*e/(self.K*self.fpy))**(self.N))**(1/self.N)))

    def mostrar_relacion_constitutiva(self):
        particion_e = range(1100)
        x = []
        y = []
        min_delta = 8000
        min_x = None
        for x_v in particion_e:
            x.append(x_v/100000)
            y_v = self.relacion_constitutiva(x_v/100000)
            if abs(y_v - 1000) < abs(min_delta):
                min_delta = y_v - 1000
                min_x = x_v
            y.append(y_v)
        plt.scatter(x, y, color="r", s=3, label="")
        plt.show()


