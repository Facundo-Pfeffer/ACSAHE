import xlwings as xw


class ExcelSheetManager:

    def __init__(self, sheet, rows_range=None, columns_range=None):
        self.sh = sheet
        self.default_columns_range_value = columns_range or tuple([chr(x) for x in range(65, 65 + 7)])  # A to G
        self.default_rows_range_value = rows_range or self._detect_last_row()

    def _detect_last_row(self):
        """
        Uses Excel's native used_range to get the last row with data.
        """
        try:
            last_row = self.sh.used_range.last_cell.row
            return tuple(range(1, last_row + 1))
        except Exception:
            print("Excel sheet values will be capped to 3000")
            return (1, 3000)  # fallback in case Excel is empty or throws error

    def get_value(self, column, row):
        return self.sh.range(f"{column}{row}").value

    def get_values_in_range(self, col_start, col_end, row_start, row_end):
        """Returns 2D list of values from a rectangular Excel range."""
        range_str = f"{col_start}{row_start}:{col_end}{row_end}"
        values = self.sh.range(range_str).value

        if not isinstance(values, list):
            return [[values]]
        if not isinstance(values[0], list):
            return [values]
        return values

    def get_column_values(self, column, row_start, row_end):
        """Returns 1D list of values in a single Excel column."""
        values = self.sh.range(f"{column}{row_start}:{column}{row_end}").value
        return values if isinstance(values, list) else [values]

    def change_cell_value_by_range(self, cell_address, new_value):
        self.sh.range(cell_address).value = new_value

    def find_cell_by_value(self, wanted_value, columns_range=None, rows_range=None):
        if columns_range is None:
            columns_range = self.default_columns_range_value
        if rows_range is None:
            rows_range = self.default_rows_range_value

        row_start, row_end = rows_range[0], rows_range[-1]
        for column in columns_range:
            values = self.get_column_values(column, row_start, row_end)
            for i, val in enumerate(values):
                if str(val).strip() == wanted_value:
                    return column, row_start + i  # First match
        return None, None

    def get_value_on_the_right(self, wanted_value, rows_range=None, n_column=1, row_offset=0, column_offset=0):
        if rows_range is None:
            rows_range = self.default_rows_range_value

        row_start, row_end = rows_range[0], rows_range[-1]
        col_start = self.default_columns_range_value[0]
        col_end = self.default_columns_range_value[-1]

        values = self.get_values_in_range(col_start, col_end, row_start, row_end)

        for i, row in enumerate(values):
            for j, val in enumerate(row):
                cell = str(val).strip() if isinstance(val, str) else val
                if cell == wanted_value:
                    target_col = j + n_column + column_offset
                    target_row = i + row_offset
                    if 0 <= target_col < len(row) and 0 <= target_row < len(values):
                        return values[target_row][target_col]
                    else:
                        return None
        return None

    def get_n_rows_after_value(self, wanted_value, number_of_rows_after_value,
                               columns_range=None, rows_range=None):
        if columns_range is None:
            columns_range = self.default_columns_range_value
        if rows_range is None:
            rows_range = self.default_rows_range_value

        start_row = rows_range[0]
        end_row = rows_range[-1]

        for column in columns_range:
            col_range_str = f"{column}{start_row}:{column}{end_row}"
            values = self.sh.range(col_range_str).value

            # Ensure list (sometimes single-cell returns just a value)
            if not isinstance(values, list):
                values = [values]

            for i, cell_value in enumerate(values):
                cell_text = str(cell_value).strip() if isinstance(cell_value, str) else cell_value
                if cell_text == wanted_value:
                    found_row = start_row + i
                    return list(range(found_row, found_row + number_of_rows_after_value))

        return []

    def get_rows_range_between_values(
            self, wanted_values_tuple, columns_range=None, rows_range=None):
        if columns_range is None:
            columns_range = self.default_columns_range_value
        if rows_range is None:
            rows_range = self.default_rows_range_value
        start_value, end_value = wanted_values_tuple
        range_start = range_end = 0
        row_start, row_end = rows_range[0], rows_range[-1]
        for column in columns_range:
            values = self.get_column_values(column, row_start, row_end)
            for i, val in enumerate(values):
                val_clean = str(val).strip() if isinstance(val, str) else val
                if val_clean == start_value and not range_start:
                    range_start = row_start + i
                elif val_clean == end_value and not range_end:
                    range_end = row_start + i
                if range_start and range_end:
                    break

        return list(range(range_start, range_end)) if range_start and range_end else []

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

        # Read the full column range in one call
        col_range_str = f"{column_letter}{row_range[0]}:{column_letter}{row_range[-1]}"
        values = self.sh.range(col_range_str).value

        # Normalize to a list (Excel may return a single value for 1 row)
        if not isinstance(values, list):
            values = [values]

        # Strip and search
        for i, cell_value in enumerate(values):
            cell_text = str(cell_value).strip() if cell_value is not None else ""
            if word in cell_text:
                row = row_range[0] + i
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

    def get_cell_combinations(self, columns_range=None, rows_range=None):
        if columns_range is None:
            columns_range = self.default_columns_range_value
        if rows_range is None:
            rows_range = self.default_rows_range_value

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
    def col_letter_to_num(col_str: str):
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


class ExcelManager:
    def __init__(self, file_path, read_only=True):
        self.app = xw.App(visible=False)
        self.app.display_alerts = False
        self.app.screen_updating = False
        self.wb = self.app.books.open(file_path, update_links=False, read_only=read_only)

    def get_sheet(self, sheet_name):
        return ExcelSheetManager(self.wb.sheets[sheet_name])

    def close(self):
        self.wb.close()
        self.app.quit()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
