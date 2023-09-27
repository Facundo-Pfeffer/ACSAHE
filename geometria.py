import random
import matplotlib.pyplot as plt
import numpy as np
import math
import copy
from typing import List
from matplotlib.patches import Arc
from plotly_util import PlotlyUtil

tolerancia = 10 ** -13
lista_colores = ["r", "b", "g", "c", "m", "y", "k"]
lista_espesores = [x / 5 for x in range(10, 20)]


class Nodo(object):
    def __init__(self, x: (int, float), y: (int, float)):
        self.x = x
        self.y = y

    def __eq__(self, otro_nodo):  # Determinar si dos puntos son iguales, bajo el valor de tolerancia
        return self.x - tolerancia <= otro_nodo.x <= self.x + tolerancia and self.y - tolerancia <= otro_nodo.y <= self.y + tolerancia


class ListaDeNodos(object):
    """Objeto que alberga una lista de elementos de clase Nodo."""

    def __init__(self, lista_nodos):
        self.lista_nodos = lista_nodos

    def eliminar_duplicados(self):
        resultado = [self.lista_nodos[0]]
        for nodo in self.lista_nodos[1:]:
            if not any(nodo == nodo_b for nodo_b in resultado):
                resultado.append(nodo)
        return resultado


class Segmento(object):
    """Segmento en dos dimensiones definido a partir de 2 Nodos de paso."""

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
        xmin, xmax = self.extremos_x
        ymin, ymax = self.extremos_y
        return xmin - tolerancia <= nodo.x <= xmax + tolerancia and ymin - tolerancia <= nodo.y <= ymax + tolerancia

    def determinar_si_nodo_pertenece_a_segmento(self, nodo):
        return self.recta_segmento.ecuacion_recta(nodo) == 0 and self.determinar_si_nodo_esta_en_rango(nodo)

    def extremos_segmento(self):
        extramos_x = (min(self.nodo_1.x, self.nodo_2.x), max(self.nodo_1.x, self.nodo_2.x))
        extramos_y = (min(self.nodo_1.y, self.nodo_2.y), max(self.nodo_1.y, self.nodo_2.y))
        return extramos_x, extramos_y

    def obtener_interseccion_recta(self, recta):
        nodo_interseccion_rectas = recta & self.recta_segmento
        if not nodo_interseccion_rectas:  # Paralelas
            return None
        resultado = nodo_interseccion_rectas if self.determinar_si_nodo_esta_en_rango(
            nodo_interseccion_rectas) else None
        return resultado

    def plot(self, ax=None, **kwargs):
        if ax is None:
            plt.plot([self.nodo_1.x, self.nodo_2.x], [self.nodo_1.y, self.nodo_2.y], **kwargs)
        else:
            ax.plot([self.nodo_1.x, self.nodo_2.x], [self.nodo_1.y, self.nodo_2.y], **kwargs)

    def __and__(self, otro_segmento):
        result = self.recta_segmento & otro_segmento.recta_segmento  # Buscando interseccion
        if not result:
            return None
        return result if self.determinar_si_nodo_esta_en_rango(
            result) and otro_segmento.determinar_si_nodo_esta_en_rango(result) else None


class Recta(object):
    def __init__(self, nodo_1: Nodo, nodo_2: Nodo):
        self.nodo_1 = nodo_1
        self.nodo_2 = nodo_2
        a, b, c = self.obtener_parametros_ecuacion_implicita(nodo_1, nodo_2)
        self.ecuacion_recta = lambda nodo: a * nodo.x + b * nodo.y + c

        # Definición de métodos a ser usados.
        self.distancia_a_nodo = lambda nodo: (a * nodo.x + b * nodo.y + c) / ((a ** 2 + b ** 2) ** 0.5)
        self.distancia_a_nodo_v = lambda nodo: abs(nodo.y + (c + a * nodo.x) / b) if b != 0 else None
        self.distancia_a_nodo_h = lambda nodo: abs(nodo.x + (c + b * nodo.y) / a) if a != 0 else None

        # Distancia en Vertical y Horizontal, respectivamente.
        self.y = lambda x: -c / b - a / b * x
        self.x = lambda y: -c / a - b / a * y

    @staticmethod
    def obtener_parametros_ecuacion_implicita(nodo_1, nodo_2):
        """Obtiene los parámetros a, b y c de una recta, de manera de describir
        la ecuación de la misma en el plano de la forma a*x+b*y*c (tipo cartesiana o implícita)"""
        x1, y1 = nodo_1.x, nodo_1.y
        x2, y2 = nodo_2.x, nodo_2.y
        a = y1 - y2
        b = x2 - x1
        c = y2 * (x1 - x2) + (y2 - y1) * x2
        return a, b, c

    def mostrar_recta(self):
        plt.plot([self.nodo_1.x, self.nodo_2.x], [self.nodo_1.y, self.nodo_2.y])

    def __and__(self, otra_recta) -> Nodo or None:
        """Realiza la intersección de la recta con otra provista, en el plano.
        :param otra_recta: recta a intersectar.
        :return Nodo de intersección or None si no se encuentran"""
        x1, y1, x2, y2 = self.nodo_1.x, self.nodo_1.y, self.nodo_2.x, self.nodo_2.y
        x3, y3, x4, y4 = otra_recta.nodo_1.x, otra_recta.nodo_1.y, otra_recta.nodo_2.x, otra_recta.nodo_2.y
        det = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)  # Determinante de la matriz de coordenadas
        if -1 * tolerancia <= det <= tolerancia:  # Cuando den tiende a 0, las rectas son paralelas, no hay intersección.
            return None
        # Se aplica la fórmula de Cramer para resolver el sistema de ecuaciones lineal.
        x = ((x1 * y2 - y1 * x2) * (x3 - x4) - (x1 - x2) * (x3 * y4 - y3 * x4)) / det
        y = ((x1 * y2 - y1 * x2) * (y3 - y4) - (y1 - y2) * (x3 * y4 - y3 * x4)) / det
        return Nodo(x, y)


