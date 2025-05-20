import copy
import math
import random
from typing import List
import numpy as np

from build.utils.plotly_engine import ACSAHEPlotlyEngine

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

    def equation(self, node: Node):
        return self.a*node.x + self.b*node.y + self.c

    def distancia_a_nodo_v(self, node):
        return abs(node.y + (self.c + self.a * node.x) / self. b) if self.b != 0 else None

    def distancia_a_nodo_h(self, node):
        return abs(node.x + (self.c + self.b * node.y) / self.a) if self.a != 0 else None

        # Distancia en Vertical y Horizontal, respectivamente.

    def line_implicit_equation(self, node: Node) -> float:
        return self.a * node.x + self.b * node.y + self.c

    def distance_to_node(self, node: Node) -> float:
        return self.equation(node) / math.hypot(self.a, self.b)

    def is_node_in_line(self, node: Node) -> bool:
        distance_to_node = self.distance_to_node(node)
        return abs(distance_to_node) < TOLERANCE

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
        plotly_util = ACSAHEPlotlyEngine()
        plotly_util.plotly_segment(self.start_node, self.end_node)

    def __and__(self, otra_recta) -> Node or None:
        """Intersection of lines in 2D plane."""
        x1, y1, x2, y2 = self.start_node.x, self.start_node.y, self.end_node.x, self.end_node.y
        x3, y3, x4, y4 = otra_recta.start_node.x, otra_recta.start_node.y, otra_recta.end_node.x, otra_recta.end_node.y
        det = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
        if -1 * TOLERANCE <= det <= TOLERANCE:  # When den approaches 0, the lines are parallel (no intersection).
            return None
        # Cramer's law for solving the linear equation system.
        x = ((x1 * y2 - y1 * x2) * (x3 - x4) - (x1 - x2) * (x3 * y4 - y3 * x4)) / det
        y = ((x1 * y2 - y1 * x2) * (y3 - y4) - (y1 - y2) * (x3 * y4 - y3 * x4)) / det
        return Node(x, y)

    def __floordiv__(self, other):
        """True if lines are parallel"""
        intersection = self & other
        if intersection is None:
            return True
        return False


class Vector(object):
    def __init__(self, start_node, end_node):
        self.a = end_node.x-start_node.x
        self.b = end_node.y-start_node.y
        self.modulus = math.sqrt(self.b**2 + self.a**2)
        self.not_null = self.modulus > TOLERANCE
        self.start_node = start_node

    def __mul__(self, other_vector):
        """Scalar product."""
        return self.a*other_vector.a + self.b*other_vector.b


