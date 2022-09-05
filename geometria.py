import random
import matplotlib.pyplot as plt
import numpy as np
from copy import copy as CopyObject


class Nodo(object):
    def __init__(self, x, y):
        self.x = x
        self.y = y


class Segmento(object):
    def __init__(self, nodo_1: Nodo, nodo_2: Nodo):
        self.nodo_1 = nodo_1
        self.nodo_2 = nodo_2
        self.recta_segmento = Recta(nodo_1, nodo_2)
        self.extremos_x, self.extremos_y = self.extremos_segmento()

    def obtener_parametros_ecuacion_recta(self):
        x1, y1 = self.nodo_1.x, self.nodo_1.y
        x2, y2 = self.nodo_2.x, self.nodo_2.y
        a = y1 - y2
        b = x2 - x1
        c = y2 * (x1 - x2) + (y2 - y1) * x2
        return a, b, c

    def determinar_si_nodo_esta_en_rango(self, nodo):
        tolerancia = 0.000000000000001
        xmin, xmax = self.extremos_x
        ymin, ymax = self.extremos_y
        return xmin - tolerancia <= nodo.x <= xmax + tolerancia and ymin - tolerancia <= nodo.y <= ymax + tolerancia

    def determinar_si_nodo_pertenece_a_segmento(self, nodo):
        return self.recta_segmento.ecuacion_recta(nodo) == 0 and  self.determinar_si_nodo_esta_en_rango(nodo)

    def extremos_segmento(self):
        extramos_x = (min(self.nodo_1.x, self.nodo_2.x), max(self.nodo_1.x, self.nodo_2.x))
        extramos_y = (min(self.nodo_1.y, self.nodo_2.y), max(self.nodo_1.y, self.nodo_2.y))
        return extramos_x, extramos_y

    def obtener_interseccion_recta(self, recta):
        nodo_interseccion_rectas = recta & self.recta_segmento
        if not nodo_interseccion_rectas:  # Paralelas
            return None
        resultado = nodo_interseccion_rectas if self.determinar_si_nodo_esta_en_rango(nodo_interseccion_rectas) else None
        return resultado

    def __and__(self, otro_segmento):
        result = self.recta_segmento & otro_segmento.recta_segmento  # Buscando interseccion
        if not result:
            return None
        return result if self.determinar_si_nodo_esta_en_rango(result) and otro_segmento.determinar_si_nodo_esta_en_rango(result) else None


class Recta(object):
    def __init__(self, nodo_1: Nodo, nodo_2: Nodo):
        self.nodo_1 = nodo_1
        self.nodo_2 = nodo_2
        a, b, c = self.obtener_parametros_ecuacion_recta()
        self.ecuacion_recta = lambda nodo: a*nodo.x + b*nodo.y + c
        self.distancia_a_nodo = lambda nodo: (a*nodo.x + b*nodo.y + c)/((a**2 + b**2)**0.5)
        self.distancia_a_nodo_v = lambda nodo: abs(nodo.y + (c+a*nodo.x)/b) if b!=0 else None
        self.distancia_a_nodo_h = lambda nodo: abs(nodo.x + (c+b*nodo.y)/a) if a!=0 else None

        self.y = lambda x: -c/b - a/b * x
        self.x = lambda y: -c/a - b/a * y

    def obtener_parametros_ecuacion_recta(self):
        x1, y1 = self.nodo_1.x, self.nodo_1.y
        x2, y2 = self.nodo_2.x, self.nodo_2.y
        a = y1 - y2
        b = x2 - x1
        c = y2*(x1-x2) + (y2-y1)*x2
        return a, b, c

    def mostrar_recta(self):
        plt.plot([self.nodo_1.x, self.nodo_2.x], [self.nodo_1.y, self.nodo_2.y])

    def __and__(self, otra_recta):
        """Intersecta las rectas
        :param otra_recta:
        :return Nodo or None:"""
        tolerancia = 0.000000000000001
        x1, y1, x2, y2 = self.nodo_1.x, self.nodo_1.y, self.nodo_2.x, self.nodo_2.y
        x3, y3, x4, y4 = otra_recta.nodo_1.x, otra_recta.nodo_1.y, otra_recta.nodo_2.x, otra_recta.nodo_2.y
        den = (x1-x2)*(y3-y4) - (y1-y2)*(x3-x4)
        if -1*tolerancia <= den <= tolerancia: # Las rectas son paralelas, no hay interseccion
            return None
        x = ((x1*y2 - y1*x2)*(x3-x4)-(x1-x2)*(x3*y4-y3*x4))/den
        y = ((x1*y2 - y1*x2)*(y3-y4)-(y1-y2)*(x3*y4-y3*x4))/den
        return Nodo(x, y)


