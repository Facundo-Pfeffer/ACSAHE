import copy
import math
import random
from typing import List

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Arc

from build.ext_utils.plotly_util import PlotlyUtil

TOLERANCE = 10 ** -10
pyplot_colors_list = ["r", "b", "g", "c", "m", "y", "k"]
thickness_list = [x / 5 for x in range(10, 20)]


class Node(object):
    """A Node in 2D space."""
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __eq__(self, other_node):
        """Determine if two points are equal within tolerance."""
        return self.x - TOLERANCE <= other_node.x <= self.x + TOLERANCE and self.y - TOLERANCE <= other_node.y <= self.y + TOLERANCE

    def __sub__(self, other_node):
        """Obtains the distance between nodes."""
        return math.sqrt((self.x - other_node.x) ** 2 + (self.y - other_node.y) ** 2)


class NodeList(object):
    """Container for a list of Node instances."""

    def __init__(self, node_list: list[Node]):
        self.node_list = node_list

    def remove_duplicates(self):
        """Removes duplicate nodes based on tolerance."""
        unique_nodes_list = [self.node_list[0]]
        for node in self.node_list[1:]:
            if not any(node == unique_node for unique_node in unique_nodes_list):
                unique_nodes_list.append(node)
        return unique_nodes_list


class Line(object):
    def __init__(self, start_node: Node, end_node: Node):
        self.start_node = start_node
        self.end_node = end_node
        self.a, self.b, self.c = self._get_implicit_eq_params(start_node, end_node)
        self.y = lambda x: -self.c / self.b - self.a / self.b * x
        self.x = lambda y: -self.c / self.a - self.b / self.a * y


    def distancia_a_nodo_v(self, node):
        return abs(node.y + (self.c + self.a * node.x) / self. b) if self.b != 0 else None

    def distancia_a_nodo_h(self, node):
        return abs(node.x + (self.c + self.b * node.y) / self.a) if self.a != 0 else None

        # Distancia en Vertical y Horizontal, respectivamente.

    def line_implicit_equation(self, node: Node) -> float:
        return self.a * node.x + self.b * node.y + self.c

    def distance_to_node(self, node: Node) -> float:
        return self.equation(node) / math.hypot(self.a, self.b)

    @staticmethod
    def _get_implicit_eq_params(start_node, end_node):
        """Returns a, b, c parameters for the implicit line equation ax + by + c = 0"""
        x1, y1 = start_node.x, start_node.y
        x2, y2 = end_node.x, end_node.y
        a = y1 - y2
        b = x2 - x1
        c = y2 * (x1 - x2) + (y2 - y1) * x2
        return a, b, c

    def show_line_pyplot(self):
        """Method useful for debugging."""
        plt.plot([self.start_node.x, self.end_node.x], [self.start_node.y, self.end_node.y])

    def __and__(self, otra_recta) -> Node or None:
        """Realiza la intersección de la recta con otra provista, en el plano.
        :param otra_recta: recta a intersectar.
        :return Nodo de intersección or None si no se encuentran"""
        x1, y1, x2, y2 = self.start_node.x, self.start_node.y, self.end_node.x, self.end_node.y
        x3, y3, x4, y4 = otra_recta.start_node.x, otra_recta.start_node.y, otra_recta.end_node.x, otra_recta.end_node.y
        det = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)  # Determinante de la matriz de coordenadas
        if -1 * TOLERANCE <= det <= TOLERANCE:  # Cuando den tiende a 0, las rectas son paralelas, no hay intersección.
            return None
        # Se aplica la fórmula de Cramer para resolver el sistema de ecuaciones lineal.
        x = ((x1 * y2 - y1 * x2) * (x3 - x4) - (x1 - x2) * (x3 * y4 - y3 * x4)) / det
        y = ((x1 * y2 - y1 * x2) * (y3 - y4) - (y1 - y2) * (x3 * y4 - y3 * x4)) / det
        return Node(x, y)


