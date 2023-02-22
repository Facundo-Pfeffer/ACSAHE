from excel_manager import ExcelManager
from acero_pretensado import BarraAceroPretensado
from acero_pasivo import BarraAceroPasivo
from hormigon import Hormigon
from geometria import Nodo, Contorno, Recta, SeccionGenerica
from matrices import MatrizAceroPasivo
import math
import matplotlib.pyplot as plt
from scipy.optimize import fsolve


class FindInitialDeformation:
    def __init__(self, def_de_pretensado_inicial):
        self.def_de_pretensado_inicial = def_de_pretensado_inicial
        self.excel_wb = ExcelManager("DISGHA Prueba EJEMPLO 1 - PRETENSADO.xlsm")

        self.angulo_plano_de_carga_esperado = 0
        self.hormigon = Hormigon(tipo=self.excel_wb.get_value("C", "3"))
        self.tipo_estribo = self.excel_wb.get_value("E", "9")
        self.setear_propiedades_acero_pasivo()
        self.setear_propiedades_acero_activo()
        self.planos_de_deformacion = self.obtener_planos_de_deformacion()

        self.dx, self.dy = self.get_discretizacion()


        self.seccion_H = self.obtener_matriz_hormigon()
        self.EEH = self.seccion_H.elementos
        self.XG, self.YG = self.seccion_H.xg, self.seccion_H.yg

        self.EA = self.obtener_matriz_acero_pasivo()
        self.EAP = self.obtener_matriz_acero_pretensado()

        self.mostrar_seccion()

        result = fsolve(self.function_to_miminize, [0, 0, 0])
        ec, phix, phiy = result
        self.ec_plano_deformacion_elastica_inicial = lambda x, y: ec/100000+math.tan(math.radians(phix/1000))*(y-self.YG) + math.tan(math.radians(phiy/1000))*(x-self.XG)  # Ecuacion del plano referida al sistema de ecuaciones sin rotar
        self.asignar_deformacion_hormigon_a_elementos_pretensados()

        self.print_result_unidimensional(result)
        lista_resultados = self.iterar()
        self.mostrar_resultado(lista_resultados)

    def mostrar_seccion(self):
        # ax = plt.gca()
        # ax.set_aspect('equal', adjustable='box')
        self.EA.cargar_barras_como_circulos_para_mostrar()
        self.seccion_H.mostrar_seccion()
        plt.axis('equal')
        plt.show()

    def mostrar_resultado(self, lista_resultados):
        X = []
        Y = []
        for resultado in lista_resultados:
            sumF, M, plano_def, tipo, phi = resultado
            x = M/100
            y = -sumF  # Negativo para que la compresión quede en cuadrante I y II del diagrama.
            X.append(x)
            Y.append(y)

        fig = plt.figure()
        ax = fig.add_subplot(1, 1, 1)

        # Move left y-axis and bottim x-axis to centre, passing through (0,0)
        ax.spines['left'].set_position('zero')
        ax.spines['bottom'].set_position('zero')

        # Eliminate upper and right axes
        ax.spines['right'].set_color('none')
        ax.spines['top'].set_color('none')

        # Show ticks in the left and lower axes only
        ax.xaxis.set_ticks_position('bottom')
        ax.yaxis.set_ticks_position('left')



        plt.scatter(X, Y, c="r", marker=".")
        for resultado in lista_resultados:
            sumF, M, plano_def, tipo, phi = resultado
            x = M/100  # kN/m²
            y = -sumF  # kN
            # plt.annotate(str(phi), (x,y))
            plt.annotate(str(plano_def[2]), (x, y))
            # plt.annotate(str(plano_def), (x,y))

        plt.show()


    def asignar_deformacion_hormigon_a_elementos_pretensados(self):
        ec_plano = self.ec_plano_deformacion_elastica_inicial
        for elemento_pretensado in self.EAP:
            elemento_pretensado.def_elastica_hormigon_perdidas = ec_plano(elemento_pretensado.x, elemento_pretensado.y)

    def iterar(self):
        lista_de_puntos = []
        for plano_de_deformacion in self.planos_de_deformacion:
            try:
                sol = fsolve(self.obtener_theta_para_plano_de_carga, 0, args=plano_de_deformacion, xtol=0.05,
                             full_output=1)
                theta, diferencia_plano_de_carga = sol[0][0], sol[1]['fvec']
                if abs(diferencia_plano_de_carga) < 2:
                    sumF, Mx, My, phi = self.obtener_resultante_para_theta_y_def(theta, *plano_de_deformacion)
                    lista_de_puntos.append([sumF, self.obtener_momento_resultante(Mx, My), plano_de_deformacion, plano_de_deformacion[2], phi])
                else:  # Punto Descartado, no se encontró solución.
                    pass
            except RuntimeWarning as e:
                continue

        return lista_de_puntos



    def obtener_resultante_para_theta_y_def(self, theta, *plano_de_deformacion):
        EEH_girado, EA_girado, EAP_girado = self.calculo_distancia_eje_neutro_de_elementos(theta)
        EEH_girado.sort(key=lambda elemento_h: elemento_h.y_girado)
        ecuacion_plano_deformacion = self.obtener_ecuacion_plano_deformacion(EEH_girado, plano_de_deformacion)
        sumF, Mx, My, phi = self.calcular_sumatoria_de_fuerzas_en_base_a_eje_neutro_girado(EEH_girado, EA_girado, EAP_girado, ecuacion_plano_deformacion)
        return sumF, Mx, My, phi

    def obtener_theta_para_plano_de_carga(self, theta, *plano_de_deformacion):
        sumF, Mx, My, phi = self.obtener_resultante_para_theta_y_def(theta, *plano_de_deformacion)
        ex = round(My/sumF, 5)
        ey = round(Mx/sumF, 5)
        if ex == 0 and ey == 0:  # Carga centrada, siempre "pertenece" al plano de carga
            return 0
        angulo_plano_de_carga = self.obtener_angulo_resultante_momento(Mx, My)
        alpha = 90-self.angulo_plano_de_carga_esperado
        diferencia = angulo_plano_de_carga - alpha  # Apuntamos a que esto sea 0
        return diferencia

    def obtener_momento_resultante(self, Mx, My):
        return (1 if Mx >= 0 else -1) * math.sqrt(Mx**2 + My**2)

    def obtener_angulo_resultante_momento(self, Mx, My):
        M = self.obtener_momento_resultante(Mx, My)
        if M == 0:
            return
        if abs(My) > 10:  # Valores muy cercanos a 0 tienden a desestabilizar esta comparación
            inclinacion_plano_de_carga = math.degrees(math.acos(My/M))
        elif abs(Mx) > 10:
            inclinacion_plano_de_carga = math.degrees(math.asin(Mx/M))
        elif My !=0:
            inclinacion_plano_de_carga = math.degrees(math.atan(Mx/My))
        else:
            inclinacion_plano_de_carga = 0
        return inclinacion_plano_de_carga

    def calcular_sumatoria_de_fuerzas_en_base_a_eje_neutro_girado(self,EEH_girado, EA_girado, EAP_girado, ecuacion_plano_deformacion):
        y_max, y_min = EEH_girado[-1].y_girado, EEH_girado[0].y_girado
        sumFA = sumFP = sumFH = 0
        MxA = MxAP = MxH = 0
        MyA = MyAP = MyH = 0
        e1, e2 = ecuacion_plano_deformacion(y_max), ecuacion_plano_deformacion(y_min)

        def_max_comp = min(e1, e2)

        # c = def_max_comp*(y_max-y_min)/(-e1+e2)

        for barra in EA_girado:
            dist_eje_neutro, def_elemento, area = barra.y_girado, ecuacion_plano_deformacion(barra.y_girado), barra.area
            FA = barra.relacion_constitutiva(def_elemento) * area
            sumFA = sumFA + FA
            MxA = FA * barra.yg + MxA
            MyA = -FA * barra.xg + MyA

        for barra_p in EAP_girado:
            dist_eje_neutro, deformacion_neta, area = barra_p.y_girado, ecuacion_plano_deformacion(barra_p.y_girado), barra_p.area
            deformacion_hormigon = barra_p.def_elastica_hormigon_perdidas
            deformacion_pretensado_inicial = barra_p.deformacion_de_pretensado_inicial
            deformacion_total = deformacion_neta + deformacion_hormigon + deformacion_pretensado_inicial

            Fp = barra_p.relacion_constitutiva(deformacion_total) * area
            sumFP = sumFP + Fp
            MxAP = Fp * barra_p.yg + MxAP
            MyAP = -Fp * barra_p.xg + MyAP

        for elemento in EEH_girado:
            def_elemento, area = ecuacion_plano_deformacion(elemento.y_girado), elemento.area
            F_hor = self.hormigon.relacion_constitutiva_simplificada(def_elemento, e_max_comp=def_max_comp)*area
            sumFH = sumFH + F_hor
            MxH = F_hor * elemento.yg + MxH
            MyH = -F_hor * elemento.xg + MyH

        factor_minoracion_de_resistencia = self.obtener_factor_minoracion_de_resistencia(EA_girado, ecuacion_plano_deformacion, self.tipo_estribo)
        # factor_minoracion_de_resistencia = 1
        resultados_parciales = {
            "H": {"F": sumFH,
                  "Mx": MxH,
                  "My": MyH},
            "A": {"F": sumFA,
                  "Mx": MxA,
                  "My": MyA},
            "AP": {"F": sumFP,
                  "Mx": MxAP,
                  "My": MyAP}
        }

        sumF = sumFA + sumFP + sumFH
        Mx = round(MxA + MxAP + MxH, 8)
        My = round(MyA + MyAP + MyH, 8)


        sumF = factor_minoracion_de_resistencia * sumF
        Mx = factor_minoracion_de_resistencia * Mx
        My = factor_minoracion_de_resistencia * My
        return sumF, Mx, My, factor_minoracion_de_resistencia

    def obtener_ecuacion_plano_deformacion(self, EEH_girado, plano_de_deformacion):
        y_max, y_min = EEH_girado[-1].y_girado, EEH_girado[0].y_girado
        def_max, def_min = plano_de_deformacion[0], plano_de_deformacion[1]
        A = (def_max-def_min)/(y_max-y_min)
        B = def_min-A*y_min
        return lambda y_girado: y_girado*A+B

    def calculo_distancia_eje_neutro_de_elementos(self, theta):
        EEH_girado, EA_girado, EAP_girado = self.EEH.copy(), self.EA.copy(), self.EAP.copy()
        for elemento_hormigon in EEH_girado:
            elemento_hormigon.y_girado = self.distancia_eje_rotado(elemento_hormigon, angulo=theta)
        for elemento_acero in EA_girado:
            elemento_acero.y_girado = self.distancia_eje_rotado(elemento_acero, angulo=theta)
        for elemento_acero_p in EAP_girado:
            elemento_acero_p.y_girado = self.distancia_eje_rotado(elemento_acero_p, angulo=theta)
        return EEH_girado, EA_girado, EAP_girado

    def distancia_eje_rotado(self, elemento, angulo):
        angulo_rad = angulo * math.pi/180
        value = -elemento.xg * math.sin(angulo_rad) + elemento.yg * math.cos(angulo_rad)
        return value

    @staticmethod
    def obtener_planos_de_deformacion():
        result = []
        for j in range(290):
            if j <= 25:
                def_superior = -3
                def_inferior = -3 + 0.1*j
                tipo = f"1-{j}"
            elif j>25 and j<=100:
                def_superior = -3
                def_inferior = -3 + 0.03 * j
                tipo = f"2-{j}"
            elif j>100 and j<=200:
                def_superior = -3
                def_inferior = -3 + 0.1 * (j-70)
                tipo = f"3-{j}"
            elif j>200 and j<=230:
                def_superior = -3
                def_inferior = 10 + (j-200)*2
                tipo = f"4-{j}"
            else:
                def_superior = -3+(j-230)*0.15
                def_inferior = 60
                tipo = f"5-{j}"
        # for j in range(110):
        #     if j<=65:
        #         def_superior = -3
        #         def_inferior = -3 + 0.2*j
        #         tipo = f"1-{j}"
        #     elif j<=90:
        #         def_superior = -3
        #         def_inferior = 10+(j-65)*2
        #         tipo = f"2-{j}"
        #     else:
        #         def_superior = -3 + (j-90) * 0.3
        #         def_inferior = 60
        #         tipo = f"3-{j}"
            result.append((def_superior/1000, def_inferior/1000, tipo))
        lista_invertida = [(x[1], x[0], "-" + x[2]) for x in result]
        return result + lista_invertida

    def obtener_angulo_plano_de_carga(self):
        rows_n = self.excel_wb.get_n_rows_after_value("INCLINACIÓN DEL PLANO DE CARGA", 5)

    def obtener_matriz_acero_pasivo(self):
        lista_filas = self.excel_wb.get_rows_range_between_values(("ARMADURAS", "ARMADURAS PRETENSADAS"))
        resultado = MatrizAceroPasivo()
        for fila in lista_filas[5:-1]:  #TODO mejorar
            x, y, d = self.obtener_valores_acero_tabla(fila)
            if d == 0:
                continue
            xg = round(x*100 - self.XG, 10)
            yg = round(y*100 - self.YG, 10)
            resultado.append(BarraAceroPasivo(xg, yg, d))
        return resultado

    def verificar_tolerancia(self, valor):
        tolerancia = 0.00000000000004
        return 0 if abs(valor) <= tolerancia else valor

    def obtener_valores_acero_tabla(self, fila):
        return self.excel_wb.get_value("C", fila), self.excel_wb.get_value("E", fila), self.excel_wb.get_value("G", fila)

    def setear_propiedades_acero_pasivo(self):
        try:
            tipo = self.excel_wb.get_value("C", "5")
            values = BarraAceroPasivo.tipos_de_acero_y_valores.get(tipo)
            for k, v in values.items():
                self.__setattr__(k, v)
            fy = BarraAceroPasivo.tipos_de_acero_y_valores.get(tipo.upper())["fy"]
            BarraAceroPasivo.E = 200000
            BarraAceroPasivo.fy = fy
        except Exception:
            raise Exception("No se pudieron setear las propiedades del acero pasivo, revise configuración")

    def obtener_matriz_acero_pretensado(self):
        lista_filas = self.excel_wb.get_rows_range_between_values(("ARMADURAS PRETENSADAS", "DISCRETIZACIÓN DE LA SECCIÓN"))
        resultado = []
        for fila in lista_filas[5:-1]:
            x, y, d = self.obtener_valores_acero_tabla(fila)
            if d == 0:
                continue
            x = x - self.XG
            y = y - self.YG
            resultado.append(BarraAceroPretensado(x, y, d))
        return resultado

    def setear_propiedades_acero_activo(self):
        try:
            tipo = self.excel_wb.get_value("C", "7")
            tipo = tipo.upper()
            values = BarraAceroPretensado.tipos_de_acero_y_valores.get(tipo)
            for k, v in values.items():
                setattr(BarraAceroPretensado, k, v)
            BarraAceroPretensado.Eps = 20000  # kN/cm²
            BarraAceroPretensado.deformacion_de_pretensado_inicial = self.def_de_pretensado_inicial
        except Exception:
            raise Exception("No se pudieron setear las propiedades del acero activo, revise configuración")

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
                coordenadas_nodos.append(Nodo(x*100, y*100))
            contornos[str(i+1)] = Contorno(coordenadas_nodos, signo, ordenar=True)
            coordenadas_nodos = []
        dx, dy = self.get_discretizacion()
        EEH = SeccionGenerica(contornos, dx, dy)
        return EEH

    def get_discretizacion(self):
        rows_range = self.excel_wb.get_n_rows_after_value("DISCRETIZACIÓN DE LA SECCIÓN", 5, rows_range=range(40, 300))
        dx = self.excel_wb.get_value_on_the_right("ΔX =", rows_range)
        dy = self.excel_wb.get_value_on_the_right("ΔY =", rows_range)
        return dx * 100, dy * 100  # En centímetros

    def function_to_miminize(self, c):
        (ec, phix, phiy) = c
        return self.calcular_sumatoria_de_fuerzas_en_base_a_plano_baricentrico(ec, phix, phiy)


    def obtener_factor_minoracion_de_resistencia(self, EA, ecuacion_plano_de_def, tipo_estribo):
        phi_min = 0.65 if tipo_estribo != "Zunchos en espiral" else 0.7
        if len(EA) == 0:  # Hormigón Simple
            return 0.55
        lista_def_girado = [ecuacion_plano_de_def(barra.y_girado) for barra in EA]
        y_girado_max = max(lista_def_girado)
        if y_girado_max >= 5/1000:
            return 0.9
        elif y_girado_max < 2/1000:
            return phi_min
        else:
            return phi_min*(0.005-y_girado_max)/0.003 + 0.9*(y_girado_max-0.002)/0.003  # Interpolación lineal

    def calcular_sumatoria_de_fuerzas_en_base_a_plano_baricentrico(self, ec, phix, phiy):
        ec_plano = lambda x, y: ec/100000+math.tan(math.radians(phix/1000))*(y-self.YG)+math.tan(math.radians(phiy/1000))*(x-self.XG) # Ecuacion del plano
        sumF = 0
        Mx = 0
        My = 0
        EA = self.EA
        EAP = self.EAP
        EEH = self.EEH
        for barra in EA:
            x, y, e, A = barra.x, barra.y, ec_plano(barra.x, barra.y), barra.area
            F = -barra.relacion_constitutiva(e) * A
            sumF = sumF + F
            Mx = F * y + Mx
            My = -F * x + My
        for barra_p in EAP:
            x, y, e, A = barra_p.x, barra_p.y, ec_plano(barra_p.x, barra_p.y), barra_p.area
            F = (barra_p.relacion_constitutiva(-e+self.def_de_pretensado_inicial)) * A
            sumF = sumF + F
            Mx = F * y + Mx
            My = -F * x + My
        for elemento in EEH:
            x, y, e, A = elemento.xg, elemento.yg, ec_plano(elemento.xg, elemento.yg), elemento.area
            F = -(self.hormigon.relacion_constitutiva_elastica(e)) * A
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
        # plt.show()

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


resolver = FindInitialDeformation(5/1000)