class Poligono(object):
    """Polígono CONVEXO en el plano, formado por una serie de nodos."""

    def __init__(self, nodos: List[Nodo], ordenar: bool = False):
        """
        :param nodos: lista de nodos que definen el contorno del polígono.
        :param ordenar: define si la lista de nodos anterior debe ser ordenada en sentido antihorario, siendo dicho
         sentido el convencional para el programa."""

        self.nodos_extremos = nodos if not ordenar else self.ordenar_nodos_poligono_convexo_antihorario(nodos)
        self.x = [nodo.x for nodo in self.nodos_extremos]
        self.y = [nodo.y for nodo in self.nodos_extremos]
        self.total_de_nodos = len(nodos)
        self.segmentos_borde = self.obtener_segmentos_borde()
        valor_area = self.determinar_area_poligono()
        self.area = valor_area
        self.nodo_centroide = self.determinar_centroide()
        self.xg, self.yg = self.nodo_centroide.x, self.nodo_centroide.y
        # Se definen estos atributos para determinar si el elemento fue modificado por una intersección (ver método)
        self.nodos_interseccion_lista = []
        self.numero_de_modificaciones = 0
        self.nodo_centroide_original = copy.copy(self.nodo_centroide)
        self.area_original = valor_area

    @staticmethod
    def ordenar_nodos_poligono_convexo_antihorario(nodos=None):
        """Ordena los nodos en sentido antihorario, cuando el polígono SEA CONVEXO."""
        if nodos is None:
            return None
        x_array = np.array([nodo.x for nodo in nodos])
        y_array = np.array([nodo.y for nodo in nodos])

        # Coordenadas del centroide
        x0 = np.mean(x_array)
        y0 = np.mean(y_array)

        # Calcular las distancias desde el centroide a cada nodo
        r = np.sqrt((x_array - x0) ** 2 + (y_array - y0) ** 2)
        # Calcula el ángulo antihorario con respecto al eje x de cada punto, y ordena en base al mismo.
        angulos = np.where((y_array - y0) > 0, np.arccos((x_array - x0) / r), 2 * np.pi - np.arccos((x_array - x0) / r))
        mask = np.argsort(angulos)
        x_sorted = x_array[mask]
        y_sorted = y_array[mask]

        nodos_ordenados = []
        for i in range(len(x_sorted)):
            nodos_ordenados.append(Nodo(x_sorted[i], y_sorted[i]))
        return nodos_ordenados

    def obtener_segmentos_borde(self):
        """A partir de los nodos que fueron ingresados, obtiene la lista de segmentos de borde."""
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
            nodo_2 = self.nodos_extremos[i + 1] if i + 1 < imax else self.nodos_extremos[0]
            area = area + (nodo_1.x * nodo_2.y - nodo_2.x * nodo_1.y)
            i = i + 1
        return abs(area / 2)

    def determinar_centroide(self):
        try:
            i = 0
            imax = len(self.nodos_extremos)
            cx, cy = 0, 0
            while i < imax:
                nodo_1 = self.nodos_extremos[i]
                nodo_2 = self.nodos_extremos[i + 1] if i + 1 < imax else self.nodos_extremos[0]
                cx = cx + (nodo_1.x + nodo_2.x) * (nodo_1.x * nodo_2.y - nodo_2.x * nodo_1.y)
                cy = cy + (nodo_1.y + nodo_2.y) * (nodo_1.x * nodo_2.y - nodo_2.x * nodo_1.y)
                i = i + 1
            return Nodo(cx / (6 * self.area), cy / (6 * self.area))
        except RuntimeWarning as e:
            print(e)

    def determinar_si_nodo_pertence_a_contorno(self, nodo_a_buscar: Nodo):
        """Devuelve verdadero si el nodo se encuentra dentro del contorno, sin incluir los bordes del mismo."""
        for i, nodo in enumerate(self.nodos_extremos):
            nodo_1, nodo_2, nodo_3 = self.obtener_3_nodos_x_indice(i)
            recta = Recta(nodo_1, nodo_2)  # Recta definida por el nodo 1 y nodo 2.
            # La ecuación de la recta devolverá valores del mismo signo para puntos del mismo semiplano.
            signo_semiplano_contorno = recta.ecuacion_recta(nodo_3)
            if signo_semiplano_contorno == 0:
                raise Exception(f"Error de Ingreso de datos: Ingresar puntos en el contorno que no estén alineados", )
            signo_semiplano_elemento = recta.ecuacion_recta(nodo_a_buscar)
            if signo_semiplano_contorno * signo_semiplano_elemento < 0:  # Si son de distinto signo, no pertenece.
                return False
        return True

    def determinar_si_nodo_pertence_a_contorno_sin_borde(self, nodo_a_buscar: Nodo):
        """Devuelve verdadero si el nodo se encuentra dentro del contorno, incluyendo los bordes del mismo."""
        for i, nodo in enumerate(self.nodos_extremos):
            nodo_1, nodo_2, nodo_3 = self.obtener_3_nodos_x_indice(i)
            recta = Recta(nodo_1, nodo_2)  # Recta definida por el nodo 1 y nodo 2.
            # La ecuación de la recta devolverá valores del mismo signo para puntos del mismo semiplano.
            signo_semiplano_contorno = recta.ecuacion_recta(nodo_3)
            if signo_semiplano_contorno == 0:
                raise Exception("Error de Ingreso de datos: Ingresar puntos en el contorno que no estén alineados.")
            signo_semiplano_elemento = recta.ecuacion_recta(nodo_a_buscar)
            if signo_semiplano_contorno * signo_semiplano_elemento <= 0:  # Si son de distinto signo, no pertenece.
                return False
        return True

    def obtener_3_nodos_x_indice(self, i_punto_1):
        """
        Obtiene el nodo en cuestión y los 2 nodos subsiguientes, basado en el índice del primer nodo.
        Al quedar algún índice fuera de rango, se obtiene el primer o segundo elemento según corresponda."""
        i_punto_2 = self.obtener_indice(i_punto_1, 1)
        i_punto_3 = self.obtener_indice(i_punto_1, 2)
        return self.nodos_extremos[i_punto_1], self.nodos_extremos[i_punto_2], self.nodos_extremos[i_punto_3]

    def obtener_indice(self, indice_punto_1, valor_a_sumar: int):
        """Obtiene el índice del próximo elemento, dependiendo de valor_a_sumar"""
        i_punto = indice_punto_1 + valor_a_sumar
        return i_punto if i_punto < self.total_de_nodos else i_punto - self.total_de_nodos

    def plot(self, indice_color=None,
             espesor=None,
             mostrar_centroide=False,
             texto_a_mostrar=None,
             tridimensional=False,
             ec_plano_3d=None,
             plt_3d=None,
             transparencia=1,
             ax=None):

        color = random.choice(lista_colores) if indice_color is None else lista_colores[indice_color]
        espesor = random.choice(lista_espesores) if espesor is None else espesor
        x = []
        y = []
        for segmento in self.segmentos_borde:
            x.extend([segmento.nodo_1.x, segmento.nodo_2.x])
            y.extend([segmento.nodo_1.y, segmento.nodo_2.y])

        if not tridimensional:
            plt.plot(x, y, c=color, alpha=transparencia, linewidth=espesor, zorder=0)
        else:  # Figura 3d
            z1 = [0] * len(x)
            z2 = [ec_plano_3d(x[i], y[i]) for i in range(len(x))]
            x = x * 2
            y = y * 2
            z = z1 + z2
            for i in range(len(x) - 1):
                x0, y0, z0 = [x[i], x[i + 1]], [y[i], y[i + 1]], [z[i], z[i + 1]]
                plt_3d.plot(z0, x0, y0,
                            c=color if i != len(x) / 2 - 1 else "w",
                            alpha=transparencia, linewidth=espesor, zorder=0)

        if mostrar_centroide:
            plt.scatter(self.xg, self.yg, c=color, marker=".", zorder=0)
        if texto_a_mostrar:
            plt.text(self.xg, self.yg, texto_a_mostrar)

    def obtener_poligono_interseccion(self, otro_poligono):
        """Obtiene el poligono que resulta de intersectar self con otro_poligono"""
        lista_nodos_interseccion = self & otro_poligono
        if not lista_nodos_interseccion:
            return self
        # Determinar que nodos de otro_poligono pertenecen a self
        for nodo in otro_poligono.nodos_extremos:
            if self.determinar_si_nodo_pertence_a_contorno_sin_borde(nodo):
                lista_nodos_interseccion.append(nodo)
        for nodo_pos in self.nodos_extremos:  # Determinar que nodos de self pertenecen a otro_poligono
            if otro_poligono.determinar_si_nodo_pertence_a_contorno_sin_borde(nodo_pos):
                lista_nodos_interseccion.append(nodo_pos)
        if len(lista_nodos_interseccion) <= 2:
            return self
        lista_nodos_interseccion = ListaDeNodos(lista_nodos_interseccion).eliminar_duplicados()
        return Poligono(lista_nodos_interseccion, ordenar=True)

    def restar_con_otro_poligono(self, otro_poligono):
        """Resta al elemento self el complemento con otro_poligono.
        :param otro_poligono: polígono que se le restará a self.
        :return el mismo elemento self, pero modificado por la resta."""

        lista_de_nodos_de_interseccion = self.obtener_nodos_compartidos_entre_poligonos(self, otro_poligono)

        if len(lista_de_nodos_de_interseccion) <= 2:
            return self

        poligono_interno = Poligono(lista_de_nodos_de_interseccion, ordenar=True)

        if self.area_y_centro_son_iguales(poligono_1=self, poligono_2=poligono_interno):
            # Si la interseccion es igual al mismo poligono, será eliminado.
            return None

        nueva_area = self.area - poligono_interno.area
        nueva_x = (self.area * self.xg - poligono_interno.area * poligono_interno.xg) / nueva_area
        nueva_y = (self.area * self.yg - poligono_interno.area * poligono_interno.yg) / nueva_area

        if not self.nuevo_poligono_es_valido(nueva_area, nueva_x, nueva_y):
            return None
        self.numero_de_modificaciones = self.numero_de_modificaciones + 1

        self.area = nueva_area
        self.xg, self.yg = nueva_x, nueva_y
        self.nodo_centroide = Nodo(nueva_x, nueva_y)
        self.nodos_interseccion_lista = lista_de_nodos_de_interseccion + self.nodos_interseccion_lista
        return self  # self modificado

    @staticmethod
    def nuevo_poligono_es_valido(nueva_area, nueva_x, nueva_y):  # Criterio: área=0|nodo en infinito numérico.
        return not (-tolerancia <= nueva_area <= tolerancia or nueva_x == float("inf") or nueva_y == float("inf"))

    @staticmethod
    def obtener_nodos_compartidos_entre_poligonos(poligono_1, poligono_2):
        """Devuelve una lista de:
        Aquellos nodos que intersectan alguno de los bordes entre los polígonos
        Los nodos de poligono_1 que se encuentran dentro de poligono_2, y viceversa."""

        lista_nodos_interseccion = poligono_1 & poligono_2  # Intersección de bordes
        if not lista_nodos_interseccion:  # no hay intersección
            return []

        for nodo in poligono_2.nodos_extremos:  # Determinar qué nodos de otro_poligono pertenecen a self
            if poligono_1.determinar_si_nodo_pertence_a_contorno_sin_borde(nodo):
                lista_nodos_interseccion.append(nodo)
        for nodo_pos in poligono_1.nodos_extremos:  # Determinar qué nodos de self pertenecen a otro_poligono
            if poligono_2.determinar_si_nodo_pertence_a_contorno_sin_borde(nodo_pos):
                lista_nodos_interseccion.append(nodo_pos)
        nodos_interseccion = ListaDeNodos(lista_nodos_interseccion).eliminar_duplicados()
        return nodos_interseccion

    def __and__(self, otro_poligono):
        """Devuelve los nodos de interseccion de dos poligonos"""
        lista_nodos_interseccion = []
        for segmento_contorno in self.segmentos_borde:
            for segmento_rectangulo in otro_poligono.segmentos_borde:
                interseccion = segmento_contorno & segmento_rectangulo
                if interseccion:
                    nodo_interseccion = Nodo(interseccion.x, interseccion.y)
                    if not (any(nodo_interseccion == nodo_x for nodo_x in lista_nodos_interseccion)):
                        lista_nodos_interseccion.append(nodo_interseccion)
        return lista_nodos_interseccion or None

    def __lt__(self, poligono_mayor):
        """Determina si self esta contenido dentro de poligono mayor"""
        centro_pertenece_a_contorno = poligono_mayor.determinar_si_nodo_pertence_a_contorno(self.nodo_centroide)
        if not centro_pertenece_a_contorno:
            return False
        intersecciones = poligono_mayor & self
        return True if not intersecciones else False

    @staticmethod
    def area_y_centro_son_iguales(poligono_1, poligono_2):
        """Valida si dos poligonos son iguales"""
        return poligono_2.area - tolerancia <= poligono_1.area <= poligono_2.area + tolerancia and \
            poligono_2.xg - tolerancia <= poligono_1.xg <= poligono_2.xg + tolerancia and \
            poligono_2.yg - tolerancia <= poligono_1.yg <= poligono_2.yg + tolerancia

    def desplazar_sistema_de_referencia(self, desp_x, desp_y):
        self.xg = self.xg + desp_x
        self.yg = self.yg + desp_y
        # Para que se muestre la discretización correctamente
        for nodo_extremo in self.nodos_extremos:
            nodo_extremo.x = nodo_extremo.x + desp_x
            nodo_extremo.y = nodo_extremo.y + desp_y
        self.segmentos_borde = self.obtener_segmentos_borde()