class Segment(object):
    def __init__(self, start_node: Node, end_node: Node):
        self.start_node = start_node
        self.end_node = end_node
        self.recta_segmento = Line(start_node, end_node)
        self.extremos_x, self.extremos_y = self.extremos_segmento()

    def obtener_parametros_ecuacion_recta(self):
        x1, y1 = self.start_node.x, self.start_node.y
        x2, y2 = self.end_node.x, self.end_node.y
        a = y1 - y2
        b = x2 - x1
        c = y2 * (x1 - x2) + (y2 - y1) * x2
        return a, b, c

    def determinar_si_nodo_esta_en_rango(self, nodo):
        xmin, xmax = self.extremos_x
        ymin, ymax = self.extremos_y
        return xmin - TOLERANCE <= nodo.x <= xmax + TOLERANCE and ymin - TOLERANCE <= nodo.y <= ymax + TOLERANCE

    def determinar_si_nodo_pertenece_a_segmento(self, nodo):
        return self.recta_segmento.line_implicit_equation(nodo) == 0 and self.determinar_si_nodo_esta_en_rango(nodo)

    def extremos_segmento(self):
        extramos_x = (min(self.start_node.x, self.end_node.x), max(self.start_node.x, self.end_node.x))
        extramos_y = (min(self.start_node.y, self.end_node.y), max(self.start_node.y, self.end_node.y))
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
            plt.plot([self.start_node.x, self.end_node.x], [self.start_node.y, self.end_node.y], **kwargs)
        else:
            ax.plot([self.start_node.x, self.end_node.x], [self.start_node.y, self.end_node.y], **kwargs)

    def __and__(self, otro_segmento):
        result = self.recta_segmento & otro_segmento.recta_segmento  # Buscando intersección.
        if not result:
            return None
        return result if self.determinar_si_nodo_esta_en_rango(
            result) and otro_segmento.determinar_si_nodo_esta_en_rango(result) else None