class Segment(object):
    def __init__(self, start_node: Node, end_node: Node):
        self.start_node = start_node
        self.end_node = end_node
        self.segment_line = Line(start_node, end_node)
        self.extremos_x, self.extremos_y = self._get_segment_endpoints_ranges()
        self.vector = Vector(start_node, end_node)

    def _get_general_line_equation_params(self):
        x1, y1 = self.start_node.x, self.start_node.y
        x2, y2 = self.end_node.x, self.end_node.y
        a = y1 - y2
        b = x2 - x1
        c = y2 * (x1 - x2) + (y2 - y1) * x2
        return a, b, c
    
    def is_node_endpoint(self, other_node):
        return any(other_node == self_node for self_node in [self.start_node, self.end_node])

    def is_node_in_segment_range(self, nodo):
        xmin, xmax = self.extremos_x
        ymin, ymax = self.extremos_y
        return xmin - TOLERANCE <= nodo.x <= xmax + TOLERANCE and ymin - TOLERANCE <= nodo.y <= ymax + TOLERANCE

    def node_belongs_to_segment(self, nodo):
        return self.segment_line.line_implicit_equation(nodo) == 0 and self.is_node_in_segment_range(nodo)

    def _get_segment_endpoints_ranges(self):
        x_endpoints = (min(self.start_node.x, self.end_node.x), max(self.start_node.x, self.end_node.x))
        y_endpoints = (min(self.start_node.y, self.end_node.y), max(self.start_node.y, self.end_node.y))
        return x_endpoints, y_endpoints

    def get_intersection_w_line(self, line):
        intersection_node = line & self.segment_line
        if not intersection_node:  # Paralelas
            return None
        result = intersection_node if self.is_node_in_segment_range(
            intersection_node) else None
        return result

    def plot(self, **kwargs):
        plotly_util = ACSAHEPlotlyEngine()
        plotly_util.plotly_segment(self.start_node, self.end_node, **kwargs)

    def segment_vectors_share_orientation(self, other_segment):
        if not(self & other_segment is None):
            print("Segments are not parallel hence they can't share orientation")
            return False
        scalar_vector_product = self.vector * other_segment.vector
        return True if scalar_vector_product > 0 else False

    def is_parallel_to_segment_and_shares_range(self, other_segment):
        if not(self.segment_line & other_segment.segment_line is None):  # Segments are not parallel.
            return False
        if not self.segment_line.is_node_in_line(other_segment.start_node):  # Segments are parallel but not collinear.
            return False
        if not(any([self.is_node_in_segment_range(other_segment.start_node),  # Segments do not share range
               self.is_node_in_segment_range(other_segment.end_node),
                other_segment.is_node_in_segment_range(self.start_node),
                other_segment.is_node_in_segment_range(self.start_node)])):
            return False
        return True

    def __and__(self, otro_segmento):
        """Segments intersection."""
        result = self.segment_line & otro_segmento.segment_line
        if self // otro_segmento:  # Parallel
            return None
        return result if self.is_node_in_segment_range(
            result) and otro_segmento.is_node_in_segment_range(result) else None

    def __sub__(self, other_segment):
        """Returns the resulting segment(s) when deleting the parts of self that belong to other_segment"""
        if not(self.is_parallel_to_segment_and_shares_range(other_segment)):
            return [self]
        if not self.segment_vectors_share_orientation(other_segment):
            equivalent_segment = Segment(other_segment.end_node, other_segment.start_node)
        else:
            equivalent_segment = other_segment
        segments_to_keep = []

        if self.node_belongs_to_segment(equivalent_segment.start_node):
            segments_to_keep.append(Segment(self.start_node, equivalent_segment.start_node))
        if self.node_belongs_to_segment(equivalent_segment.end_node):
            segments_to_keep.append(Segment(equivalent_segment.end_node, self.end_node))

        segments_to_keep = [segment for segment in segments_to_keep if segment.vector.not_null]
        if len(segments_to_keep) == 0:  # All self belongs to other_segment
            return None
        return segments_to_keep

    def __repr__(self):  # Created so that segments can be removed from lists. Required in plotly_engine.py module.
        return f"Segment(({self.start_node.x, self.start_node.y}); ({self.end_node.x, self.end_node.y}))"

    def __floordiv__(self, other_segment):
        """True if segments are parallel"""
        if self.segment_line & other_segment.segment_line is None:
            return True
        return False

    def __eq__(self, other_segment):
        if not self // other_segment:
            return False
        if self.vector * other_segment.vector > 0:  # Segments share orientation
            return all([self.start_node == other_segment.start_node, self.end_node == other_segment.end_node])
        else:
            return all([self.start_node == other_segment.end_node, self.end_node == other_segment.start_node])