class ElementoRectangular(Poligono):
    """El elemento finito que compone a un Polígono mayor.
     Al estar formado por 4 nodos compone en sí un Polígono."""

    def __init__(self, ubicacion_centro: Nodo, medidas: tuple):
        a, b = medidas
        self.lado_x, self.lado_y = a, b
        self.x_centro = ubicacion_centro.x
        self.y_centro = ubicacion_centro.y
        self.ubicacion_centro = ubicacion_centro
        self.medidas = medidas
        self.perimetro = 2 * a + 2 * b
        super().__init__(self.obtener_nodos_extremos())

    def determinar_area_poligono(self):
        return self.lado_x * self.lado_y

    def determinar_centroide(self):
        return self.ubicacion_centro

    def obtener_nodos_extremos(self):
        x, y = self.x_centro, self.y_centro
        a, b = self.lado_x, self.lado_y
        return Nodo(x + a / 2, y + b / 2), Nodo(x + a / 2, y - b / 2), Nodo(x - a / 2, y - b / 2), Nodo(x - a / 2,
                                                                                                        y + b / 2)

    def obtener_segmentos_borde(self):
        return (
            Segmento(self.nodos_extremos[0], self.nodos_extremos[1]),
            Segmento(self.nodos_extremos[1], self.nodos_extremos[2]),
            Segmento(self.nodos_extremos[2], self.nodos_extremos[3]),
            Segmento(self.nodos_extremos[3], self.nodos_extremos[0])
        )