class Poligono(object):
    """Polígono CONVEXO en el plano, formado por una serie de nodos."""
    tipo = "Poligonal"

    def __init__(self, nodos: List[Node], ordenar: bool = False):
        """
        :param nodos: lista de nodos que definen el contorno del polígono.
        :param ordenar: Define si la lista de nodos anterior debe ser ordenada en sentido antihorario, siendo dicho
         sentido el convencional para el programa."""

        self.nodos_extremos = nodos if not ordenar else self.ordenar_nodos_poligono_convexo_antihorario(nodos)
        self.x = [nodo.x for nodo in self.nodos_extremos]
        self.y = [nodo.y for nodo in self.nodos_extremos]
        self.total_de_nodos = len(nodos)
        self.segmentos_borde = self.obtener_segmentos_borde()
        valor_area = self.determinar_area_poligono()
        if valor_area == 0 and isinstance(self, Contorno):
            raise Exception(f"El contorno de índice {self.indice} contiene área 0. Por favor, revisar la entrada de datos.")
        self.area = valor_area
        if valor_area > TOLERANCE:
            self.nodo_centroide = self.determinar_centroide()
            self.xg, self.yg = self.nodo_centroide.x, self.nodo_centroide.y
            # Se definen estos atributos para determinar si el elemento fue modificado por una intersección (ver método)
            self.nodos_interseccion_lista = []
            self.numero_de_modificaciones = 0
            self.nodo_centroide_original = copy.copy(self.nodo_centroide)
            self.area_original = valor_area

    @staticmethod
    def ordenar_nodos_poligono_convexo_antihorario(nodos=None):
        """Ordena los nodos en sentido antihorario, cuando el polígono SEA CONVEXO (requisito)."""
        if nodos is None:
            return None
        x_array = np.array([nodo.x for nodo in nodos])
        y_array = np.array([nodo.y for nodo in nodos])

        # Coordenadas del centroide
        x0 = np.mean(x_array)
        y0 = np.mean(y_array)

        # Calcular las distancias desde el centroide a cada nodo
        r = np.sqrt((x_array - x0) ** 2 + (y_array - y0) ** 2)
        # Calcula el ángulo antihorario con respecto al eje X de cada punto, y ordena basándose en el mismo.
        angulos = np.arctan2(y_array - y0, x_array - x0)
        mask = np.argsort(angulos)
        x_sorted = x_array[mask]
        y_sorted = y_array[mask]

        nodos_ordenados = []
        for i in range(len(x_sorted)):
            nodos_ordenados.append(Node(x_sorted[i], y_sorted[i]))
        return nodos_ordenados

    def obtener_segmentos_borde(self):
        """A partir de los nodos que fueron ingresados, obtiene la lista de segmentos de borde."""
        i = 0
        imax = len(self.nodos_extremos)
        lista_de_segmentos = []
        while i < imax:
            nodo_1 = self.nodos_extremos[i]
            nodo_2 = self.nodos_extremos[i + 1] if i + 1 < imax else self.nodos_extremos[0]
            lista_de_segmentos.append(Segment(nodo_1, nodo_2))
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
            return Node(cx / (6 * self.area), cy / (6 * self.area))
        except RuntimeWarning as e:
            print(e)

    def determinar_si_nodo_pertence_a_contorno(self, nodo_a_buscar: Node):
        """Devuelve verdadero si el nodo se encuentra dentro del contorno, sin incluir los bordes del mismo."""
        for i, nodo in enumerate(self.nodos_extremos):
            nodo_1, nodo_2, nodo_3 = self.obtener_3_nodos_x_indice(i)
            recta = Line(nodo_1, nodo_2)  # Recta definida por el nodo 1 y nodo 2.
            # La ecuación de la recta devolverá valores del mismo signo para puntos del mismo semiplano.
            signo_semiplano_contorno = recta.line_implicit_equation(nodo_3)
            if signo_semiplano_contorno == 0:
                raise Exception(f"Error de Ingreso de datos: Ingresar puntos en el contorno que no estén alineados", )
            signo_semiplano_elemento = recta.line_implicit_equation(nodo_a_buscar)
            if signo_semiplano_contorno * signo_semiplano_elemento < 0:  # Si son de distinto signo, no pertenece.
                return False
        return True

    def determinar_si_nodo_pertence_a_contorno_sin_borde(self, nodo_a_buscar: Node):
        """Devuelve verdadero si el nodo se encuentra dentro del contorno, incluyendo los bordes del mismo."""
        for i, nodo in enumerate(self.nodos_extremos):
            nodo_1, nodo_2, nodo_3 = self.obtener_3_nodos_x_indice(i)
            recta = Line(nodo_1, nodo_2)  # Recta definida por el nodo 1 y nodo 2.
            # La ecuación de la recta devolverá valores del mismo signo para puntos del mismo semiplano.
            signo_semiplano_contorno = recta.line_implicit_equation(nodo_3)
            if signo_semiplano_contorno == 0:
                raise Exception("Error de Ingreso de datos: Ingresar puntos en el contorno que no estén alineados.")
            signo_semiplano_elemento = recta.line_implicit_equation(nodo_a_buscar)
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

        color = random.choice(pyplot_colors_list) if indice_color is None else pyplot_colors_list[indice_color]
        espesor = random.choice(thickness_list) if espesor is None else espesor
        x = []
        y = []
        for segmento in self.segmentos_borde:
            x.extend([segmento.start_node.x, segmento.end_node.x])
            y.extend([segmento.start_node.y, segmento.end_node.y])

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
            plt.scatter(self.xg, self.yg, c=color, marker=".", zorder=0, s=self.area/10)
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
        lista_nodos_interseccion = NodeList(lista_nodos_interseccion).remove_duplicates()
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
        self.nodo_centroide = Node(nueva_x, nueva_y)
        self.nodos_interseccion_lista = lista_de_nodos_de_interseccion + self.nodos_interseccion_lista
        return self  # self modificado

    @staticmethod
    def nuevo_poligono_es_valido(nueva_area, nueva_x, nueva_y):  # Criterio: área=0|nodo en infinito numérico.
        return not (-TOLERANCE * TOLERANCE <= nueva_area <= TOLERANCE * TOLERANCE or nueva_x == float(
            "inf") or nueva_y == float("inf"))

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
        nodos_interseccion = NodeList(lista_nodos_interseccion).remove_duplicates()
        return nodos_interseccion

    def __and__(self, otro_poligono):
        """Devuelve los nodos de interseccion de dos poligonos"""
        lista_nodos_interseccion = []
        if isinstance(self, ContornoCircular) or isinstance(otro_poligono, ContornoCircular):
            return lista_nodos_interseccion
        for segmento_contorno in self.segmentos_borde:
            for segmento_rectangulo in otro_poligono.segmentos_borde:
                interseccion = segmento_contorno & segmento_rectangulo
                if interseccion:
                    nodo_interseccion = Node(interseccion.x, interseccion.y)
                    if not (any(nodo_interseccion == nodo_x for nodo_x in lista_nodos_interseccion)):
                        lista_nodos_interseccion.append(nodo_interseccion)
        return lista_nodos_interseccion or None

    def pertenece_a_contorno(self, contorno):
        """Determina si self está contenido dentro de poligono mayor"""
        centro_pertenece_a_contorno = contorno.determinar_si_nodo_pertence_a_contorno(self.nodo_centroide)
        if not centro_pertenece_a_contorno:
            return False
        if not isinstance(contorno, ContornoCircular):
            intersecciones = contorno & self
            return True if not intersecciones else False
        return True

    @staticmethod
    def area_y_centro_son_iguales(poligono_1, poligono_2):
        """Valida si dos polígonos son iguales"""
        return poligono_2.area - TOLERANCE <= poligono_1.area <= poligono_2.area + TOLERANCE and \
            poligono_2.xg - TOLERANCE <= poligono_1.xg <= poligono_2.xg + TOLERANCE and \
            poligono_2.yg - TOLERANCE <= poligono_1.yg <= poligono_2.yg + TOLERANCE

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

    def __init__(self, ubicacion_centro: Node, medidas: tuple):
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
        return Node(x + a / 2, y + b / 2), Node(x + a / 2, y - b / 2), Node(x - a / 2, y - b / 2), Node(x - a / 2,
                                                                                                        y + b / 2)

    def obtener_segmentos_borde(self):
        return (
            Segment(self.nodos_extremos[0], self.nodos_extremos[1]),
            Segment(self.nodos_extremos[1], self.nodos_extremos[2]),
            Segment(self.nodos_extremos[2], self.nodos_extremos[3]),
            Segment(self.nodos_extremos[3], self.nodos_extremos[0])
        )


