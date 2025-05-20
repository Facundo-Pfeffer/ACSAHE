import math
import plotly.graph_objects as go


class BarraAceroPasivo():
    default_strain_stress_relation_vars = {"ADN 420": {"fy": 420}, "ADN 500": {"fy": 500}, "AL 220": {"fy": 220}}
    E = None
    fy = None
    ey = None
    eu = None

    def __init__(self, x, y, d, identificador):
        """
        IMPORTANT
        Before initializing an instance of this class, the values of fy [steel yield stress] and
        E [modulus of elasticity of the material] must be set.
        """
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

    def stress_strain_eq(self, e):
        """Relación bilineal."""
        if abs(e) > self.ey:
            sign = +1 if e >= 0 else -1
            return self.fy * sign  # kN/cm²
        else:
            return self.E * e  # kN/cm²

    def show_stress_strain_curve(self):
        particion_e = range(-1000, 1000)
        x = [e / 100000 for e in particion_e]
        y = [self.stress_strain_eq(e_val) for e_val in x]

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
