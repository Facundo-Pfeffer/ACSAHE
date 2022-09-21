from excel_manager import ExcelManager
from acero_pretensado import AceroPretensado
from acero_pasivo import AceroPasivo
from hormigon import Hormigon
from geometria import Nodo, Contorno, Recta, SeccionGenerica
import math
import matplotlib.pyplot as plt
from scipy.optimize import fsolve


class FindInitialDeformation:
    def __init__(self, def_de_pretensado_inicial):
        self.def_de_pretensado_inicial = def_de_pretensado_inicial
        self.excel_wb = ExcelManager("DISGHA Prueba SECCIONES CAJON 1.xlsm")
        # self.planos_de_deformación = self.obtener_planos_de_deformacion()
        self.acero_pasivo = AceroPasivo(self.excel_wb.get_value("C", "5"))
        self.acero_pretensado = AceroPretensado(tipo=self.excel_wb.get_value("C", "7"))
        self.hormigon = Hormigon(tipo=self.excel_wb.get_value("C", "3"))

        self.seccion_H = self.obtener_matriz_hormigon()
        self.EEH = self.seccion_H.elementos
        self.XG = self.seccion_H.xg, self.YG = self.seccion_H.yg

        self.EA = self.obtener_matriz_acero_pasivo()
        self.EAP = self.obtener_matriz_acero_pretensado()

        result = fsolve(self.function_to_miminize, [0, 0, 0])
        self.print_result_unidimensional(result)
        # self.print_result_tridimensional(result)

    @staticmethod
    def obtener_planos_de_deformacion():
        y = 1
        result = []
        for j in range(195):
            if j <= 130:
                punto_1 = Nodo(-3, y)
                punto_2 = Nodo(-3 + 0.1*j, -y)
            elif j>130 and j<=180:
                punto_1 = Nodo(-3, y)
                punto_2 = Nodo(10 + (j-130), -y)
            else:
                punto_1 = Nodo(-3+(j-180)*0.3, y)
                punto_2 = Nodo(60, -y)
            recta = Recta(punto_1, punto_2)
            recta.mostrar_recta()
            result.append(recta)
        # plt.show()
        return result

    def obtener_matriz_acero_pasivo(self):
        rows = self.excel_wb.get_rows_range_between_values(("ARMADURAS", "ARMADURAS PRETENSADAS"))
        resultado = []
        for row in rows:
            x_y_d = self.excel_wb.get_value("C", row), self.excel_wb.get_value("E", row), math.pi*(self.excel_wb.get_value("G", row)/2000)**2
            resultado.append(x_y_d)
        return resultado

    def obtener_matriz_acero_pretensado(self):
        rows = self.excel_wb.get_rows_range_between_values(("ARMADURAS PRETENSADAS", "DISCRETIZACIÓN DE LA SECCIÓN"))
        resultado = []
        for row in rows:
            x_y_d = self.excel_wb.get_value("C", row), self.excel_wb.get_value("E", row), math.pi*(self.excel_wb.get_value("G", row)/2000)**2
            resultado.append(x_y_d)
        return resultado

    def get_signo(self, contorno):  #TODO mejorar
        value = self.excel_wb.get_value("D", contorno[0])
        return +1 if "Pos" in value else -1

    def get_cantidad_de_nodos(self, contorno): #TODO mejorar
        return self.excel_wb.get_value("G", contorno[0])

    def obtener_matriz_hormigon(self):
        filas_hormigon = self.excel_wb.get_rows_range_between_values(("GEOMETRÍA DE LA SECCIÓN DE HORMIGÓN", "ARMADURAS"))
        lista_filas_contornos = self.excel_wb.subdivide_range_in_filled_ranges("B", filas_hormigon)
        contornos = {}
        coordenadas_nodos = []
        for i, filas_contorno in enumerate(lista_filas_contornos):
            signo = self.get_signo(filas_contorno)
            cantidad_de_nodos = self.get_cantidad_de_nodos(filas_contorno)
            for fila_n in self.excel_wb.get_n_rows_after_value("Nodo nº", cantidad_de_nodos+1, rows_range=filas_contorno)[1:]:
                x = self.excel_wb.get_value("C", fila_n)
                y = self.excel_wb.get_value("E", fila_n)
                coordenadas_nodos.append(Nodo(x, y))
            contornos[str(i+1)] = Contorno(coordenadas_nodos, signo)
            coordenadas_nodos = []
        dx, dy = self.get_discretizacion()
        EEH = SeccionGenerica(contornos, dx, dy)
        EEH.mostrar_seccion()
        return EEH

    def get_discretizacion(self):
        rows_range = self.excel_wb.get_n_rows_after_value("DISCRETIZACIÓN DE LA SECCIÓN", 5, rows_range=range(40, 300))
        dx = self.excel_wb.get_value_on_the_right("ΔX =", rows_range)
        dy = self.excel_wb.get_value_on_the_right("ΔY =", rows_range)
        return dx, dy

    def function_to_miminize(self, c):
        (ec, phix, phiy) = c
        return self.calcular_sumatoria_de_fuerzas(ec, phix, phiy)

    def calcular_sumatoria_de_fuerzas(self, ec, phix, phiy):
        ec_plano = lambda x, y: ec/100000+math.tan(math.radians(phix/1000))*(y-self.YG)+math.tan(math.radians(phiy/1000))*(x-self.XG) # Ecuacion del plano
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






