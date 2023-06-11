from excel_manager import ExcelManager
from acero_pretensado import BarraAceroPretensado
from acero_pasivo import BarraAceroPasivo
from hormigon import Hormigon
from geometria import Nodo, Contorno, Recta, SeccionGenerica
from matrices import MatrizAceroPasivo, MatrizAceroActivo
import math
import matplotlib.pyplot as plt
from scipy.optimize import fsolve

import warnings


class FindInitialDeformation:
    def __init__(self):
        file_name = "Archivos Excel/PLANILLA SCRATCH.xlsm"
        self.excel_wb = ExcelManager(file_name, "Ingreso de Datos")
        self.armaduras_pasivas_wb = ExcelManager(file_name, "Armaduras Pasivas")
        self.angulo_plano_de_carga_esperado = self.obtener_angulo_plano_de_carga()
        warnings.filterwarnings("error")

        self.def_de_rotura_a_pasivo = self.obtener_def_de_rotura_a_pasivo()
        self.def_de_pretensado_inicial = self.obtener_def_de_pretensado_inicial()

        self.hormigon = Hormigon(tipo=self.excel_wb.get_value("C", "4"))  # TODO mejorar
        self.tipo_estribo = self.excel_wb.get_value("E", "10")

        self.setear_propiedades_acero_pasivo()
        self.setear_propiedades_acero_activo()
        self.medir_diferencias = []

        self.dx, self.dy = self.get_discretizacion()

        self.seccion_H = self.obtener_matriz_hormigon()
        self.EEH = self.seccion_H.elementos
        self.XG, self.YG = self.seccion_H.xg, self.seccion_H.yg

        self.EA = self.obtener_matriz_acero_pasivo()
        self.EAP = self.obtener_matriz_acero_pretensado()
        self.mostrar_seccion()

        self.deformacion_maxima_de_acero = self.obtener_deformacion_maxima_de_acero()

        self.planos_de_deformacion = self.obtener_planos_de_deformacion()
        self.mostrar_planos_de_deformacion()

        ec, phix, phiy = self.obtener_plano_deformación_inicial()
        self.print_result_tridimensional(ec, phix, phiy)
        self.ec_plano_deformacion_elastica_inicial = lambda x, y: ec + math.tan(math.radians(phix)) * (y) + math.tan(
            math.radians(phiy)) * (x)
        self.asignar_deformacion_hormigon_a_elementos_pretensados()

        self.lista_planos_sin_solucion = []
        lista_resultados = self.iterar()
        print(f"Se obtuvieron {len(self.lista_planos_sin_solucion)}/{len(lista_resultados)} puntos sin solución,"
              f"\nTotal: {len(self.lista_planos_sin_solucion)+len(lista_resultados)}"
              f"\nDetalles:"
              f"{self.lista_planos_sin_solucion}")
        self.medir_diferencias.sort(reverse=True)
        print(self.medir_diferencias)
        self.mostrar_resultado(lista_resultados)

    def obtener_plano_deformación_inicial(self):
        resultado = fsolve(
            self.converger_funcion_desplazamiento_elastico_inicial, [-self.def_de_pretensado_inicial, 0, 0])
        ec, phix, phiy = resultado
        return ec, phix, phiy

    def converger_funcion_desplazamiento_elastico_inicial(self, c):
        (ec, phix, phiy) = c
        return self.calcular_sumatoria_de_fuerzas_en_base_a_plano_baricentrico(ec, phix, phiy)

    def obtener_deformacion_maxima_de_acero(self):
        def_max_acero_pasivo = BarraAceroPasivo.eu
        def_max_acero_activo = BarraAceroPretensado.epu
        return min(def_max_acero_pasivo, def_max_acero_activo)

    def obtener_def_de_rotura_a_pasivo(self):
        value = self.armaduras_pasivas_wb.get_value("B", 6)  # TODO mejorar
        return value

    def obtener_def_de_pretensado_inicial(self):
        value = self.excel_wb.get_value("E", 8)  # TODO mejorar
        return value / 1000

    def mostrar_seccion(self):
        # ax = plt.gca()
        # ax.set_aspect('equal', adjustable='box')
        fig, ax = self.EA.cargar_barras_como_circulos_para_mostrar()
        self.EAP.cargar_barras_como_circulos_para_mostrar(fig, ax)
        self.seccion_H.mostrar_contornos_2d()
        self.seccion_H.mostrar_discretizacion_2d()
        plt.title("Sección y Discretización")
        plt.axis('equal')
        plt.show()

    def mostrar_planos_de_deformacion(self):
        lista_colores = ["k", "r", "b", "g", "c", "m", "y", "k"]
        plt.plot([0, 0], [1, -1], c=lista_colores[0], linewidth=10, zorder=10)
        for p_def in self.planos_de_deformacion:
            plt.title("Planos de Deformación")
            tipo = p_def[2]
            if tipo >= 0:
                plt.plot([-p_def[0], -p_def[1]], [1, -1], c=lista_colores[tipo], linewidth=2, zorder=1)
        plt.show()

    def mostrar_resultado(self, lista_resultados):
        lista_colores = ["k", "r", "b", "g", "c", "m", "y", "k"]

        X = []
        Y = []

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

        for resultado in lista_resultados:
            sumF, M, plano_def, tipo, phi = resultado
            x = M / 100
            y = -sumF  # Negativo para que la compresión quede en cuadrante I y II del diagrama.
            X.append(x)
            Y.append(y)
            plt.scatter(x, y, c=lista_colores[abs(tipo)], marker="." if tipo >= 0 else "x")
        # for resultado in lista_resultados:
        #     sumF, M, plano_def, tipo, phi = resultado
        #     x = M / 100  # kN/m²
        #     y = -sumF  # kN
        #     #     # plt.annotate(str(phi), (x,y))
        #     #     plt.annotate(str(f"{round(plano_def[0]*1000, 3)}/{round(plano_def[1]*1000, 3)}"), (x, y))
        #     plt.annotate(plano_def[3], (x, y))
            # plt.annotate(str(plano_def), (x,y))
        plt.title("Rultado")
        plt.show()

    def asignar_deformacion_hormigon_a_elementos_pretensados(self):
        ec_plano = self.ec_plano_deformacion_elastica_inicial
        for elemento_pretensado in self.EAP:
            elemento_pretensado.def_elastica_hormigon_perdidas = ec_plano(elemento_pretensado.xg,
                                                                          elemento_pretensado.yg)

    def iterar(self):
        lista_de_puntos = []
        try:
            for plano_de_deformacion in self.planos_de_deformacion:
                sol = fsolve(self.obtener_theta_para_plano_de_carga, 0, xtol=0.001, args=plano_de_deformacion,
                             full_output=1, maxfev=100)  # Max fev = número de iteraciones máximo
                theta, diferencia_plano_de_carga, sol_encontrada = sol[0][0], sol[1]['fvec'], sol[2] == 1
                self.medir_diferencias.append((diferencia_plano_de_carga, plano_de_deformacion))
                if sol_encontrada is True and abs(diferencia_plano_de_carga) < 5:
                    sumF, Mx, My, phi = self.obtener_resultante_para_theta_y_def(theta, *plano_de_deformacion)
                    lista_de_puntos.append(
                        [sumF, self.obtener_momento_resultante(Mx, My), plano_de_deformacion, plano_de_deformacion[2],
                         phi])

                else:  # Punto Descartado, no se encontró solución.
                    self.lista_planos_sin_solucion.append(f"{plano_de_deformacion}\n{sol}")
        except Exception as e:
            pass

        return lista_de_puntos

    def obtener_resultante_para_theta_y_def(self, theta, *plano_de_deformacion):
        EEH_girado, EA_girado, EAP_girado = self.calculo_distancia_eje_neutro_de_elementos(theta)
        EEH_girado.sort(key=lambda elemento_h: elemento_h.y_girado)
        EA_girado.sort(key=lambda elemento_a: elemento_a.y_girado)
        EAP_girado.sort(key=lambda elemento_ap: elemento_ap.y_girado)
        ecuacion_plano_deformacion = self.obtener_ecuacion_plano_deformacion(EEH_girado, EA_girado, EAP_girado,
                                                                             plano_de_deformacion)
        sumF, Mx, My, phi = self.calcular_sumatoria_de_fuerzas_en_base_a_eje_neutro_girado(EEH_girado, EA_girado,
                                                                                           EAP_girado,
                                                                                           ecuacion_plano_deformacion)
        return sumF, Mx, My, phi

    # def obtener_def_max_comp(self, plano_de_deformacion):

    def obtener_theta_para_plano_de_carga(self, theta, *plano_de_deformacion):
        sumF, Mx, My, phi = self.obtener_resultante_para_theta_y_def(theta, *plano_de_deformacion)
        ex = round(My / sumF, 5)
        ey = round(Mx / sumF, 5)
        if ex == 0 and ey == 0:  # Carga centrada, siempre "pertenece" al plano de carga
            return 0
        angulo_plano_de_carga = self.obtener_angulo_resultante_momento(Mx, My)
        alpha = 90 - self.angulo_plano_de_carga_esperado
        diferencia = angulo_plano_de_carga - alpha  # Apuntamos a que esto sea 0
        return diferencia

    def obtener_momento_resultante(self, Mx, My):
        return (1 if Mx >= 0 else -1) * math.sqrt(Mx ** 2 + My ** 2)

    def obtener_angulo_resultante_momento(self, Mx, My):
        M = self.obtener_momento_resultante(Mx, My)
        if M == 0:
            return
        if abs(My) > 10:  # Valores muy cercanos a 0 tienden a desestabilizar esta comparación
            inclinacion_plano_de_carga = math.degrees(math.acos(My / M))
        elif abs(Mx) > 10:
            inclinacion_plano_de_carga = math.degrees(math.asin(Mx / M))
        elif My != 0:
            inclinacion_plano_de_carga = math.degrees(math.atan(Mx / My))
        else:
            inclinacion_plano_de_carga = 0
        return inclinacion_plano_de_carga

    def obtener_ecuacion_plano_deformacion(self, EEH_girado, EA_girado, EAP_girado, plano_de_deformacion):
        """Construye la ecuación de una recta que pasa por los puntos (y_positivo,def_1) (y_negativo,def_2).
        y_positivo e y_negativo seran la distancia al eje neutro del elemento de hormigon mas comprimido, o
        de la barra de acero (pasivo o activo) mas traccionada. Lo positivo o negativo depende de que lado del eje neutro
        se encuentra el analisis."""
        try:

            def_1, def_2 = plano_de_deformacion[0], plano_de_deformacion[1]
            y_positivo = self.obtener_y_determinante_positivo(def_1, EA_girado, EAP_girado, EEH_girado)
            y_negativo = self.obtener_y_determinante_negativo(def_2, EA_girado, EAP_girado, EEH_girado)
            A = (def_1 - def_2) / (y_positivo - y_negativo)
            B = def_2 - A * y_negativo
            return lambda y_girado: y_girado * A + B
        except RuntimeWarning as e:
            print(e)

    def obtener_y_determinante_positivo(self, def_extrema, EA_girado, EAP_girado, EEH_girado):
        """Lo positivo indica que se encuentra con coordendas y_girado positivas (de un lado del eje neutro)"""
        if def_extrema <= 0 or def_extrema < self.deformacion_maxima_de_acero:  # Compresión
            return EEH_girado[-1].y_girado  # Fibra de Hormigón más alejada
        return max(EA_girado[-1].y_girado, EAP_girado[-1].y_girado)  # Armadura más traccionada (más alejada eje neutro)

    def obtener_y_determinante_negativo(self, def_extrema, EA_girado, EAP_girado, EEH_girado):
        """Lo negativco indica que se encuentra con coordendas y_girado negativas (de un lado del eje neutro)"""
        if def_extrema <= 0 or def_extrema < self.deformacion_maxima_de_acero:
            return EEH_girado[0].y_girado  # Maxima fibra comprimida hormigón
        return min(EA_girado[0].y_girado, EAP_girado[0].y_girado)  # Armadura más traccionada (más alejada eje neutro)

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
        angulo_rad = angulo * math.pi / 180
        value = -elemento.xg * math.sin(angulo_rad) + elemento.yg * math.cos(angulo_rad)
        return value

    def obtener_planos_de_deformacion(self):
        """Obtiene una lista de los planos de deformación últimos a utilizarse para determinar los estados de resistencia
        últimos, cada elemento de esta lista representa, en principio, un punto sobre el diagrama de interacción.
        Este puede no ser el caso si hay puntos para los cuales no se encuentra una convergencia, en ese caso será
        descartado."""
        lista_de_planos = []
        try:
            lista_de_rangos = [(0, 15), (16, 100), (101, 200), (201, 275), (275, 325), (326, 350)]
            for j in range(350):
                if j <= 25:
                    def_final = -0.5
                    def_superior = -3
                    def_inferior = -3 + (def_final + 3) * j / (25)  # Hasta -0.3
                    tipo = 1
                elif 25 < j <= 100:
                    def_inicial = -0.5
                    def_final = 0
                    def_superior = -3
                    def_inferior = def_inicial + (def_final-def_inicial) * (j - 25) / (100 - 25)  # Hasta 0
                    tipo = 2
                elif 100 < j <= 200:
                    def_superior = -3
                    def_inferior = 10 * (j - 100) / (200 - 100)
                    tipo = 3
                elif 200 < j <= 275:  # Hasta la deformación máxima del acero.
                    def_superior = -3
                    def_inferior = 10 + (j - 200) * (self.deformacion_maxima_de_acero * 1000 - 10) / (275 - 200)
                    tipo = 4
                elif j <= 325:
                    def_superior = -3 + (6 + 3) * (j - 275) / (325 - 275)
                    def_inferior = self.deformacion_maxima_de_acero * 1000
                    tipo = 5
                else:
                    def_superior = 6 + (self.deformacion_maxima_de_acero * 1000 - 6) * (j - 325) / (350 - 326)
                    def_inferior = self.deformacion_maxima_de_acero * 1000
                    tipo = 6
                lista_de_planos.append((def_superior / 1000, def_inferior / 1000, tipo, j))
        except AttributeError as e:
            pass
        lista_invertida = [(x[1], x[0], -x[2], x[3]) for x in lista_de_planos]  # Misma lista, invertida de signo
        return lista_de_planos + lista_invertida

    def obtener_angulo_plano_de_carga(self):
        rows_n = self.excel_wb.get_n_rows_after_value("INCLINACIÓN DEL PLANO DE CARGA", 5)
        return self.excel_wb.get_value("E", rows_n[2])  # TODO mejorar

    def obtener_matriz_acero_pasivo(self):
        lista_filas = self.excel_wb.get_rows_range_between_values(
            ("ARMADURAS PASIVAS (H°- Armado)", "ARMADURAS ACTIVAS (H°- Pretensado)"))
        resultado = MatrizAceroPasivo()
        for fila in lista_filas[5:-1]:  # TODO mejorar
            x, y, d = self.obtener_valores_acero_tabla(fila)
            if d == 0:
                continue
            xg = round(x - self.XG, 5)
            yg = round(y - self.YG, 5)
            resultado.append(BarraAceroPasivo(xg, yg, d))
        return resultado

    def verificar_tolerancia(self, valor):
        tolerancia = 0.00000000000004
        return 0 if abs(valor) <= tolerancia else valor

    def obtener_valores_acero_tabla(self, fila):
        return self.excel_wb.get_value("C", fila), self.excel_wb.get_value("E", fila), self.excel_wb.get_value("G", fila)

    def setear_propiedades_acero_pasivo(self):
        try:
            tipo = self.excel_wb.get_value("C", "6")
            values = BarraAceroPasivo.tipos_de_acero_y_valores.get(tipo)
            for k, v in values.items():
                self.__setattr__(k, v)
            fy = BarraAceroPasivo.tipos_de_acero_y_valores.get(tipo.upper())["fy"]
            BarraAceroPasivo.E = 200000
            BarraAceroPasivo.fy = fy
            BarraAceroPasivo.eu = self.def_de_rotura_a_pasivo
        except Exception:
            raise Exception("No se pudieron setear las propiedades del acero pasivo, revise configuración")

    def obtener_matriz_acero_pretensado(self):
        lista_filas = self.excel_wb.get_rows_range_between_values(
            ("ARMADURAS ACTIVAS (H°- Pretensado)", "DISCRETIZACIÓN DE LA SECCIÓN"))
        resultado = MatrizAceroActivo()
        for fila in lista_filas[5:-1]:  # TODO mejorar
            x, y, area = self.obtener_valores_acero_tabla(fila)
            if area == 0:
                continue
            xg = round(x - self.XG, 5)
            yg = round(y - self.YG, 5)
            resultado.append(BarraAceroPretensado(xg, yg, area))
        return resultado

    def setear_propiedades_acero_activo(self):
        try:
            tipo = self.excel_wb.get_value("C", "8")
            tipo = tipo.upper()
            values = BarraAceroPretensado.tipos_de_acero_y_valores.get(tipo)
            for k, v in values.items():
                setattr(BarraAceroPretensado, k, v)
            BarraAceroPretensado.Eps = 20000  # kN/cm²
            BarraAceroPretensado.deformacion_de_pretensado_inicial = self.def_de_pretensado_inicial
        except Exception:
            raise Exception("No se pudieron setear las propiedades del acero activo, revise configuración")

    def get_signo(self, contorno):  # TODO mejorar
        value = self.excel_wb.get_value("D", contorno[0])
        return +1 if "Pos" in value else -1

    def get_cantidad_de_nodos(self, contorno):  # TODO mejorar
        return self.excel_wb.get_value("G", contorno[0])

    def obtener_matriz_hormigon(self):
        filas_hormigon = self.excel_wb.get_rows_range_between_values(
            ("GEOMETRÍA DE LA SECCIÓN DE HORMIGÓN", "ARMADURAS PASIVAS (H°- Armado)"))
        lista_filas_contornos = self.excel_wb.subdivide_range_in_filled_ranges("B", filas_hormigon)
        contornos = {}
        coordenadas_nodos = []
        for i, filas_contorno in enumerate(lista_filas_contornos):
            signo = self.get_signo(filas_contorno)
            cantidad_de_nodos = self.get_cantidad_de_nodos(filas_contorno)
            for fila_n in self.excel_wb.get_n_rows_after_value("Nodo nº", cantidad_de_nodos + 1,
                                                               rows_range=filas_contorno)[1:]:
                x = self.excel_wb.get_value("C", fila_n)
                y = self.excel_wb.get_value("E", fila_n)
                coordenadas_nodos.append(Nodo(x, y))  # Medidas en centímetros
            contornos[str(i + 1)] = Contorno(coordenadas_nodos, signo, ordenar=True)
            coordenadas_nodos = []
        dx, dy = self.get_discretizacion()
        EEH = SeccionGenerica(contornos, dx, dy)
        return EEH

    def get_discretizacion(self):
        rows_range = self.excel_wb.get_n_rows_after_value("DISCRETIZACIÓN DE LA SECCIÓN", 5, rows_range=range(40, 300))
        dx = self.excel_wb.get_value_on_the_right("ΔX =", rows_range)
        dy = self.excel_wb.get_value_on_the_right("ΔY =", rows_range)
        return dx, dy  # En centímetros

    def obtener_factor_minoracion_de_resistencia(self, EA_girado, EAP_girado, ecuacion_plano_de_def, tipo_estribo):
        phi_min = 0.65 if tipo_estribo != "Zunchos en espiral" else 0.7
        if len(EA_girado) == 0 and len(EAP_girado) == 0:  # Hormigón Simple
            return 0.55
        lista_def_girado = [ecuacion_plano_de_def(barra.y_girado) for barra in EA_girado + EAP_girado]
        y_girado_max = max(lista_def_girado)
        if y_girado_max >= 5 / 1000:
            return 0.9
        elif y_girado_max < 2 / 1000:
            return phi_min
        else:
            return phi_min * (0.005 - y_girado_max) / 0.003 + 0.9 * (
                    y_girado_max - 0.002) / 0.003  # Interpolación lineal

    def calcular_sumatoria_de_fuerzas_en_base_a_plano_baricentrico(self, ec, phix, phiy):
        ecuacion_plano_deformacion = lambda x, y: ec + math.tan(math.radians(phix)) * (y) + math.tan(
            math.radians(phiy)) * (x)
        sumFA = sumFP = sumFH = 0
        MxA = MxAP = MxH = 0
        MyA = MyAP = MyH = 0
        for barra in self.EA:
            def_elemento, area = ecuacion_plano_deformacion(barra.xg, barra.yg), barra.area
            FA = barra.relacion_constitutiva(def_elemento) * area
            sumFA = sumFA + FA
            MxA = FA * barra.yg + MxA
            MyA = -FA * barra.xg + MyA
        for barra_p in self.EAP:
            deformacion_elastica_hormingon, area = ecuacion_plano_deformacion(barra_p.xg, barra_p.yg), barra_p.area
            deformacion_pretensado_inicial = barra_p.deformacion_de_pretensado_inicial
            deformacion_total = deformacion_elastica_hormingon + deformacion_pretensado_inicial

            Fp = barra_p.relacion_constitutiva(deformacion_total) * area
            sumFP = sumFP + Fp
            MxAP = Fp * barra_p.yg + MxAP
            MyAP = -Fp * barra_p.xg + MyAP

        for elemento in self.EEH:
            def_elemento, area = ecuacion_plano_deformacion(elemento.xg, elemento.yg), elemento.area
            F_hor = self.hormigon.relacion_constitutiva_elastica(def_elemento) * area
            sumFH = sumFH + F_hor
            MxH = F_hor * elemento.yg + MxH
            MyH = -F_hor * elemento.xg + MyH

        sumF = sumFA + sumFP + sumFH
        Mx = round(MxA + MxAP + MxH, 8)
        My = round(MyA + MyAP + MyH, 8)

        return [sumF, Mx, My]

    def calcular_sumatoria_de_fuerzas_en_base_a_eje_neutro_girado(
            self, EEH_girado, EA_girado, EAP_girado, ecuacion_plano_deformacion):
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

        deformaciones_pp = []
        for barra_p in EAP_girado:
            dist_eje_neutro, deformacion_neta, area = barra_p.y_girado, ecuacion_plano_deformacion(
                barra_p.y_girado), barra_p.area
            deformacion_hormigon = barra_p.def_elastica_hormigon_perdidas
            deformacion_pretensado_inicial = barra_p.deformacion_de_pretensado_inicial
            deformacion_total = deformacion_neta + deformacion_hormigon + deformacion_pretensado_inicial

            deformaciones_pp.append(
                {
                    "elastica": deformacion_hormigon,
                    "inicial": deformacion_pretensado_inicial,
                    "neta": deformacion_neta,
                    "total": deformacion_total
                }
            )

            Fp = barra_p.relacion_constitutiva(deformacion_total) * area
            sumFP = sumFP + Fp
            MxAP = Fp * barra_p.yg + MxAP
            MyAP = -Fp * barra_p.xg + MyAP

        for elemento in EEH_girado:
            def_elemento, area = ecuacion_plano_deformacion(elemento.y_girado), elemento.area
            F_hor = self.hormigon.relacion_constitutiva_simplificada(def_elemento, e_max_comp=def_max_comp) * area
            sumFH = sumFH + F_hor
            MxH = F_hor * elemento.yg + MxH
            MyH = -F_hor * elemento.xg + MyH

        factor_minoracion_de_resistencia = self.obtener_factor_minoracion_de_resistencia(
            EA_girado, EAP_girado, ecuacion_plano_deformacion, self.tipo_estribo)
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

    def print_result_tridimensional(self, ec, phix, phiy):
        ec_plano = lambda x, y: ec + math.tan(math.radians(phix)) * y + math.tan(math.radians(phiy)) * x
        self.seccion_H.mostrar_contornos_3d(ecuacion_plano_a_desplazar=ec_plano)


resolver = FindInitialDeformation()