class Poligono(object):

    def __init__(self, nodos):
        self.nodos_extremos = self.ordenar_nodos_antihorario(nodos)
        self.x = [nodo.x for nodo in self.nodos_extremos]
        self.y = [nodo.y for nodo in self.nodos_extremos]
        self.total_de_nodos = len(nodos)
        self.segmentos_borde = self.obtener_segmentos_borde()
        valor_area = self.determinar_area_poligono()
        self.area = valor_area
        self.nodo_centroide = self.determinar_centroide()
        self.xg, self.yg = self.nodo_centroide.x, self.nodo_centroide.y
        # Se definen estos atributos para determinar si el elemento fue modificado por una interseccion (ver metodo)
        self.nodos_interseccion_lista = []
        self.numero_de_modificaciones = 0
        self.nodo_centroide_original = CopyObject(self.nodo_centroide)
        self.area_original = valor_area


    @staticmethod
    def ordenar_nodos_antihorario(nodos=None):
        if nodos is None:
            return None
        x_array = np.array([nodo.x for nodo in nodos])
        y_array = np.array([nodo.y for nodo in nodos])
        x0 = np.mean(x_array)
        y0 = np.mean(y_array)
        r = np.sqrt((x_array - x0) ** 2 + (y_array - y0) ** 2)

        angles = np.where((y_array - y0) > 0, np.arccos((x_array - x0) / r), 2 * np.pi - np.arccos((x_array - x0) / r))

        mask = np.argsort(angles)

        x_sorted = x_array[mask]
        y_sorted = y_array[mask]

        nodos_ordenados = []

        for i in range(len(x_sorted)):
            nodos_ordenados.append(Nodo(x_sorted[i], y_sorted[i]))
        return nodos_ordenados

    def obtener_segmentos_borde(self):
        i = 0
        imax = len(self.nodos_extremos)
        lista_de_segmentos = []
        while i < imax:
            nodo_1 = self.nodos_extremos[i]
            nodo_2 = self.nodos_extremos[i + 1] if i + 1 < imax else self.nodos_extremos[0]
            lista_de_segmentos.append(Segmento(nodo_1, nodo_2))
            i = i + 1
        return lista_de_segmentos

    def determinar_area_poligono(self):
        i = 0
        imax = len(self.nodos_extremos)
        area = 0
        while i < imax:
            nodo_1 = self.nodos_extremos[i]
            nodo_2 = self.nodos_extremos[i+1] if i+1 < imax else self.nodos_extremos[0]
            area = area + (nodo_1.x*nodo_2.y - nodo_2.x*nodo_1.y)
            i = i + 1
        return abs(area/2)

    def determinar_centroide(self):
        try:
            i = 0
            imax = len(self.nodos_extremos)
            cx, cy = 0, 0
            while i < imax:
                nodo_1 = self.nodos_extremos[i]
                nodo_2 = self.nodos_extremos[i+1] if i+1 < imax else self.nodos_extremos[0]
                cx = cx + (nodo_1.x+nodo_2.x)*(nodo_1.x*nodo_2.y-nodo_2.x*nodo_1.y)
                cy = cy + (nodo_1.y+nodo_2.y)*(nodo_1.x*nodo_2.y-nodo_2.x*nodo_1.y)
                i = i + 1
            return Nodo(cx/(6*self.area), cy/(6*self.area))
        except RuntimeWarning as e:
            print(e)

    def determinar_si_nodo_pertence_a_contorno(self, nodo_a_buscar: Nodo):
        for i, nodo in enumerate(self.nodos_extremos):
            nodo_1, nodo_2, nodo_3 = self.obtener_3_nodos_x_indice(i)
            recta = Recta(nodo_1, nodo_2)  # Recta definida por el nodo 1 y nodo 2.
            signo_semiplano_contorno = recta.ecuacion_recta(
                nodo_3)  # La ecuacion de la recta devuelve un número cuyo signo será el adecuado para los puntos que se encuentran en el mismo semiplano
            if signo_semiplano_contorno == 0:
                print("Por favor, ingresar puntos en el contorno que no esten alineados")
                return
            signo_semiplano_elemento = recta.ecuacion_recta(nodo_a_buscar)
            if signo_semiplano_contorno * signo_semiplano_elemento < 0:  # Si son de distinto signo descartar el elemento
                return False
        return True

    def determinar_si_nodo_pertence_a_contorno_sin_borde(self, nodo_a_buscar: Nodo):
        for i, nodo in enumerate(self.nodos_extremos):
            nodo_1, nodo_2, nodo_3 = self.obtener_3_nodos_x_indice(i)
            recta = Recta(nodo_1, nodo_2)  # Recta definida por el nodo 1 y nodo 2.
            signo_semiplano_contorno = recta.ecuacion_recta(
                nodo_3)  # La ecuacion de la recta devuelve un número cuyo signo será el adecuado para los puntos que se encuentran en el mismo semiplano
            if signo_semiplano_contorno == 0:
                print("Por favor, ingresar puntos en el contorno que no esten alineados")
                return
            signo_semiplano_elemento = recta.ecuacion_recta(nodo_a_buscar)
            if signo_semiplano_contorno * signo_semiplano_elemento <= 0:  # Si son de distinto signo descartar el elemento
                return False
        return True

    def obtener_3_nodos_x_indice(self, i_punto_1):
        """Obtiene el nodo en cuestión y los 2 nodos subsiguientes, basado en el índice del primer nodo.
        Al quedar algun índice fuera de rango, se obtiene el primer o segundo elemento según corresponda."""
        i_punto_2 = self.obtener_indice(i_punto_1, 1)
        i_punto_3 = self.obtener_indice(i_punto_1, 2)
        return self.nodos_extremos[i_punto_1], self.nodos_extremos[i_punto_2], self.nodos_extremos[i_punto_3]

    def obtener_indice(self, indice_punto_1, valor_a_sumar: int):
        i_punto = indice_punto_1 + valor_a_sumar
        return i_punto if i_punto < self.total_de_nodos else i_punto - self.total_de_nodos

    def cargar_poligono_para_mostrar(self, contorno_pos=True):
        lista_colores = ["r", "b", "g", "c", "m", "y", "k"]
        lista_espesores = [x/5 for x in range(10, 20)]
        colour = random.choice(lista_colores)
        espesor = random.choice(lista_espesores)
        for segmento in self.segmentos_borde:
            plt.plot([segmento.nodo_1.x, segmento.nodo_2.x], [segmento.nodo_1.y, segmento.nodo_2.y], c=colour, alpha=1,
                     linewidth=espesor)
        if contorno_pos:
            plt.scatter(self.xg, self.yg, c=colour, marker='+', s=200)
            plt.text(self.xg, self.yg, f"{self.numero_de_modificaciones}/ N{len(self.nodos_interseccion_lista)} ({self.xg:.2f}; {self.yg:.2f})\n{self.area}/{self.area_original}", fontdict=None)
            for nodo in self.nodos_interseccion_lista:
                plt.scatter(nodo.x, nodo.y, c=colour, marker='X', s=200, linewidths=0.005)

    def intersecar_con_elemento_negativo(self, otro_poligono):
        nodos_interseccion = self & otro_poligono
        if not nodos_interseccion:
            return self
        # Determinar que nodos de otro_poligono pertenecen a self
        for nodo in otro_poligono.nodos_extremos:
            if self.determinar_si_nodo_pertence_a_contorno_sin_borde(nodo):
                nodos_interseccion.append(nodo)
        for nodo_pos in self.nodos_extremos:
            if otro_poligono.determinar_si_nodo_pertence_a_contorno_sin_borde(nodo_pos):
                nodos_interseccion.append(nodo_pos)

        if len(nodos_interseccion) <= 2:
            return self

        pol_int = Poligono(nodos_interseccion)

        nueva_area = self.area - pol_int.area
        nueva_x, nueva_y = (self.area*self.xg - pol_int.area*pol_int.xg)/nueva_area, (self.area*self.yg - pol_int.area*pol_int.yg)/nueva_area

        self.numero_de_modificaciones = self.numero_de_modificaciones + 1

        self.area = nueva_area
        self.xg, self.yg = nueva_x, nueva_y
        self.nodo_centroide = Nodo(nueva_x, nueva_y)
        self.nodos_interseccion_lista = nodos_interseccion + self.nodos_interseccion_lista

    def __and__(self, otro_poligono):
        """Devuelve los nodos de intersección de dos poligonos"""
        coordenadas_interseccion = set()
        for segmento_contorno in self.segmentos_borde:
            for segmento_rectangulo in otro_poligono.segmentos_borde:
                interseccion = segmento_contorno & segmento_rectangulo
                if interseccion:
                    coordenadas_interseccion.add((interseccion.x, interseccion.y))
        return [Nodo(x[0], x[1]) for x in coordenadas_interseccion]

    def __lt__(self, poligono_mayor):
        centro_pertenece_a_contorno = poligono_mayor.determinar_si_nodo_pertence_a_contorno(self.nodo_centroide)
        if not centro_pertenece_a_contorno:
            return False
        intersecciones = poligono_mayor & self
        return True if not intersecciones else False