class Polygon(object):
    """CONVEX polygon in the plane, formed by a series of nodes."""
    tipo = "Poligonal"

    def __init__(self, nodes: List[Node], sort_nodes: bool = False):
        """
        :param nodes: list of nodes that define the polygon's contour.
        :param sort_nodes: Defines if the previous list of nodes should be sorted counterclockwise, being this
        direction the conventional one for the software."""

        self.boundary_nodes_list = nodes if not sort_nodes else self._sort_nodes_counterclokwise(nodes)
        self.x = [node.x for node in self.boundary_nodes_list]
        self.y = [node.y for node in self.boundary_nodes_list]
        self.nodes_count = len(nodes)
        self.boundary_segments_list = self._get_boundary_segments()
        area = self._get_polygon_area()
        if area == 0 and isinstance(self, Region):
            raise Exception(f"El region de índice {self.indice} contiene área 0. Por favor, revisar la entrada de datos.")
        self.area = area
        if area > TOLERANCE:
            self.centroid_node = self._get_centroid_node()
            self.xg, self.yg = self.centroid_node.x, self.centroid_node.y

            # These attributes are defined to determine if the element was modified by an intersection (see method)
            self.intersection_nodes_list = []
            self.modifications_count = 0
            self.centroid_node_original = copy.copy(self.centroid_node)
            self.area_original = area


    @staticmethod
    def _sort_nodes_counterclokwise(nodes_list=None):
        """Sort nodes counterclockwise. The polygon MUST BE Convex."""
        if nodes_list is None:
            return None
        x_array = np.array([nodo.x for nodo in nodes_list])
        y_array = np.array([nodo.y for nodo in nodes_list])

        # Centroid coordinates
        x0 = np.mean(x_array)
        y0 = np.mean(y_array)

        # Calculate distances from the centroid to each node

        r = np.sqrt((x_array - x0) ** 2 + (y_array - y0) ** 2)
        # Calculate the counterclockwise angle with respect to the X axis for each point, and sort based on it
        angulos = np.arctan2(y_array - y0, x_array - x0)
        mask = np.argsort(angulos)
        x_sorted = x_array[mask]
        y_sorted = y_array[mask]

        sorted_nodes_list = []
        for i in range(len(x_sorted)):
            sorted_nodes_list.append(Node(x_sorted[i], y_sorted[i]))
        return sorted_nodes_list

    def _get_boundary_segments(self):
        i = 0
        imax = len(self.boundary_nodes_list)
        lista_de_segmentos = []
        while i < imax:
            nodo_1 = self.boundary_nodes_list[i]
            nodo_2 = self.boundary_nodes_list[i + 1] if i + 1 < imax else self.boundary_nodes_list[0]
            lista_de_segmentos.append(Segment(nodo_1, nodo_2))
            i = i + 1
        return lista_de_segmentos

    def _get_polygon_area(self):
        i = 0
        imax = len(self.boundary_nodes_list)
        area = 0
        while i < imax:
            nodo_1 = self.boundary_nodes_list[i]
            nodo_2 = self.boundary_nodes_list[i + 1] if i + 1 < imax else self.boundary_nodes_list[0]
            area = area + (nodo_1.x * nodo_2.y - nodo_2.x * nodo_1.y)
            i = i + 1
        return abs(area / 2)

    def _get_centroid_node(self):
        try:
            i = 0
            imax = len(self.boundary_nodes_list)
            cx, cy = 0, 0
            while i < imax:
                nodo_1 = self.boundary_nodes_list[i]
                nodo_2 = self.boundary_nodes_list[i + 1] if i + 1 < imax else self.boundary_nodes_list[0]
                cx = cx + (nodo_1.x + nodo_2.x) * (nodo_1.x * nodo_2.y - nodo_2.x * nodo_1.y)
                cy = cy + (nodo_1.y + nodo_2.y) * (nodo_1.x * nodo_2.y - nodo_2.x * nodo_1.y)
                i = i + 1
            return Node(cx / (6 * self.area), cy / (6 * self.area))
        except RuntimeWarning as e:
            print(e)

    def is_node_inside_boundaries(self, nodo_a_buscar: Node):
        """Returns True if the node is inside the boundaries of the polygon, False otherwise."""
        for i, nodo in enumerate(self.boundary_nodes_list):
            nodo_1, nodo_2, nodo_3 = self._get_3_nodes_per_index(i)
            recta = Line(nodo_1, nodo_2)  # Recta definida por el nodo 1 y nodo 2.
            # La ecuación de la recta devolverá valores del mismo sign para puntos del mismo semiplano.
            sign_semiplano_region = recta.line_implicit_equation(nodo_3)
            if sign_semiplano_region == 0:
                raise Exception(f"Error de Ingreso de datos: Ingresar puntos en el region que no estén alineados", )
            sign_semiplano_elemento = recta.line_implicit_equation(nodo_a_buscar)
            if sign_semiplano_region * sign_semiplano_elemento < 0:  # Si son de distinto sign, no pertenece.
                return False
        return True

    def is_node_inside_borderless_boundaries(self, nodo_a_buscar: Node):
        """Returns True if the node is inside the boundaries of the polygon BUT not in the boundaries, False otherwise."""
        for i, nodo in enumerate(self.boundary_nodes_list):
            nodo_1, nodo_2, nodo_3 = self._get_3_nodes_per_index(i)
            recta = Line(nodo_1, nodo_2)  # Recta definida por el nodo 1 y nodo 2.
            # La ecuación de la recta devolverá valores del mismo sign para puntos del mismo semiplano.
            sign_semiplano_region = recta.line_implicit_equation(nodo_3)
            if sign_semiplano_region == 0:
                raise Exception("Error de Ingreso de datos: Ingresar puntos en el region que no estén alineados.")
            sign_semiplano_elemento = recta.line_implicit_equation(nodo_a_buscar)
            if sign_semiplano_region * sign_semiplano_elemento <= 0:  # Si son de distinto sign, no pertenece.
                return False
        return True

    def _get_3_nodes_per_index(self, i_first_node):
        """Gets the node with index i_first_node and the 2 next nodes inside boundary_nodes_list
        When any index falls out of range, it gets the first or second element as appropriate."""
        i_second_node = self._get_node_index(i_first_node, 1)
        i_third_node = self._get_node_index(i_first_node, 2)
        return self.boundary_nodes_list[i_first_node], self.boundary_nodes_list[i_second_node], self.boundary_nodes_list[i_third_node]

    def _get_node_index(self, indice_punto_1, index_offset: int):
        """Gets node index value inside boundary_nodes_list based on index_offset value"""
        i_punto = indice_punto_1 + index_offset
        return i_punto if i_punto < self.nodes_count else i_punto - self.nodes_count

    def get_intersection_polygon(self, other_polygon):
        """Returns the intersection of Polygons"""
        intersection_nodes_list = self & other_polygon
        if not intersection_nodes_list:
            return self
        # Determines which nodes of other_polygon belong inside self
        for nodo in other_polygon.boundary_nodes_list:
            if self.is_node_inside_borderless_boundaries(nodo):
                intersection_nodes_list.append(nodo)
        for nodo_pos in self.boundary_nodes_list: # Determines which nodes of self are inside other_polygons
            if other_polygon.is_node_inside_borderless_boundaries(nodo_pos):
                intersection_nodes_list.append(nodo_pos)
        if len(intersection_nodes_list) <= 2:
            return self
        intersection_nodes_list = NodeList(intersection_nodes_list).remove_duplicates()
        return Polygon(intersection_nodes_list, sort_nodes=True)

    def substract_with_other_polygon(self, other_polygon):
        """Subtracts from the self element the complement with other_polygon.
        :param other_polygon: polygon that will be subtracted from self.
        :return: the same self element, but modified by the subtraction."""

        intersection_nodes_list = self._get_shared_nodes_list(self, other_polygon)

        if len(intersection_nodes_list) <= 2:
            return self

        internal_polygon = Polygon(intersection_nodes_list, sort_nodes=True)

        if self.area_y_centro_son_iguales(poligono_1=self, poligono_2=internal_polygon):
            # If the intersection equals self, it will be removed.
            return None

        nueva_area = self.area - internal_polygon.area
        nueva_x = (self.area * self.xg - internal_polygon.area * internal_polygon.xg) / nueva_area
        nueva_y = (self.area * self.yg - internal_polygon.area * internal_polygon.yg) / nueva_area

        if not self._is_new_polygon_valid(nueva_area, nueva_x, nueva_y):
            return None
        self.modifications_count = self.modifications_count + 1

        self.area = nueva_area
        self.xg, self.yg = nueva_x, nueva_y
        self.centroid_node = Node(nueva_x, nueva_y)
        self.intersection_nodes_list = intersection_nodes_list + self.intersection_nodes_list
        return self  # self modificado

    @staticmethod
    def _is_new_polygon_valid(nueva_area, nueva_x, nueva_y):  # Criterio: área=0|nodo en infinito numérico.
        return not (-TOLERANCE * TOLERANCE <= nueva_area <= TOLERANCE * TOLERANCE or nueva_x == float(
            "inf") or nueva_y == float("inf"))

    @staticmethod
    def _get_shared_nodes_list(polygon_1, polygon_2):
        """Returns a list of:
        Nodes that intersect any of the edges between the polygons
        Nodes from poligono_1 that are within poligono_2, and vice versa."""
        
        shared_nodes_list = polygon_1 & polygon_2  # Shared boundaries
        if not shared_nodes_list:  # No intersection
            return []

        for nodo in polygon_2.boundary_nodes_list:  # Gets nodes from polygon_2 that are inside polygon_1
            if polygon_1.is_node_inside_borderless_boundaries(nodo):
                shared_nodes_list.append(nodo)
        for nodo_pos in polygon_1.boundary_nodes_list:  # Gets nodes from polygon_2 that are inside polygon_1
            if polygon_2.is_node_inside_borderless_boundaries(nodo_pos):
                shared_nodes_list.append(nodo_pos)
        intersection_nodes = NodeList(shared_nodes_list).remove_duplicates()
        return intersection_nodes

    def is_segment_a_border_segment(self, segment: Segment):
        for border_segment in self.boundary_segments_list:
            if border_segment == segment:
                return True
        return False

    def __and__(self, other_polygon):
        """Returns intersection nodes between the borders of self and other_polygon"""
        intersection_nodes_list = []
        if isinstance(self, CircularRegion) or isinstance(other_polygon, CircularRegion):
            return intersection_nodes_list
        for region_boundary_segment in self.boundary_segments_list:
            for other_boundary_segment in other_polygon.boundary_segments_list:
                interseccion = region_boundary_segment & other_boundary_segment
                if interseccion:
                    nodo_interseccion = Node(interseccion.x, interseccion.y)
                    if not (any(nodo_interseccion == nodo_x for nodo_x in intersection_nodes_list)):
                        intersection_nodes_list.append(nodo_interseccion)
        return intersection_nodes_list or None

    def is_node_in_element(self, region):
        centro_is_node_in_element = region.is_node_inside_boundaries(self.centroid_node)
        if not centro_is_node_in_element:
            return False
        if not isinstance(region, CircularRegion):  # TODO add functionality
            intersecciones = region & self
            return True if not intersecciones else False
        return True

    @staticmethod
    def area_y_centro_son_iguales(poligono_1, poligono_2):
        """Valida si dos polígonos son iguales"""
        return poligono_2.area - TOLERANCE <= poligono_1.area <= poligono_2.area + TOLERANCE and \
            poligono_2.xg - TOLERANCE <= poligono_1.xg <= poligono_2.xg + TOLERANCE and \
            poligono_2.yg - TOLERANCE <= poligono_1.yg <= poligono_2.yg + TOLERANCE

    def translate_reference_frame(self, desp_x, desp_y):
        self.xg = self.xg + desp_x
        self.yg = self.yg + desp_y
        for nodo_extremo in self.boundary_nodes_list:
            nodo_extremo.x = nodo_extremo.x + desp_x
            nodo_extremo.y = nodo_extremo.y + desp_y
        self.boundary_segments_list = self._get_boundary_segments()