class ElementoTrapecioCircular():
    def __init__(self, nodo_centro: Nodo, radios: tuple, angulos):
        self.area = math.radians(angulos[1] - angulos[0]) * (radios[1] ** 2 - radios[0] ** 2) / 2
        angulo_medio = math.radians(angulos[1] + angulos[0]) / 2

        self.angulo_inicial, self.angulo_final = min(angulos), max(angulos)
        self.radio_interno, self.radio_externo = min(radios), max(radios)
        self.nodo_centro = nodo_centro
        self.xc = nodo_centro.x
        self.yc = nodo_centro.y

        theta = math.radians(self.angulo_final - self.angulo_inicial) / 2

        # El centroide de un sector circular se define como 2R sin(θ)/(3θ); siendo R el radio y θ la apertura del sector
        area_1 = math.radians(self.angulo_final - self.angulo_inicial) * (self.radio_externo ** 2) / 2
        area_2 = math.radians(self.angulo_final - self.angulo_inicial) * (self.radio_interno ** 2) / 2
        radio_al_centroide = 2 * math.sin(theta) / (3 * theta) * (
                    self.radio_externo * area_1 - self.radio_interno * area_2) / self.area
        self.xg = math.cos(angulo_medio) * radio_al_centroide + self.xc
        self.yg = math.sin(angulo_medio) * radio_al_centroide + self.yc

        self.nodos_extremos = self.obtener_nodos_extremos()
        self.segmentos_rectos = self.obtener_segmentos_rectos()

    def obtener_nodos_extremos(self):
        resultado = []
        if self.radio_interno == 0:  # Circulo
            return []
        for theta in [self.angulo_inicial, self.angulo_final]:
            for r in [self.radio_interno, self.radio_externo]:
                resultado.append(
                    Nodo(self.xc + r * math.cos(math.radians(theta)), self.yc + r * math.sin(math.radians(theta))))
        return resultado

    def obtener_segmentos_rectos(self):
        if len(self.nodos_extremos) == 0:
            return None
        return (
            Segmento(self.nodos_extremos[0], self.nodos_extremos[1]),
            Segmento(self.nodos_extremos[2], self.nodos_extremos[3])
        )

    def nodo_en_elemento(self, nodo: Nodo):
        xc, yc = nodo.x - self.nodo_centro.x, nodo.y - self.nodo_centro.y
        angulo = math.atan2(yc, xc)
        angulo = angulo + 360 if angulo < 0 else angulo  # Sumar 360 para convertir a ángulo con respecto a x.
        radio = math.sqrt(xc ** 2 + yc ** 2)
        return self.angulo_inicial <= angulo <= self.angulo_final and self.radio_interno <= radio <= self.radio_externo

    def desplazar_sistema_de_referencia(self, desp_x, desp_y):
        self.xg = self.xg + desp_x
        self.xc = self.xc + desp_x
        self.yg = self.yg + desp_y
        self.yc = self.yc + desp_y
        self.nodo_centro = Nodo(self.xc, self.yc)
        self.nodos_extremos = self.obtener_nodos_extremos()
        self.segmentos_rectos = self.obtener_segmentos_rectos()

    def plot(self, indice_color, espesor, ax, mostrar_centroide=False, transparencia=1):
        # Coordenadas de los puntos del trapecio circular
        color = random.choice(lista_colores) if indice_color is None else lista_colores[indice_color]
        espesor = random.choice(lista_espesores) if espesor is None else espesor
        style_data = {"color": color, "linewidth": espesor, "alpha": transparencia}

        arco_externo = Arc((self.xc, self.yc),
                           2 * self.radio_externo,
                           2 * self.radio_externo,
                           theta1=self.angulo_inicial,
                           theta2=self.angulo_final,
                           **style_data)
        if self.radio_interno > 0:
            arco_interno = Arc((self.xc, self.yc),
                               2 * self.radio_interno,
                               2 * self.radio_interno,
                               theta1=self.angulo_inicial,
                               theta2=self.angulo_final,
                               **style_data)
            ax.add_patch(arco_interno)

        ax.add_patch(arco_externo)
        if self.segmentos_rectos is not None:
            self.segmentos_rectos[0].plot(ax, **style_data)
            self.segmentos_rectos[1].plot(ax, **style_data)
        if mostrar_centroide:
            plt.scatter(self.xg, self.yg, c=color, marker=".", zorder=0)
        return ax
        # Crear la figura y el gráfico


