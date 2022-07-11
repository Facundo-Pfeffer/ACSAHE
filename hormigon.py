

class Hormigon:

    def __init__(self, tipo):
        self.E = 4700 * (int(tipo)**0.5)

    def relacion_constitutiva(self, e):
        return self.E*e if e > 0 else 0