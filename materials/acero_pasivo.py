import math
from functools import lru_cache
import plotly.graph_objects as go


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
        x = [e / 100000 for e in particion_e]
        y = [self.relacion_constitutiva(e_val) for e_val in x]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=x,
            y=y,
            mode='markers',
            marker=dict(color='red', size=3),
            showlegend=False
        ))
        fig.update_layout(
            title="Relación Constitutiva",
            xaxis_title="Deformación",
            yaxis_title="Tensión",
        )
        fig.show()
