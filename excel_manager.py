import xlwings as xw


class ExcelManager:

    default_columns_range_value = tuple([chr(x) for x in range(65, 65+7)])  # Tuple from A to G
    default_rows_range_value = tuple(range(1, 400))

    def __init__(self, file_name, sheet_name):
        self.wb = xw.Book(file_name)
        self.sh = self.wb.sheets[sheet_name]

    def get_value(self, column, row):
        return self.sh.range(f"{column}{row}").value

    def find_cell_by_value(self, wanted_value, columns_range=default_columns_range_value,
                           rows_range=default_rows_range_value):
        cells = self.get_cell_combinations(columns_range, rows_range)
        for column, row in cells:
            if self.get_value(column, row) == wanted_value:
                return column, row
        return None, None

    def get_value_on_the_right(self, wanted_value, rows_range=default_rows_range_value, n_column=1):
        column_initial, search_row = self.find_cell_by_value(wanted_value, rows_range=rows_range)
        if not column_initial:
            return None
        ascii_column_number = ord(column_initial) + n_column
        return self.get_value(chr(ascii_column_number), search_row)

    def get_n_rows_after_value(self, wanted_value, number_of_rows_after_value,
                               columns_range=default_columns_range_value, rows_range=default_rows_range_value):
        start_value = wanted_value
        range_start = 0
        cells = self.get_cell_combinations(columns_range, rows_range)
        for column_letter, row_number in cells:
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

    def subdivide_range_in_contain_word(self, column_letter, row_range, word):
        result = []
        subrange_start = None
        for row in row_range:
            if word in (str(self.get_value(column_letter, row)) or ""):
                if subrange_start is None:
                    subrange_start = row
                else:
                    result.append(list(range(subrange_start, row)))
                    subrange_start = row
        if subrange_start is not None:
            result.append(list(range(subrange_start, row_range[-1] + 1)))
        return result

    def cell_is_filled(self, column, row):
        value = self.sh.range(f"{column}{row}").color
        return value is not None

    def get_cell_combinations(self, columns_range=default_columns_range_value, rows_range=default_rows_range_value):
        result = []
        for column_letter in columns_range:
            for row_number in rows_range:
                result.append((column_letter, row_number))
        return result

    def add_plot(self, fig, location, **kwargs):
        plot = self.sh.pictures.add(fig, update=True, left=self.sh.range(location).left, top=self.sh.range(location).top, **kwargs)

    def insert_values_vertically(self, initial_cell, list_of_values):

        columns_to_clean = ['I', 'J', 'K']
        start_row = 3
        for column in columns_to_clean:
            column_range = self.sh.range(f"{column}{start_row}").expand("down")
            column_range.clear()

        self.sh.range(initial_cell).value = list_of_values