class ContornoCircular(ElementoTrapecioCircular):
    tipo = "Circular"

    def __init__(self, nodo_centro: Nodo, indice, radios: tuple, angulos: tuple = (0, 360), signo=1):
        self.signo = signo
        super().__init__(nodo_centro, radios, angulos)

    def discretizar_contorno(self, discretizacion_angulo, discretizacion_radio):
        """Define la lista de elementos tipo ElementoRectangular que se encuentran dentro del contorno."""
        n = discretizacion_radio
        funcion_radios = lambda i: self.radio_interno + (self.radio_externo - self.radio_interno) * (
                    1 - (1 - i / n) ** 1.25)

        resultado = []
        radio = self.radio_interno
        radio_final = funcion_radios(1)
        i_inicial = 0

        if self.radio_interno == 0:  # Sector central circular
            resultado.append(ElementoTrapecioCircular(
                nodo_centro=self.nodo_centro,
                angulos=(self.angulo_inicial, self.angulo_final),
                radios=(radio, radio_final / 2)))
            angulo = self.angulo_inicial
            while angulo <= self.angulo_final - discretizacion_angulo:
                resultado.append(ElementoTrapecioCircular(
                    nodo_centro=self.nodo_centro,
                    angulos=(angulo, angulo + discretizacion_angulo),
                    radios=(radio_final / 2, radio_final)))
                angulo = angulo + discretizacion_angulo
            i_inicial = i_inicial + 1

        for i_radios in range(i_inicial, n):
            radio = funcion_radios(i_radios)
            radio_final = funcion_radios(i_radios + 1)
            angulo = self.angulo_inicial
            while angulo <= self.angulo_final - discretizacion_angulo:
                resultado.append(ElementoTrapecioCircular(
                    nodo_centro=self.nodo_centro,
                    angulos=(angulo, angulo + discretizacion_angulo),
                    radios=(radio, radio_final)))
                angulo = angulo + discretizacion_angulo
        return resultado

    def eliminar_elementos_fuera_de_contorno(self, lista_de_elementos):
        """Elimina aquellos elementos definidos preliminarmente que finalmente se encuentran por fuera del contorno."""
        for elemento_diferencial in lista_de_elementos.copy():
            if not self.nodo_en_elemento(elemento_diferencial.nodo_centroide):  # Fuera del semiplano del contorno.
                lista_de_elementos.remove(elemento_diferencial)
        return lista_de_elementos

    def mostrar_contorno_y_discretizacion(self, lista_elementos):
        # Contorno
        fig, ax = plt.subplots()
        for elemento in lista_elementos:
            elemento.plot(ax)
        plt.show()