class RectangularElement(Polygon):
    """A rectangular finite element. It inherits the properties of a Polygon."""

    def __init__(self, ubicacion_centro: Node, medidas: tuple):
        a, b = medidas
        self.lado_x, self.lado_y = a, b
        self.x_centro = ubicacion_centro.x
        self.y_centro = ubicacion_centro.y
        self.ubicacion_centro = ubicacion_centro
        self.medidas = medidas
        self.perimetro = 2 * a + 2 * b
        super().__init__(self.obtener_boundary_nodes_list())

    def _get_polygon_area(self):
        return self.lado_x * self.lado_y

    def _get_centroid_node(self):
        return self.ubicacion_centro

    def obtener_boundary_nodes_list(self):
        x, y = self.x_centro, self.y_centro
        a, b = self.lado_x, self.lado_y
        return Node(x + a / 2, y + b / 2), Node(x + a / 2, y - b / 2), Node(x - a / 2, y - b / 2), Node(x - a / 2,
                                                                                                        y + b / 2)

    def _get_boundary_segments(self):
        return (
            Segment(self.boundary_nodes_list[0], self.boundary_nodes_list[1]),
            Segment(self.boundary_nodes_list[1], self.boundary_nodes_list[2]),
            Segment(self.boundary_nodes_list[2], self.boundary_nodes_list[3]),
            Segment(self.boundary_nodes_list[3], self.boundary_nodes_list[0])
        )


