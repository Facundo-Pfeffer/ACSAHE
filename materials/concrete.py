class Concrete:
    B1 = None

    def __init__(self, tipo):
        self.fc = tipo
        self.E = 470 * (int(tipo)**0.5)  # kN/cm²
        self.B1 = self.obtener_beta_1()

    def simplified_stress_strain_eq(self, e, e_max_comp):
        """
        Returns the stress (in kN/cm²) based on the assumptions established in Section 10.2 of CIRSOC 201 (2005).
        Note that negative strains correspond to compressed fibers.

        Parameters:
        :param e: strain of the fiber being analyzed.
        :param e_max_comp: strain of the most compressed fiber in the section.
        """
        e_lim = (1 - self.B1) * e_max_comp  # Deformación a partir de la cual estamos fuera del bloque de tensiones.
        if e > e_lim:  # = e menos comprimido que e_lim (recordar sign).
            return 0
        else:
            return -0.85*self.fc/10  # kN/cm²

    def elastic_stress_strain_eq(self, e):
        """
        Returns the stress (in kN/cm²) assuming purely elastic behavior of the concrete (Hooke's law).
        The tensile contribution of the concrete is not considered in this relation.
        """
        return self.E*e if e < 0 else 0  # kN/cm²

    def obtener_beta_1(self):
        """
        Returns the value of ß1, which defines the relationship between the depth of the neutral axis
        and that of the stress block. Refer to Section 10.2.7.3 of CIRSOC 201 (2005).
        :return:
        """
        if self.fc > 30:
            return 0.85-0.05*(self.fc-30)/7
        return 0.85