class Contorno(Poligono):
    """Un contorno es un polígono el cual podrá ser discretizado en elementos tipo ElementoRectangular.
    Además, el atributo signo lleva asignado un significado:
    signo = -1; negativo implica que el contorno es un agujero en la sección final.
    signo = 1; por el contrario, positivo es un contorno con elementos que aportarán a la solución final."""
    tipo = "Poligonal"

    def __init__(self, nodos: list, signo: int, indice, ordenar=False):
        self.signo = signo
        self.indice = indice
        super().__init__(nodos, ordenar=ordenar)

    def discretizar_contorno(self, dx, dy):
        """Define la lista de elementos tipo ElementoRectangular que se encuentran dentro del contorno."""
        lista_de_elementos = self.obtener_lista_de_elementos_preliminar(dx, dy)
        lista_de_elementos.sort(key=lambda elemento: (elemento.y, elemento.x))
        # Elementos con coordenadas no válidas deben ser limpiados
        lista_elem_validos = [elem for elem in lista_de_elementos if not (math.isnan(elem.xg) or math.isnan(elem.yg))]
        return self.eliminar_elementos_fuera_de_contorno(
            lista_elem_validos)  # Limpieza adicional de elementos no validos.

    def obtener_lista_de_elementos_preliminar(self, dx, dy):
        """Obtiene la lista de elementos preliminarmente del rectángulo mayor que contiene al contorno, para luego
         eliminar los restantes."""
        lista_de_elementos = []
        lista_de_direcciones = [(1, 1), (1, -1), (-1, -1), (-1, 1)]
        for direccion in lista_de_direcciones:
            x_partida = self.xg + direccion[0] * dx / 2
            y_partida = self.yg + direccion[1] * dy / 2
            lista_de_elementos = lista_de_elementos + self.elementos_segun_direccion(x_partida, y_partida, dx, dy,
                                                                                     direccion)
        return lista_de_elementos

    def elementos_segun_direccion(self, x_partida, y_partida, dx, dy, direccion: tuple):
        """La direccion de avance viene dada por una tupla tipo (±1; ±1), el primer término indicando si es positivo
        en X y el segundo si lo es en Y."""
        x_max, y_max = max(self.x), max(self.y)
        x_min, y_min = min(self.x), min(self.y)
        lista_de_elementos = []
        condicion_y = lambda yp: yp - dy / 2 < y_max if direccion[1] == 1 else yp + dy / 2 > y_min
        condicion_x = lambda xp: xp - dx / 2 < x_max if direccion[0] == 1 else xp + dx / 2 > x_min
        x = x_partida
        y = y_partida
        while condicion_y(y):
            while condicion_x(x):
                rectangulo_diferencial = ElementoRectangular(ubicacion_centro=Nodo(x, y), medidas=(dx, dy))
                rectangulo_diferencial = rectangulo_diferencial.obtener_poligono_interseccion(
                    self)  # recortando con bordes de contorno
                lista_de_elementos.append(rectangulo_diferencial)
                x = x + direccion[0] * dx
            y = y + direccion[1] * dy
            x = x_partida
        return lista_de_elementos

    def eliminar_elementos_fuera_de_contorno(self, lista_de_elementos):
        """Elimina aquellos elementos definidos preliminarmente que finalmente se encuentran por fuera del contorno."""
        for i, nodo in enumerate(self.nodos_extremos):
            nodo_1, nodo_2, nodo_3 = self.obtener_3_nodos_x_indice(i)
            recta = Recta(nodo_1, nodo_2)  # Recta definida por el nodo 1 y 2.
            # La ecuación de la recta devuelve números del mismo signos para puntos en el mismo semiplano
            signo_semiplano_contorno = recta.ecuacion_recta(nodo_3)
            if signo_semiplano_contorno == 0:
                raise Exception(
                    f"Por favor, ingresar puntos en el contorno que no estén alineados. Contorno: {self.indice}")
            for elemento_diferencial in lista_de_elementos.copy():
                signo_semiplano_elemento = recta.ecuacion_recta(elemento_diferencial.nodo_centroide)
                if signo_semiplano_contorno * signo_semiplano_elemento < 0:  # Fuera del semiplano del contorno.
                    lista_de_elementos.remove(elemento_diferencial)
        return lista_de_elementos

    def mostrar_contorno_y_discretizacion(self, lista_elementos):
        # Contorno
        X = [nodo.x for nodo in self.nodos_extremos]
        Y = [nodo.y for nodo in self.nodos_extremos]
        plt.plot(X, Y)
        for elemento in lista_elementos:
            elemento.plot(indice_color=0, espesor=0.5)
        self.plot(indice_color=1)
        plt.title("Contorno y Discretizacion - pre eliminar elementos negativos")
        plt.show()