class AnnularSectorElement(object):
    tipo = "Annular Sector"

    def __init__(self, centroid_node: Node, boundary_radii_list: tuple, boundary_angles_list):
        self.area = math.radians(boundary_angles_list[1] - boundary_angles_list[0]) * (boundary_radii_list[1] ** 2 - boundary_radii_list[0] ** 2) / 2
        angulo_medio = math.radians(boundary_angles_list[1] + boundary_angles_list[0]) / 2

        self.start_angle, self.end_angle = min(boundary_angles_list), max(boundary_angles_list)
        self.internal_radius, self.external_radius = min(boundary_radii_list), max(boundary_radii_list)
        self.centroid_node = centroid_node
        self.centroid_node = centroid_node
        self.xc = centroid_node.x
        self.yc = centroid_node.y

        theta = math.radians(self.end_angle - self.start_angle) / 2

        # The centroid is defined by 2R sin(θ)/(3θ); R stands for radius and θ the angle.
        external_area = math.radians(self.end_angle - self.start_angle) * (self.external_radius ** 2) / 2
        internal_area = math.radians(self.end_angle - self.start_angle) * (self.internal_radius ** 2) / 2
        centroid_radius = 2 * math.sin(theta) / (3 * theta) * (
                self.external_radius * external_area - self.internal_radius * internal_area) / self.area
        self.xg = math.cos(angulo_medio) * centroid_radius + self.xc
        self.yg = math.sin(angulo_medio) * centroid_radius + self.yc
        self.centroid_node = Node(self.xg, self.yg)

        self.boundary_nodes_list = self._get_boundary_nodes_list()
        self.boundary_straight_segments_list = self._get_straight_boundary_segments_list()

    def _get_boundary_nodes_list(self):
        nodes_list = []
        if self.internal_radius == 0:  # Portion of circle
            return []
        for theta in [self.start_angle, self.end_angle]:
            for r in [self.internal_radius, self.external_radius]:
                nodes_list.append(
                    Node(self.xc + r * math.cos(math.radians(theta)), self.yc + r * math.sin(math.radians(theta))))
        return nodes_list

    def _get_straight_boundary_segments_list(self):
        if len(self.boundary_nodes_list) == 0:
            return None
        return (
            Segment(self.boundary_nodes_list[0], self.boundary_nodes_list[1]),
            Segment(self.boundary_nodes_list[2], self.boundary_nodes_list[3])
        )

    def is_node_in_annular_sector(self, nodo: Node):
        xc, yc = nodo.x - self.centroid_node.x, nodo.y - self.centroid_node.y
        angulo = math.atan2(yc, xc)
        angulo = angulo + 360 if angulo < 0 else angulo  # Sumar 360 para convertir a ángulo con respecto a x.
        radio = math.sqrt(xc ** 2 + yc ** 2)
        return self.start_angle <= angulo <= self.end_angle and self.internal_radius <= radio <= self.external_radius

    def translate_reference_frame(self, desp_x, desp_y):
        self.xg += desp_x
        self.xc += desp_x
        self.yg += desp_y
        self.yc += desp_y
        self.centroid_node.x += desp_x
        self.centroid_node.y += desp_y
        self.boundary_nodes_list = self._get_boundary_nodes_list()
        self.boundary_straight_segments_list = self._get_straight_boundary_segments_list()

    def is_node_in_element(self, region):
        """Determina si self está contenido dentro de polígono mayor"""
        return region.is_node_inside_boundaries(self.centroid_node)


