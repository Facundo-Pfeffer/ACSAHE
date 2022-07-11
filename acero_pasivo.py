import matplotlib.pyplot as plt


class AceroPasivo():

    def __init__(self, tipo):
        self.fy = None
        self.E = 200000
        tipos_de_acero_y_valores = {
            "ADN 420":
                {
                    "fy": 420
                },
            "ADN 500":
                {
                    "fy": 500
                },
            "ADN 220":
                {
                    "fy": 220
                }
        }

        self.fy = tipos_de_acero_y_valores.get(tipo.upper())["fy"]
        self.ey = self.fy/self.E

    def relacion_constitutiva(self, e):
        if abs(e) > self.ey:
            sign = +1 if e>=0 else -1
            return self.fy * sign
        else:
            return self.E * e

    def mostrar_relacion_constitutiva(self):
        particion_e = range(-1000, 1000)
        x = []
        y = []
        for x_v in particion_e:
            x.append(x_v/100000)
            y.append(self.relacion_constitutiva(x_v/100000))
        plt.scatter(x, y, color="r", s=3, label="")
        plt.show()