class SeccionArbitraria(object):
    """Una Sección Genérica será la combinación de objetos tipo Contorno, dando el resultante dependiendo del signo,
    de los mismos."""

    def __init__(self, contornos: dict, dx, dy):
        self.dx, self.dy = dx, dy
        self.contornos_negativos = [contorno for indice_contorno, contorno in contornos.items() if contorno.signo == -1]
        self.contornos_positivos = [contorno for indice_contorno, contorno in contornos.items() if contorno.signo == 1]
        self.elementos = self.obtener_matriz_elementos_positivos()
        self.area, self.xg, self.yg = self.obtener_baricentro_y_area()
        self.cambiar_coordenadas_a_baricentro()
        self.x_min = min(x.xg for x in self.elementos)
        self.x_max = max(x.xg for x in self.elementos)
        self.y_min = min(x.yg for x in self.elementos)
        self.y_max = max(x.yg for x in self.elementos)

    def obtener_matriz_elementos_positivos(self):
        result = []
        for contorno_positivo in self.contornos_positivos:
            if contorno_positivo.tipo == "Poligonal":
                lista_elementos_positivos = contorno_positivo.discretizar_contorno(self.dx, self.dy)
            else:
                lista_elementos_positivos = contorno_positivo.discretizar_contorno(discretizacion_angulo=5,
                                                                                   discretizacion_radio=50)
            for elemento_positivo in lista_elementos_positivos:
                if self.elemento_pertenece_a_contorno_negativo(elemento_positivo):
                    continue  # Descartar elemento
                elemento_intersectado = self.obtener_interseccion_elemento_positivo_con_negativo(elemento_positivo)
                if elemento_intersectado:
                    result.append(elemento_intersectado)
        return result

    def elemento_pertenece_a_contorno_negativo(self, elemento_positivo: Poligono):
        for contorno_negativo in self.contornos_negativos:
            if elemento_positivo < contorno_negativo:  # Pertenece COMPLETAMENTE a elemento
                return True
        return False

    def obtener_interseccion_elemento_positivo_con_negativo(self, elemento_positivo):
        for contorno_neg in self.contornos_negativos:
            elemento_positivo = elemento_positivo.restar_con_otro_poligono(contorno_neg)
            if elemento_positivo is None:
                return None
        return elemento_positivo

    def mostrar_contornos_2d(self, ax):
        for contorno_negativo in self.contornos_negativos:
            contorno_negativo.plot(indice_color=2, espesor=2, ax=ax)
        for contorno_positivo in self.contornos_positivos:
            contorno_positivo.plot(ax=ax, indice_color=2, espesor=2)

    def mostrar_contornos_2d_plotly(self, fig):
        plotly_util = PlotlyUtil()
        plotly_util.plot_poligono(fig=fig, lista_elementos=self.contornos_negativos, color="Red", espesor=3, transparencia=1)
        plotly_util.plot_poligono(fig=fig, lista_elementos=self.contornos_positivos, color="Cyan", espesor=4, transparencia=1)

    def mostrar_discretizacion_2d(self, ax):
        for elemento in self.elementos:
            elemento.plot(indice_color=3, espesor=0.2, mostrar_centroide=True, ax=ax, transparencia=0.1)

    def mostrar_discretizacion_2d_plotly(self, fig):
        plotly_util = PlotlyUtil()
        plotly_util.plot_poligono(fig=fig, lista_elementos=self.elementos, color="Cyan", transparencia=0.2, mostrar_centroide=True)

    def mostrar_contornos_3d(self, ecuacion_plano_a_desplazar=None):
        fig = plt.figure()
        ax = fig.add_subplot(projection='3d')
        for contorno_negativo in self.contornos_negativos:
            contorno_negativo.plot(
                indice_color=2, espesor=2, tridimensional=True, ec_plano_3d=ecuacion_plano_a_desplazar,
                plt_3d=ax)
        for contorno_positivo in self.contornos_positivos:
            contorno_positivo.plot(
                indice_color=1, espesor=2, tridimensional=True, ec_plano_3d=ecuacion_plano_a_desplazar,
                plt_3d=ax)

    def mostrar_discretizacion_3d_desplazada(self):
        for elemento in self.elementos:
            elemento.cargar_poligono_para_mostrar(indice_color=3, espesor=2, mostrar_centroide=True)

    def obtener_baricentro_y_area(self):
        area_total = 0
        sx = 0
        sy = 0
        for elemento in self.elementos:
            area_total = area_total + elemento.area
            sx = sx + elemento.area * elemento.xg
            sy = sy + elemento.area * elemento.yg
        return round(area_total, 10), round(sx / area_total, 10), round(sy / area_total, 10)

    def cambiar_coordenadas_a_baricentro(self):
        for elemento in self.elementos:
            elemento.desplazar_sistema_de_referencia(desp_x=-self.xg, desp_y=-self.yg)
        for contorno_pos in self.contornos_positivos:
            contorno_pos.desplazar_sistema_de_referencia(desp_x=-self.xg, desp_y=-self.yg)
        for contorno_neg in self.contornos_negativos:
            contorno_neg.desplazar_sistema_de_referencia(desp_x=-self.xg, desp_y=-self.yg)

    @staticmethod
    def plot_to_buf(lista_de_elementos, height=2800, width=2800, inc=0.3):
        data = np.array([(elemento.xg, elemento.yg) for elemento in lista_de_elementos])
        xlims = (data[:, 0].min(), data[:, 0].max())
        ylims = (data[:, 1].min(), data[:, 1].max())
        dxl = xlims[1] - xlims[0]
        dyl = ylims[1] - ylims[0]

        print('xlims: (%f, %f)' % xlims)
        print('ylims: (%f, %f)' % ylims)

        buffer = np.zeros((height + 1, width + 1))
        for i, p in enumerate(data):
            print('\rloading: %03d' % (float(i) / data.shape[0] * 100), end=' ')
            x0 = int(round(((p[0] - xlims[0]) / dxl) * width))
            y0 = int(round((1 - (p[1] - ylims[0]) / dyl) * height))
            buffer[y0, x0] += inc
            if buffer[y0, x0] > 1.0:
                buffer[y0, x0] = 1.0
        return xlims, ylims, buffer

    def obtener_rango_valores_extremos(self):
        lista_x = []
        lista_y = []
        for contorno in self.contornos_positivos:
            for nodo in contorno.nodos_extremos:
                lista_x.append(nodo.x)
                lista_y.append(nodo.y)
        return ((min(lista_x), max(lista_x)), (min(lista_y), max(lista_y)))
