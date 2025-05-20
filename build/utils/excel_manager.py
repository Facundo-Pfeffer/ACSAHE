import xlwings as xw
import os
import shutil
import tempfile
import unicodedata
from pathlib import Path


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

    def insert_column_values(self, column, start_row, values):
        """
        Efficiently writes a list of values vertically into one column using a single Excel call.
        """
        end_row = start_row + len(values) - 1
        range_str = f"{column}{start_row}:{column}{end_row}"
        self.sh.range(range_str).value = [[v] for v in values]  # column format

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
        cell_address = self.get_cell_address_on_the_right(wanted_value, rows_range, n_column, row_offset, column_offset)
        if not cell_address:
            return None
        return self.get_value(cell_address[0], cell_address[1])

    def get_cell_address_on_the_right(self, wanted_value, rows_range=None, n_column=1, row_offset=0, column_offset=0):
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
                        return xw.utils.col_name(target_col+1), target_row + row_start
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
                column_range.clear_contents()

        start = self.sh.range(initial_cell)
        n = len(list_of_values)
        target_range = start.resize(n, len(list_of_values[0]))

        # Extract formatting from the first cell
        fmt = {
            "font_name": start.font.name,
            "font_size": start.font.size,
            "bold": start.font.bold,
            "italic": start.font.italic,
            "color": start.font.color,
            "horizontal_alignment": start.api.HorizontalAlignment,
            "vertical_alignment": start.api.VerticalAlignment,
            "interior_color": start.color,
            "number_format": start.number_format,
            "borders": [   # Safely capturing borders before pasting. Avoiding .COM race conditions.
                {
                    "index": i,  # i 1 to 6: left, top, bottom, right, inside vertical, inside horizontal respectively.
                    "line_style": start.api.Borders(i).LineStyle,
                    "weight": start.api.Borders(i).Weight,
                    "color": start.api.Borders(i).Color,
                }
                for i in range(1, 4)
            ],
        }

        # Insert values in bulk
        self.sh.range(initial_cell).value = list_of_values

        # Restore formatting only on the first cell
        start.font.name = fmt["font_name"]
        start.font.size = fmt["font_size"]
        start.font.bold = fmt["bold"]
        start.font.italic = fmt["italic"]
        start.font.color = fmt["color"]
        start.api.HorizontalAlignment = fmt["horizontal_alignment"]
        start.api.VerticalAlignment = fmt["vertical_alignment"]
        start.color = fmt["interior_color"]
        start.number_format = fmt["number_format"]

        for border in fmt["borders"]:
            b = start.api.Borders(border["index"])
            if b is not None:
                if border["line_style"] is not None:
                    b.LineStyle = border["line_style"]
                if border["weight"] is not None:
                    b.Weight = border["weight"]
                if border["color"] is not None:
                    b.Color = border["color"]

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

    def delete_contents_from_column(self, start_column_number, offset=0):
        # Find the last row and column
        last_column_letter = self.sh.range('XFD2').end('left').column
        if last_column_letter < start_column_number:
            last_column_letter = start_column_number

        start_column_letter = xw.utils.col_name(start_column_number)
        last_column_letter = xw.utils.col_name(last_column_letter+offset)

        # Define the range to clear
        range_to_clear = f"{start_column_letter}:{last_column_letter}"
        self.sh.range(range_to_clear).delete()

    def clear_contents_from_column(self, start_column_number, offset=0, start_row=None, end_row=None):
        if not all([start_row, end_row]):
            start_row = end_row = ""

        # Find the last column used (in row 2)
        if not offset:
            last_column_index = self.sh.range('XFD2').end('left').column
            if last_column_index < start_column_number:
                last_column_index = start_column_number
            last_column_letter = xw.utils.col_name(last_column_index + offset)
        else:
            last_column_letter = xw.utils.col_name(start_column_number + offset)

        start_column_letter = xw.utils.col_name(start_column_number)

        # Define the range to clear (entire columns, but just values)
        range_to_clear = f"{start_column_letter}{start_row}:{last_column_letter}{end_row}"
        self.sh.range(range_to_clear).clear_contents()  # ✅ only clears values

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

    def clear_columns_from_row(self, columns, start_row_number, offset=0):
        """
        Efficiently clears contents from given columns starting at a specific row.

        Parameters:
            columns (list of str): e.g. ["I", "J", "K"]
            start_row_number (int): starting row to clear from.
            offset (int): optional extra rows beyond detected last row.
        """
        # Determine the last used row to cap the range
        last_row = self.sh.used_range.last_cell.row
        if last_row < start_row_number:
            last_row = start_row_number

        last_row += offset

        for col in columns:
            cell_range = f"{col}{start_row_number}:{col}{last_row}"
            self.sh.range(cell_range).clear_contents()

    def insert_lists_into_columns(self, start_row, columns, row_values_list):
        if len(columns) != len(row_values_list):
            raise ValueError("The number of columns must match the number of value lists.")

        for col_letter, values in zip(columns, row_values_list):
            self.insert_column_values(col_letter, start_row, values)