class CircularRegion(AnnularSectorElement):
    tipo = "Circular"

    def __init__(self, centroid_node: Node, indice, boundary_radii_list: tuple, boundary_angles_list: tuple = (0, 360), sign=1):
        self.sign = sign
        super().__init__(centroid_node, boundary_radii_list, boundary_angles_list)

    def generate_mesh(self, discretizacion_angulo, discretizacion_radio):
        """Define la lista de elements_list tipo ElementoRectangular que se encuentran dentro del region."""
        n = discretizacion_radio
        funcion_radii = lambda i: self.internal_radius + (self.external_radius - self.internal_radius) * (
                1 - (1 - i / n) ** 1.25)

        resultado = []
        radio = self.internal_radius
        radio_final = funcion_radii(1)
        i_inicial = 0

        if self.internal_radius == 0:  # Sector central circular
            resultado.append(AnnularSectorElement(
                centroid_node=self.centroid_node,
                boundary_angles_list=(self.start_angle, self.end_angle),
                boundary_radii_list=(radio, radio_final / 2)))
            angulo = self.start_angle
            while angulo <= self.end_angle - discretizacion_angulo:
                resultado.append(AnnularSectorElement(
                    centroid_node=self.centroid_node,
                    boundary_angles_list=(angulo, angulo + discretizacion_angulo),
                    boundary_radii_list=(radio_final / 2, radio_final)))
                angulo = angulo + discretizacion_angulo
            i_inicial = i_inicial + 1

        for i_radii in range(i_inicial, n):
            radio = funcion_radii(i_radii)
            radio_final = funcion_radii(i_radii + 1)
            angulo = self.start_angle
            while angulo <= self.end_angle - discretizacion_angulo:
                resultado.append(AnnularSectorElement(
                    centroid_node=self.centroid_node,
                    boundary_angles_list=(angulo, angulo + discretizacion_angulo),
                    boundary_radii_list=(radio, radio_final)))
                angulo = angulo + discretizacion_angulo
        return resultado

    def remove_outside_elements(self, elements_list):
        """Remove elements that lay outside the Polygon limits."""
        for elemento_diferencial in elements_list.copy():
            if not self.is_node_in_annular_sector(elemento_diferencial.centroid_node):  # Fuera del semiplano del region.
                elements_list.remove(elemento_diferencial)
        return elements_list

    def is_node_inside_boundaries(self, nodo: Node):
        distancia_centro = self.centroid_node - nodo
        internal_radius_with_tolerance = max(self.internal_radius - TOLERANCE, 0.00)  # Avoiding negative values.
        return internal_radius_with_tolerance <= distancia_centro <= self.external_radius + TOLERANCE

    def is_node_inside_borderless_boundaries(self, nodo: Node):
        distancia_centro = self.centroid_node - nodo
        return self.internal_radius < distancia_centro < self.external_radius