class ElementoTrapecioCircular(object):
    tipo = "Trapecio Circular"

    def __init__(self, nodo_centro: Node, radios: tuple, angulos):
        self.area = math.radians(angulos[1] - angulos[0]) * (radios[1] ** 2 - radios[0] ** 2) / 2
        angulo_medio = math.radians(angulos[1] + angulos[0]) / 2

        self.angulo_inicial, self.angulo_final = min(angulos), max(angulos)
        self.radio_interno, self.radio_externo = min(radios), max(radios)
        self.nodo_centroide = nodo_centro
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
        self.nodo_centroide = Node(self.xg, self.yg)

        self.nodos_extremos = self.obtener_nodos_extremos()
        self.segmentos_rectos = self.obtener_segmentos_rectos()

    def obtener_nodos_extremos(self):
        resultado = []
        if self.radio_interno == 0:  # Circulo
            return []
        for theta in [self.angulo_inicial, self.angulo_final]:
            for r in [self.radio_interno, self.radio_externo]:
                resultado.append(
                    Node(self.xc + r * math.cos(math.radians(theta)), self.yc + r * math.sin(math.radians(theta))))
        return resultado

    def obtener_segmentos_rectos(self):
        if len(self.nodos_extremos) == 0:
            return None
        return (
            Segment(self.nodos_extremos[0], self.nodos_extremos[1]),
            Segment(self.nodos_extremos[2], self.nodos_extremos[3])
        )

    def nodo_en_elemento(self, nodo: Node):
        xc, yc = nodo.x - self.nodo_centro.x, nodo.y - self.nodo_centro.y
        angulo = math.atan2(yc, xc)
        angulo = angulo + 360 if angulo < 0 else angulo  # Sumar 360 para convertir a ángulo con respecto a x.
        radio = math.sqrt(xc ** 2 + yc ** 2)
        return self.angulo_inicial <= angulo <= self.angulo_final and self.radio_interno <= radio <= self.radio_externo

    def desplazar_sistema_de_referencia(self, desp_x, desp_y):
        self.xg += desp_x
        self.xc += desp_x
        self.yg += desp_y
        self.yc += desp_y
        self.nodo_centro.x += desp_x
        self.nodo_centro.y += desp_y
        self.nodos_extremos = self.obtener_nodos_extremos()
        self.segmentos_rectos = self.obtener_segmentos_rectos()

    def plot(self, indice_color, espesor, ax, mostrar_centroide=False, transparencia=1.00):
        # Coordenadas de los puntos del trapecio circular
        color = random.choice(pyplot_colors_list) if indice_color is None else pyplot_colors_list[indice_color]
        espesor = random.choice(thickness_list) if espesor is None else espesor
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
            plt.scatter(self.xg, self.yg, c=color, marker=".", zorder=0, s=self.area/10)
        return ax
        # Crear la figura y el gráfico

    def plotly_elemento(self, fig, mostrar_centroide=False, transparencia=1):
        PlotlyUtil.plot_trapecio_circular(trapecio_circular=self,
                                          fig=fig,
                                          mostrar_centroide=mostrar_centroide,
                                          transparencia=transparencia)

    def pertenece_a_contorno(self, contorno):
        """Determina si self está contenido dentro de polígono mayor"""
        return contorno.determinar_si_nodo_pertence_a_contorno(self.nodo_centroide)