class RectanguloDiferencial(Poligono):
    def __init__(self, ubicacion_centro: Nodo, medidas: tuple):
        a, b = medidas
        self.lado_x, self.lado_y = a, b
        self.x_centro = ubicacion_centro.x
        self.y_centro = ubicacion_centro.y
        self.ubicacion_centro = ubicacion_centro
        self.medidas = medidas
        self.perimetro = 2*a + 2*b
        super().__init__(self.obtener_nodos_extremos())

    def determinar_area_poligono(self):
        return self.lado_x * self.lado_y

    def determinar_centroide(self):
        return self.ubicacion_centro

    def obtener_nodos_extremos(self):
        x, y = self.x_centro, self.y_centro
        a, b = self.lado_x, self.lado_y
        return Nodo(x + a / 2, y + b / 2), Nodo(x + a / 2, y - b / 2), Nodo(x - a / 2, y - b / 2), Nodo(x - a / 2, y + b / 2)

    def obtener_segmentos_borde(self):
        return (
            Segmento(self.nodos_extremos[0], self.nodos_extremos[1]),
            Segmento(self.nodos_extremos[1], self.nodos_extremos[2]),
            Segmento(self.nodos_extremos[2], self.nodos_extremos[3]),
            Segmento(self.nodos_extremos[3], self.nodos_extremos[0])
        )