class Region(Polygon):
    tipo = "Poligonal"

    def __init__(self, nodes: list, sign: int, indice, sort_nodes=False):
        self.sign = sign
        self.indice = indice
        super().__init__(nodes, sort_nodes=sort_nodes)

    def generate_mesh(self, dx, dy):
        """Generates the mesh based on contiguous RectangularElement"""
        elements_list = self._get_raw_list_of_elements(dx, dy)
        elements_list.sort(key=lambda element: (element.y, element.x))
        # Non-valid elements are removed
        lista_elem_validos = [elem for elem in elements_list if elem.area > TOLERANCE and (not (math.isnan(elem.xg) or math.isnan(elem.yg)))]
        return self.remove_outside_elements(
            lista_elem_validos)  # Additional filtering

    def _get_raw_list_of_elements(self, dx, dy):
        list_of_elements = []
        direction_vectors_list = [(1, 1), (1, -1), (-1, -1), (-1, 1)]
        for direccion in direction_vectors_list:
            x_partida = self.xg + direccion[0] * dx / 2
            y_partida = self.yg + direccion[1] * dy / 2
            list_of_elements = list_of_elements + self.elements_per_direction(x_partida, y_partida, dx, dy,
                                                                              direccion)
        return list_of_elements

    def elements_per_direction(self, x_partida, y_partida, dx, dy, direction: tuple):
        x_max, y_max = max(self.x), max(self.y)
        x_min, y_min = min(self.x), min(self.y)
        elements_list = []
        y_condition = lambda yp: yp - dy / 2 < y_max if direction[1] == 1 else yp + dy / 2 > y_min
        x_condition = lambda xp: xp - dx / 2 < x_max if direction[0] == 1 else xp + dx / 2 > x_min
        x = x_partida
        y = y_partida
        while y_condition(y):
            while x_condition(x):
                rectandultar_element = RectangularElement(ubicacion_centro=Node(x, y), medidas=(dx, dy))
                rectandultar_element = rectandultar_element.get_intersection_polygon(self)  # Trimming boundaries
                elements_list.append(rectandultar_element)
                x = x + direction[0] * dx
            y = y + direction[1] * dy
            x = x_partida
        return elements_list

    def remove_outside_elements(self, elements_list):
        """Remove elements from elements_list that lay outside the region."""
        for i, nodo in enumerate(self.boundary_nodes_list):
            node_1, node_2, node_3 = self._get_3_nodes_per_index(i)
            line_1_2 = Line(node_1, node_2)
            # The line equation returns numbers with the same sign for points on the same semi-plane.
            inside_semi_plane_sign = line_1_2.line_implicit_equation(node_3)
            if inside_semi_plane_sign == 0:
                raise Exception(
                    f"Por favor, ingresar puntos en el region que no estén alineados. Region de índice: {self.indice}")
            for element in elements_list.copy():
                element_semi_plane_sign = line_1_2.line_implicit_equation(element.centroid_node)
                if inside_semi_plane_sign * element_semi_plane_sign < 0:  # The element is outside the region.
                    elements_list.remove(element)
        return elements_list


