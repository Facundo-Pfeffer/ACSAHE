class Hormigon:
    B1 = None

    def __init__(self, tipo):
        self.fc = tipo
        self.E = 470 * (int(tipo)**0.5)  # kN/cm²
        self.B1 = self.obtener_beta_1()

    def relacion_constitutiva_simplificada(self, e, e_max_comp):
        """
        Obtiene la tensión (en kN/cm²) utilizando las hipótesis planteadas en el apartado 10.2 del CIRSOC 201 (2005).
        Se recuerda que las deformaciones negativas corresponden a una fibra comprimida.

        Variables:
        :param e: deformación de la fibra a analizarse.
        :param e_max_comp: deformación de la fibra más comprimida de la sección.
        """
        e_lim = (1 - self.B1) * e_max_comp  # Deformación a partir de la cual estamos fuera del bloque de tensiones.
        if e > e_lim:  # = e menos comprimido que e_lim (recordar signo).
            return 0
        else:
            return -0.85*self.fc/10  # kN/cm²

    def relacion_constitutiva_elastica(self, e):
        """
        Obtiene la tensión (en kN/cm²) suponiendo un comportamiento puramente elástico del hormigón (ley de Hooke).
        No se considera la contribución a la tracción del hormigón para esta relación.
        """
        return self.E*e if e < 0 else 0  # kN/cm²

    def obtener_beta_1(self):
        """
        Obtiene el valor de ß1, el cual determina la relación entre la profundidad del eje neutro y la del bloque
        de tensiones. Refiérase al apartado 10.2.7.3 del CIRSOC 201 (2005).
        :return:
        """
        if self.fc > 30:
            return 0.85-0.05*(self.fc-30)/7
        return 0.85