class Contorno(Poligono):
    def __init__(self, nodos: list, signo: int):
        self.signo = signo
        super().__init__(nodos)

    def discretizar_contorno(self, dx, dy):
        lista_de_elementos = self.obtener_lista_de_elementos_preliminar(dx, dy)
        return self.eliminar_elementos_fuera_de_contorno(lista_de_elementos)

    def obtener_lista_de_elementos_preliminar(self, dx, dy):
        """Obtiene la lista de elementos preliminarmente del rectangulo que contiene al contorno, para luego eliminar
        los elementos restantes."""
        x_max, y_max = max(self.x), max(self.y)
        x_min, y_min = min(self.x), min(self.y)
        x = x_min + dx * 0.5
        y = y_min + dy * 0.5
        lista_de_elementos = []
        while y <= y_max:
            while x <= x_max:
                lista_de_elementos.append(RectanguloDiferencial(ubicacion_centro=Nodo(x, y), medidas=(dx, dy)))
                x = x + dx
            y = y + dy
            x = x_min + dx * 0.5
        return lista_de_elementos

    def eliminar_elementos_fuera_de_contorno(self, lista_de_elementos):
        for i, nodo in enumerate(self.nodos_extremos):
            nodo_1, nodo_2, nodo_3 = self.obtener_3_nodos_x_indice(i)
            recta = Recta(nodo_1, nodo_2) # Recta definida por el nodo 1 y nodo 2.
            signo_semiplano_contorno = recta.ecuacion_recta(nodo_3)  # La ecuacion de la recta devuelve un número cuyo signo será el adecuado para los puntos que se encuentran en el mismo semiplano
            if signo_semiplano_contorno == 0:
                print("Por favor, ingresar puntos en el contorno que no esten alineados")
                return
            for elemento_diferencial in lista_de_elementos.copy():
                signo_semiplano_elemento = recta.ecuacion_recta(elemento_diferencial.ubicacion_centro)
                if signo_semiplano_contorno * signo_semiplano_elemento < 0:  # Si son de distinto signo, descartar el elemento
                    lista_de_elementos.remove(elemento_diferencial)
        return lista_de_elementos

    def mostrar_contorno_y_discretizacion(self, EEH):
        # Contorno
        X = [nodo.x for nodo in self.nodos_extremos]
        Y = [nodo.y for nodo in self.nodos_extremos]
        plt.plot(X, Y)
        x = [Elemento.x for Elemento in EEH]
        y = [Elemento.y for Elemento in EEH]
        plt.scatter(x, y, color="r", s=2, label="Discretizacion")
        plt.show()