class ContornoCircular(ElementoTrapecioCircular):
    tipo = "Circular"

    def __init__(self, nodo_centro: Node, indice, radios: tuple, angulos: tuple = (0, 360), signo=1):
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
                nodo_centro=self.nodo_centroide,
                angulos=(self.angulo_inicial, self.angulo_final),
                radios=(radio, radio_final / 2)))
            angulo = self.angulo_inicial
            while angulo <= self.angulo_final - discretizacion_angulo:
                resultado.append(ElementoTrapecioCircular(
                    nodo_centro=self.nodo_centroide,
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
                    nodo_centro=self.nodo_centroide,
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

    def determinar_si_nodo_pertence_a_contorno(self, nodo: Node):
        distancia_centro = self.nodo_centro - nodo
        return self.radio_interno - TOLERANCE < distancia_centro < self.radio_externo + TOLERANCE


class Contorno(Poligono):
    """Un contorno es un polígono el cual podrá ser discretizado en elementos tipo ElementoRectangular.
    Además, el atributo signo lleva asignado un significado:
    """
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
        lista_elem_validos = [elem for elem in lista_de_elementos if elem.area > TOLERANCE and (not (math.isnan(elem.xg) or math.isnan(elem.yg)))]
        return self.eliminar_elementos_fuera_de_contorno(
            lista_elem_validos)  # Limpieza adicional de elementos no válidos.

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
                rectangulo_diferencial = ElementoRectangular(ubicacion_centro=Node(x, y), medidas=(dx, dy))
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
            recta = Line(nodo_1, nodo_2)  # Recta definida por el nodo 1 y 2.
            # La ecuación de la recta devuelve números del mismo signos para puntos en el mismo semiplano
            signo_semiplano_contorno = recta.line_implicit_equation(nodo_3)
            if signo_semiplano_contorno == 0:
                raise Exception(
                    f"Por favor, ingresar puntos en el contorno que no estén alineados. Contorno: {self.indice}")
            for elemento_diferencial in lista_de_elementos.copy():
                signo_semiplano_elemento = recta.line_implicit_equation(elemento_diferencial.nodo_centroide)
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
    """Una Sección Arbitraria será la combinación de objetos tipo Contorno.
    Los elementos con signo positivo representan regiones de alma llena mientras que las negativas regiones vacías."""

    def __init__(self, contornos: dict, discretizacion):
        self.dx, self.dy, self.dr, self.d_ang = discretizacion
        self.contornos_negativos = [contorno for indice_contorno, contorno in contornos.items() if contorno.signo == -1]
        self.contornos_positivos = [contorno for indice_contorno, contorno in contornos.items() if contorno.signo == 1]
        self.elementos = self.obtener_matriz_elementos_positivos()
        self.area, self.xg, self.yg = self.obtener_baricentro_y_area()
        self.cambiar_coordenadas_a_baricentro()
        self.Ix, self.Iy = self.calcular_inercias()
        self.x_min, self.x_max, self.y_min, self.y_max = self.obtener_valores_extremos()

    def obtener_matriz_elementos_positivos(self):
        result = []
        for contorno_positivo in self.contornos_positivos:
            if contorno_positivo.tipo == "Poligonal":
                lista_elementos_positivos = contorno_positivo.discretizar_contorno(self.dx, self.dy)
            else:  # Circular
                lista_elementos_positivos = contorno_positivo.discretizar_contorno(discretizacion_angulo=self.d_ang,
                                                                                   discretizacion_radio=self.dr)
            for elemento_positivo in lista_elementos_positivos:
                if self.elemento_pertenece_a_contorno_negativo(
                        elemento_positivo) or elemento_positivo.area < TOLERANCE:
                    continue  # Descartar elemento
                elemento_intersectado = self.obtener_interseccion_elemento_positivo_con_negativo(elemento_positivo)
                if elemento_intersectado and elemento_intersectado.area > TOLERANCE:
                    result.append(elemento_intersectado)
        if len(result) == 0:
            raise Exception("Error en la generación de la geometría:\n"
                            "No se encontraron contornos positivos por fuera de contornos negativos.")
        return result

    def elemento_pertenece_a_contorno_negativo(self, elemento_positivo: Poligono):
        for contorno_negativo in self.contornos_negativos:
            if elemento_positivo.pertenece_a_contorno(contorno_negativo):  # Pertenece COMPLETAMENTE a elemento
                return True
        return False

    def obtener_interseccion_elemento_positivo_con_negativo(self, elemento_positivo):
        if not(isinstance(elemento_positivo, ElementoTrapecioCircular)):
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

    def mostrar_discretizacion_2d(self, ax):
        [elemento.plot(indice_color=3, espesor=1, mostrar_centroide=True, ax=ax, transparencia=0.6) for elemento in self.elementos]

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

    def obtener_baricentro_y_area(self):
        area_total = 0
        sx = 0
        sy = 0
        for elemento in self.elementos:
            area_total = area_total + elemento.area
            sx = sx + elemento.area * elemento.xg
            sy = sy + elemento.area * elemento.yg
        return round(area_total, 10), round(sx / area_total, 10), round(sy / area_total, 10)

    def calcular_inercias(self):
        Ix = 0
        Iy = 0
        for elemento in self.elementos:
            Ix = Ix + elemento.area * (elemento.yg**2)
            Iy = Iy + elemento.area * (elemento.xg**2)
        return round(Ix, 0), round(Iy, 0)

    def cambiar_coordenadas_a_baricentro(self):
        for elemento in self.elementos:
            elemento.desplazar_sistema_de_referencia(desp_x=-self.xg, desp_y=-self.yg)
        for contorno_pos in self.contornos_positivos:
            contorno_pos.desplazar_sistema_de_referencia(desp_x=-self.xg, desp_y=-self.yg)
        for contorno_neg in self.contornos_negativos:
            contorno_neg.desplazar_sistema_de_referencia(desp_x=-self.xg, desp_y=-self.yg)

    def obtener_valores_extremos(self):
        return min(x.xg for x in self.elementos), max(x.xg for x in self.elementos), min(x.yg for x in self.elementos), max(x.yg for x in self.elementos)

    def plotly(self, fig, planos_de_carga):
        plotly_util = PlotlyUtil(fig=fig)
        plotly_util.plot_seccion(seccion=self, lista_de_angulos_plano_de_carga=planos_de_carga)
