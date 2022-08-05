from excel_manager import ExcelManager
from acero_pretensado import AceroPretensado
from acero_pasivo import AceroPasivo
from hormigon import Hormigon
from geometria import Nodo, Contorno
import math
import matplotlib.pyplot as plt
from scipy.optimize import fsolve


class FindInitialDeformation:
    def __init__(self, def_de_pretensado_inicial):
        self.def_de_pretensado_inicial = def_de_pretensado_inicial
        self.excel_wb = ExcelManager("DISGHA Prueba SECCIONES.xlsm")
        self.acero_pasivo = AceroPasivo(self.excel_wb.get_value("C", "5"))
        self.acero_pretensado = AceroPretensado(tipo=self.excel_wb.get_value("C", "7"))
        self.hormigon = Hormigon(tipo=self.excel_wb.get_value("C", "3"))

        self.EEH = self.obtener_matriz_hormigon()
        self.EA = self.obtener_matriz_acero_pasivo()
        self.EAP = self.obtener_matriz_acero_pretensado()


        self.XG = 0
        self.YG = 0

        result = fsolve(self.function_to_miminize, [0,0,0])
        self.print_result_unidimensional(result)
        # self.print_result_tridimensional(result)

    def obtener_matriz_acero_pasivo(self):
        rows = list(range(27, 31))
        resultado = []
        for row in rows:
            x_y_d = self.excel_wb.get_value("C", row), self.excel_wb.get_value("E", row), math.pi*(self.excel_wb.get_value("G", row)/2000)**2
            resultado.append(x_y_d)
        return resultado

    def obtener_matriz_acero_pretensado(self):
        rows = list(range(36, 40))
        resultado = []
        for row in rows:
            x_y_d = self.excel_wb.get_value("C", row), self.excel_wb.get_value("E", row), math.pi*(self.excel_wb.get_value("G", row)/2000)**2
            resultado.append(x_y_d)
        return resultado

    def get_signo(self, contorno):
        value = self.excel_wb.get_value("D", contorno[0])
        return +1 if "Pos" in value else -1

    def obtener_matriz_hormigon(self):
        filas_hormigon = self.excel_wb.get_rows_range_between_values(("GEOMETRÍA DE LA SECCIÓN DE HORMIGÓN", "ARMADURAS"))
        lista_filas_contornos = self.excel_wb.subdivide_range_in_filled_ranges("B", filas_hormigon)
        contornos = {}
        coordenadas_nodos = []
        for i, filas_contorno in enumerate(lista_filas_contornos):
            signo = self.get_signo(filas_contorno)
            for fila_n in filas_contorno[3:]: #TODO mejorar
                x = self.excel_wb.get_value("C", fila_n)
                y = self.excel_wb.get_value("E", fila_n)
                coordenadas_nodos.append(Nodo(x, y))
            contornos[str(i+1)] = Contorno(coordenadas_nodos, signo)
            coordenadas_nodos = []
        print(contornos)
        EEH = []
        dx, dy = self.get_discretización()
        for indice_contorno, contorno in contornos.items():
            discretizacion = contorno.discretizar_contorno_como_rectangulo(dx=dx, dy=dy)
            EEH = EEH + discretizacion
            contorno.mostrar_contorno_y_discretizacion(discretizacion)
        return EEH

    def get_discretización(self):
        rows_range = self.excel_wb.get_n_rows_after_value("DISCRETIZACIÓN DE LA SECCIÓN", 5, rows_range=range(40, 300))
        dx = self.excel_wb.get_value_on_the_right("ΔX =", rows_range)
        dy = self.excel_wb.get_value_on_the_right("ΔY =", rows_range)
        return dx, dy



            # filas_coordenadas
        # contornos = [x for x in self.excel_wb.get_rows_range_between_values((x, x+1), column_letter="B", rows_range=filas_hormigon)
        #              for x in range()]
        #
        # rows = list(range(18, 22))
        # extremos = []
        # for row in rows:
        #     x_y = self.excel_wb.get_value("C", row), self.excel_wb.get_value("E", row)
        #     extremos.append(x_y)
        # dx = self.excel_wb.get_value("C", 43)
        # dy = self.excel_wb.get_value("C", 45)
        # min_x = min([c[0] for c in extremos])
        # min_y = min([c[1] for c in extremos])
        # max_x = max([c[1] for c in extremos])
        # max_y = max([c[1] for c in extremos])
        # EEH = []
        # x_to_sum = dx / 2
        # y_to_sum = dy / 2
        # for i in range(math.floor((max_x-min_x)/dx)):
        #     for j in range(math.floor((max_y-min_y)/dy)):
        #         EEH.append((min_x + x_to_sum, min_y + y_to_sum, dx*dy))
        #         y_to_sum = y_to_sum + dy
        #     y_to_sum = dy / 2
        #     x_to_sum = x_to_sum + dx
        return EEH

    def function_to_miminize(self, c):
        (ec, phix, phiy) = c
        return self.calcular_sumatoria_de_fuerzas(ec, phix, phiy)

    def calcular_sumatoria_de_fuerzas(self, ec, phix, phiy):
        ec_plano = lambda x, y: ec/100000+math.tan(math.radians(phix/1000))*y+math.tan(math.radians(phiy/1000)*x) # Ecuacion del plano
        sumF = 0
        Mx = 0
        My = 0
        EA = self.EA
        EAP = self.EAP
        EEH = self.EEH
        for barra in EA:
            x, y, e, A = barra[0], barra[1], ec_plano(barra[0], barra[1]), barra[2]
            F = -self.acero_pasivo.relacion_constitutiva(e) * A
            sumF = sumF + F
            Mx = F * y + Mx
            My = -F * x + My
        for barra_p in EAP:
            x,y,e,A = barra_p[0], barra_p[1], ec_plano(barra_p[0], barra_p[1]), barra_p[2]
            F = (self.acero_pretensado.relacion_constitutiva(-e+self.def_de_pretensado_inicial)) * A
            sumF = sumF + F
            Mx = F * y + Mx
            My = -F * x + My
        for elemento in EEH:
            x,y,e,A =elemento[0], elemento[1], ec_plano(elemento[0], elemento[1]), elemento[2]
            F = -(self.hormigon.relacion_constitutiva(e)) * A
            sumF = sumF + F
            Mx = F * y + Mx
            My = -F * x + My
        return [sumF, Mx, My]

    def iterate(self):
        ec_range = range(200)
        px_range = range(500)
        py_range = range(500)
        min_result_sum = 100000
        min_r = None
        min_p = None
        for ec_v in ec_range:
            for px_v in px_range:
                for py_v in py_range:
                    result = self.function_to_miminize((ec_v, px_v/100, py_v/100))
                    if abs(sum(result)) < abs(min_result_sum):
                        min_result_sum = sum(result)
                        min_r = result
                        min_p = (ec_v, px_v, py_v)
        print(f'\n{min_r} {min_p}\n')
        return min_p

    def print_result_unidimensional(self, result):
        ec, phix, phiy = result
        ec_plano = lambda x, y: ec / 100000 + math.tan(math.radians(phix / 1000)) * y + math.tan(
            math.radians(phiy / 1000) * x)
        y = [n/100 for n in range(-100, 100)]
        z = [ec_plano(0, n) for n in y]
        z_i = [0 for n in y]
        plt.scatter(z, y, color="r", s=3, label="")
        plt.scatter(z_i, y, color="b", s=3, label="")
        plt.show()

    # def print_result_tridimensional(self, result):
    #     ec, phix, phiy = result
    #     ec_plano = lambda x, y: ec / 100000 + math.tan(math.radians(phix / 1000)) * y + math.tan(
    #         math.radians(phiy / 1000) * x)
    #     x = [n/100 for n in range(-100, 100)]
    #     y = [n/100 for n in range(-100, 100)]
    #     plot = []
    #     for i in range(100):
    #         for j in range(100):
    #             plot.append((x[i], y[j], ec_plano(x[i], y[j]))
    #
    #     ax = plt.axes(projection='3d')
    #     plt.scatter(z, y, color="r", s=3, label="")
    #     plt.scatter(z_i, y, color="b", s=3, label="")
    #     plt.show()


resolver = FindInitialDeformation(500/100000)