class SeccionGenerica(object):
    def __init__(self, contornos: dict, dx, dy):
        self.dx, self.dy = dx, dy
        self.contornos_negativos = [contorno for indice_contorno, contorno in contornos.items() if contorno.signo == -1]
        self.contornos_positivos = [contorno for indice_contorno, contorno in contornos.items() if contorno.signo == 1]
        self.elementos = self.obtener_matriz_elementos_positivos()

    def obtener_matriz_elementos_positivos(self):
        result = []
        for contorno_positivo in self.contornos_positivos:
            lista_elementos_positivos = contorno_positivo.discretizar_contorno(self.dx, self.dy)
            for elemento_positivo in lista_elementos_positivos:
                if self.elemento_pertenece_a_contorno_negativo(elemento_positivo):
                    continue  # Descartar elemento
                result.append(self.obtener_interseccion_elemento_positivo_con_negativo(elemento_positivo))
        return result

    def elemento_pertenece_a_contorno_negativo(self, elemento_positivo: Poligono):
        for contorno_negativo in self.contornos_negativos:
            if elemento_positivo < contorno_negativo:
                return True
        return False

    def obtener_interseccion_elemento_positivo_con_negativo(self, elemento_positivo):
        for contorno_neg in self.contornos_negativos:
            elemento_positivo.intersecar_con_elemento_negativo(contorno_neg)
        return elemento_positivo

    def mostrar_seccion(self):
        for contorno_negativo in self.contornos_negativos:
            contorno_negativo.cargar_poligono_para_mostrar(contorno_pos=False)
        for elemento in self.elementos:
            elemento.cargar_poligono_para_mostrar()
        plt.show()