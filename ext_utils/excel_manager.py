import xlwings as xw


class ExcelManager:
    default_columns_range_value = tuple([chr(x) for x in range(65, 65+7)])  # Tuple from A to G
    default_rows_range_value = tuple(range(1, 400))

    def __init__(self, file_name, sheet_name):
        self.wb = xw.Book(file_name)
        self.sh = self.wb.sheets[sheet_name]

    def close(self):
        del self.wb

    def get_value(self, column, row):
        return self.sh.range(f"{column}{row}").value

    def change_cell_value_by_range(self, cell_address, new_value):
        self.sh.range(cell_address).value = new_value

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

    def insert_values_vertically(self, initial_cell, list_of_values, columns_to_clean=None, start_row=3):
        if columns_to_clean:
            for column in columns_to_clean:
                column_range = self.sh.range(f"{column}{start_row}").expand("down")
                column_range.clear()
        self.sh.range(initial_cell).value = list_of_values

    def calculate_new_range_by_coll_offset(self, original_range, column_offset):
        # Split the original range into start and end cells
        start_cell, end_cell = original_range.split(':')

        # Convert start and end cells into new start and end cells based on column offset
        new_start_cell = self.shift_cell_by_offset(start_cell, column_offset, 0)
        new_end_cell = self.shift_cell_by_offset(end_cell, column_offset, 0)

        # Return the new range in Excel format
        return f"{new_start_cell}:{new_end_cell}"

    def shift_cell_by_offset(self, cell, col_offset=0, row_offset=0):
        # Extract column letters and row number from the cell
        col_letters = ''.join(filter(str.isalpha, cell))
        row_number = ''.join(filter(str.isdigit, cell))

        # Convert the column letters to a number and apply the column offset
        new_col_num = self.col_letter_to_num(col_letters) + col_offset

        # Convert the new column number back to letters
        new_col_letters = self.col_num_to_letter(new_col_num)

        # Apply the row offset to the row number
        new_row_number = int(row_number) + row_offset

        # Construct and return the new cell reference
        return f"{new_col_letters}{new_row_number}"

    @staticmethod
    def col_letter_to_num(col_str):
        """Convert column letter(s) to a number."""
        num = 0
        for c in col_str.upper():
            num = num * 26 + (ord(c) - ord('A') + 1)
        return num

    @staticmethod
    def col_num_to_letter(col_num):
        """Convert a column number back to letter(s)."""
        col_str = ''
        while col_num > 0:
            col_num, remainder = divmod(col_num - 1, 26)
            col_str = chr(65 + remainder) + col_str
        return col_str

    def copy_paste_range(self, original_range, new_range):
        self.sh.range(original_range).copy(self.sh.range(new_range))

    def clear_contents_from_column(self, start_column_number, offset=0):
        # Find the last row and column
        last_column_letter = self.sh.range('XFD2').end('left').column
        if last_column_letter < start_column_number:
            last_column_letter = start_column_number

        start_column_letter = xw.utils.col_name(start_column_number)
        last_column_letter = xw.utils.col_name(last_column_letter+offset)

        # Define the range to clear
        range_to_clear = f"{start_column_letter}:{last_column_letter}"
        self.sh.range(range_to_clear).delete()

    def clear_contents_from_row(self, start_row_number, offset=0):
        # Find the last row and column
        last_row = self.sh.range('A1048576').end(
            'up').row  # Assuming Excel 2007 or later with a max of 1,048,576 rows
        if last_row < start_row_number:
            last_row = start_row_number

        # Define the range to clear
        start_row_number = max(start_row_number, 1)  # Ensure the start row is at least 1
        range_to_clear = f"A{start_row_number}:XFD{last_row + offset}"  # XFD is the last column in Excel
        self.sh.range(range_to_clear).clear_contents()
