

class Hormigon:
    B1 = None

    def __init__(self, tipo):
        self.fc = tipo
        self.E = 4700 * (int(tipo)**0.5)
        self.B1 = self.obtener_beta_1()

    def relacion_constitutiva_simplificada(self, deformacion, e_max_comp):
        """e_max: deformaciopn máxima en valor absoluto del hormigón, generalmente 3 por mil.
        Se recuerda que las deformaciones negativas corresponden a una fibra comprimida."""
        def_max = (1 - self.B1) * e_max_comp
        if deformacion > def_max:  # Recordar signo de deformación, implica menos negativo
            return 0
        else:
            return -0.85*self.fc*1000



    def relacion_constitutiva(self, e):
        return self.E*e if e > 0 else 0

    def obtener_beta_1(self):
        if self.fc > 30:
            return 0.85-0.05*(self.fc-30)/7
        return 0.85
