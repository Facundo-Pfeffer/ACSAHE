import openpyxl


class ExcelManager:
    default_columns_range_value = tuple([chr(x) for x in range(65, 91)])  # Tupla de mayusculas de la A a la Z
    default_rows_range_value = tuple(range(1, 400))

    def __init__(self, file_name, sheet_name):
        wb = openpyxl.load_workbook(file_name, data_only=True)
        self.sh = wb[sheet_name]

    def get_value(self, column, row):
        return self.sh[f"{column}{row}"].value

    def find_cell_by_value(self, wanted_value, columns_range=default_columns_range_value,
                           rows_range=default_rows_range_value):
        celdas = self.get_cell_combinations(columns_range, rows_range)
        for column, row in celdas:
            if self.get_value(column, row) == wanted_value:
                return column, row
        return None, None

    def get_value_on_the_right(self, wanted_value, rows_range, limit_search=100):
        """Obtiene el valor de la primer celda que se encuentre a la derecha del contenido a buscar."""
        columna_inicial, fila_de_busqueda = self.find_cell_by_value(wanted_value, rows_range=rows_range)
        if not columna_inicial:
            return None
        numero_ascii_columna = ord(columna_inicial) + 1  # Valor inicial
        while numero_ascii_columna < limit_search:
            valor_celda = self.get_value(chr(numero_ascii_columna), fila_de_busqueda)
            if valor_celda and valor_celda != wanted_value:
                return valor_celda
            numero_ascii_columna = numero_ascii_columna + 1

    def get_n_rows_after_value(self, wanted_value: str, number_of_rows_after_value: int,
                               columns_range=default_columns_range_value, rows_range=default_rows_range_value):
        start_value = wanted_value
        range_start, range_end = 0, 0
        celdas = self.get_cell_combinations(columns_range, rows_range)
        for column_letter, row_number in celdas:
            cell_value = self.get_value(column_letter, row_number)
            if cell_value == start_value:
                range_start = row_number
                break
        if range_start:
            return list(range(range_start, range_start + number_of_rows_after_value))
        return []

    def get_rows_range_between_values(self, wanted_values_tuple, columns_range=default_columns_range_value,
                                      rows_range=default_rows_range_value):
        start_value, end_value = wanted_values_tuple
        range_start, range_end = 0, 0
        for column_letter in columns_range:
            for row_number in rows_range:
                cell_value = self.get_value(column_letter, row_number)
                if isinstance(cell_value, str):
                    cell_value = cell_value.strip()
                if cell_value == start_value:
                    range_start = row_number
                elif cell_value == end_value:
                    range_end = row_number
                    break
        if range_start and range_end:
            return list(range(range_start, range_end))
        return []

    def subdivide_range_in_filled_ranges(self, column_letter, row_range):
        """Subdivides the rows given by row_range in different ranges between formatted cells"""
        result = []
        subrange_start = None
        for row in row_range:
            if self.cell_is_filled(column_letter, row):
                if subrange_start is None:
                    subrange_start = row
                else:
                    result.append(list(range(subrange_start, row)))
                    subrange_start = row
        if subrange_start is not None:
            result.append(list(range(subrange_start, row_range[-1] + 1)))
        return result

    def cell_is_filled(self, column, row):
        value = self.sh[f"{column}{row}"].fill.bgColor.value
        return bool(int(value))  # Si es 0 (sin formato) devuelve Falso

    def get_cell_combinations(self, columns_range=default_columns_range_value, rows_range=default_rows_range_value):
        result = []
        for column_letter in columns_range:
            for row_number in rows_range:
                result.append((column_letter, row_number))
        return result