class ArbitraryCrossSection(object):
    """An ArbitraryCrossSection combines Region elements.
    Elements with a positive sign represent solid web regions, while negative ones represent void regions."""

    def __init__(self, regions: dict, mesh_data):
        self.dx, self.dy, self.dr, self.d_ang = mesh_data
        self.void_regions_list = [region for i_region, region in regions.items() if region.sign == -1]
        self.solid_regions_list = [region for i_region, region in regions.items() if region.sign == 1]
        self.elements_list = self._get_solid_elements_list()
        self.area, self.xg, self.yg = self._compute_centroid_and_area()
        self.shift_coordinate_origin_to_centroid()
        self.Ix, self.Iy = self.compute_xy_moments_of_intertia()
        self.x_min, self.x_max, self.y_min, self.y_max = self.get_boundary_box_extremes()

    def _get_solid_elements_list(self):
        solid_elements_list = []
        for solid_regions in self.solid_regions_list:
            if solid_regions.tipo == "Poligonal":
                lista_elements_list_positivos = solid_regions.generate_mesh(self.dx, self.dy)
            else:  # Circular
                lista_elements_list_positivos = solid_regions.generate_mesh(discretizacion_angulo=self.d_ang,
                                                                                   discretizacion_radio=self.dr)
            for solid_element in lista_elements_list_positivos:
                if self.is_element_in_negative_region(
                        solid_element) or solid_element.area < TOLERANCE:
                    continue  # Discards element
                trimmed_element = self.intersect_solid_element_with_void_element(solid_element)
                if trimmed_element and trimmed_element.area > TOLERANCE:
                    solid_elements_list.append(trimmed_element)
        if len(solid_elements_list) == 0:
            raise Exception("Error en la generación de la geometría:\n"
                            "No se encontraron regions positivos por fuera de regions negativos.")
        return solid_elements_list

    def is_element_in_negative_region(self, solid_element: Polygon):
        for void_regionativo in self.void_regions_list:
            if solid_element.is_node_in_element(void_regionativo):  # Pertenece COMPLETAMENTE a element
                return True
        return False

    def intersect_solid_element_with_void_element(self, solid_element):
        if not(isinstance(solid_element, AnnularSectorElement)):
            for void_region in self.void_regions_list:
                solid_element = solid_element.substract_with_other_polygon(void_region)
                if solid_element is None:
                    return None
        return solid_element

    def _compute_centroid_and_area(self):
        area_total = 0
        sx = 0
        sy = 0
        for element in self.elements_list:
            area_total = area_total + element.area
            sx = sx + element.area * element.xg
            sy = sy + element.area * element.yg
        return round(area_total, 10), round(sx / area_total, 10), round(sy / area_total, 10)

    def compute_xy_moments_of_intertia(self):
        Ix = 0
        Iy = 0
        for element in self.elements_list:
            Ix = Ix + element.area * (element.yg**2)
            Iy = Iy + element.area * (element.xg**2)
        return round(Ix, 0), round(Iy, 0)

    def shift_coordinate_origin_to_centroid(self):
        for element in self.elements_list:
            element.translate_reference_frame(desp_x=-self.xg, desp_y=-self.yg)
        for region_pos in self.solid_regions_list:
            region_pos.translate_reference_frame(desp_x=-self.xg, desp_y=-self.yg)
        for void_region in self.void_regions_list:
            void_region.translate_reference_frame(desp_x=-self.xg, desp_y=-self.yg)

    def get_boundary_box_extremes(self):
        return min(x.xg for x in self.elements_list), max(x.xg for x in self.elements_list), min(x.yg for x in self.elements_list), max(x.yg for x in self.elements_list)

    def plotly(self, fig, planos_de_carga):
        plotly_util = ACSAHEPlotlyEngine(fig=fig)
        plotly_util.plot_cross_section(seccion=self, lista_de_angulos_plano_de_carga=planos_de_carga)