class ExcelManager:
    def __init__(self, file_path, read_only=True, visible=False):
        self.read_only = read_only
        if read_only is True:
            self.app = xw.App(visible=visible)
            self.app.display_alerts = False
            self.app.screen_updating = read_only
            self.read_only = read_only
            self.wb = self.safe_excel_open(self.app, file_path, read_only=read_only)
        else:
            self.wb = xw.Book(file_path)
            self.wb.save()

    def get_sheet(self, sheet_name):
        return ExcelSheetManager(self.wb.sheets[sheet_name])

    def close(self, save=True):
        if save and not self.read_only:
            self.wb.save()
            del self.wb
            return
        self.wb.close()
        if hasattr(self, "app"):
            self.app.quit()

    def __enter__(self):
        return self

    def safe_excel_open(self, app, file_path, read_only=True):
        """
        Open an Excel file in a safe environment, avoiding errors due to long paths or special characters.
        If a problematic path is detected, it copies the file to a temporary folder before opening it.
        """
        MAX_PATH = 240  # margen de seguridad bajo el límite de Windows
        file_path = Path(file_path)

        # Detectar si la ruta es peligrosa
        ruta_larga = len(str(file_path)) > MAX_PATH
        tiene_caracteres_raros = not self.is_ascii(str(file_path))

        if ruta_larga or tiene_caracteres_raros:
            temp_dir = Path(tempfile.gettempdir())
            clean_name = self.normalize_filename(file_path.name)
            temp_file = temp_dir / clean_name

            shutil.copy(file_path, temp_file)
            print(f"⚠️ Ruta compleja detectada. Archivo copiado a temporal: {temp_file}")
            file_to_open = temp_file
        else:
            file_to_open = file_path

        # Abrir con xlwings
        wb = app.books.open(str(file_to_open), update_links=False, read_only=read_only)
        return wb

    @staticmethod
    def is_ascii(s):
        try:
            s.encode('ascii')
            return True
        except UnicodeEncodeError:
            return False
    @staticmethod
    def normalize_filename(filename):
        """
        Elimina tildes y caracteres raros del nombre del archivo.
        """
        name, ext = os.path.splitext(filename)
        normalized = unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode()
        return f"{normalized}{ext}"

    def insert_data_into_multiple_sheets(self, sheet_names, columns_per_sheet, data_per_sheet, start_row=3, single_value_modifications=None):
        """
        Creates (or clones) sheets and inserts corresponding data into them efficiently.

        - If a sheet exists: reuse and clear contents.
        - If not: clone the first sheet (template) and rename.
        - All insertions use fewer Excel calls to minimize I/O.
        """
        if not (len(sheet_names) == len(columns_per_sheet) == len(data_per_sheet)):
            raise ValueError("Sheet names, columns per sheet, and data per sheet must have the same length.")

        template_sheet = self.wb.sheets[0]  # base sheet to copy formatting from

        for sheet_name, columns, data_lists in zip(sheet_names, columns_per_sheet, data_per_sheet):
            # Get or clone the sheet
            if sheet_name in [s.name for s in self.wb.sheets]:
                sheet = self.get_sheet(sheet_name)
                sheet.clear_columns_from_row(columns_per_sheet[0], 3)
            else:
                sheet = template_sheet.copy(after=self.wb.sheets[-1])
                sheet.name = sheet_name

            sheet_manager = self.get_sheet(sheet_name)
            sheet_manager.insert_lists_into_columns(
                start_row=start_row,
                columns=columns,
                row_values_list=data_lists
            )
            if single_value_modifications:
                sheet_manager.sh.range(single_value_modifications[0]).value = single_value_modifications[1]


def create_workbook_from_template(template_path, target_path, sheet_name=None):
    """
    Copies the first sheet of a template and saves it as a new file.

    Parameters:
        template_path (str): full path to the Excel template file.
        target_path (str): path where the new file should be saved.
        sheet_name (str): optional name for the copied sheet.
    """
    # Make a physical copy of the file to preserve formatting, styles, macros, etc.
    shutil.copyfile(template_path, target_path)

    # Rename the sheet if needed
    if sheet_name:
        app = xw.App(visible=False)
        wb = app.books.open(target_path)
        wb.sheets[0].name = sheet_name
        wb.save()
        wb.close()
        app.quit()
