import matplotlib.pyplot as plt


class Nodo(object):
    def __init__(self, x, y):
        self.x = x
        self.y = y

class Recta(object):
    def __init__(self, nodo_1: Nodo, nodo_2: Nodo):
        self.nodo_1 = nodo_1
        self.nodo_2 = nodo_2
        a,b,c = self.obtener_parametros_ecuacion_recta()
        self.ecuacion_recta = lambda nodo: a*nodo.x + b*nodo.y + c

    def obtener_parametros_ecuacion_recta(self):
        x1, y1 = self.nodo_1.x, self.nodo_1.y
        x2, y2 = self.nodo_2.x, self.nodo_2.y
        a = y1 - y2
        b = x2 - x1
        c = y2*(x1-x2) + (y2-y1)*x2
        return a,b,c


class RectanguloDiferencial(object):
    def __init__(self, ubicacion_centro: Nodo, medidas: tuple):
        a, b = medidas
        self.lado_1, self.lado_2 = a,b
        self.ubicacion_centro = ubicacion_centro
        self.x = ubicacion_centro.x
        self.y = ubicacion_centro.y
        self.area = a*b
        self.perimetro = 2*a + 2*b


class Contorno(object):
    def __init__(self, nodos: list, signo: int):
        self.x = [nodo.x for nodo in nodos]
        self.y = [nodo.y for nodo in nodos]
        self.nodos = nodos
        self.signo = signo
        self.total_de_nodos = len(nodos)

    def discretizar_contorno_como_rectangulo(self, dx, dy):
        lista_de_elementos = self.obtener_lista_de_elementos_preliminar(dx, dy)
        return self.eliminar_elementos_sobrestantes(lista_de_elementos)

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

    def eliminar_elementos_sobrestantes(self, lista_de_elementos):
        for i, nodo in enumerate(self.nodos):
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

    def obtener_3_nodos_x_indice(self, i_punto_1):
        """Obtiene el nodo en cuestión y los 2 nodos subsiguientes, basado en el índice del primer nodo.
        Al quedar algun índice fuera de rango, se obtiene el primer o segundo elemento según corresponda."""
        i_punto_2 = self.obtener_indice(i_punto_1, 1)
        i_punto_3 = self.obtener_indice(i_punto_1, 2)
        return self.nodos[i_punto_1], self.nodos[i_punto_2], self.nodos[i_punto_3]

    def obtener_indice(self, indice_punto_1, valor_a_sumar: int):
        i_punto = indice_punto_1 + valor_a_sumar
        return i_punto if i_punto < self.total_de_nodos else i_punto - self.total_de_nodos

    def mostrar_contorno_y_discretizacion(self, EEH):
        # Contorno
        X = [nodo.x for nodo in self.nodos]
        Y = [nodo.y for nodo in self.nodos]
        plt.plot(X, Y)
        x = [Elemento.x for Elemento in EEH]
        y = [Elemento.y for Elemento in EEH]
        plt.scatter(x, y, color="r", s=2, label="Discretizacion")
        plt.show()
