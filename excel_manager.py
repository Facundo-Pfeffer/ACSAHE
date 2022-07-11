import openpyxl


class ExcelManager:
    def __init__(self, file_name):
        wb = openpyxl.load_workbook(file_name, data_only=True)
        self.sh = wb["Ingreso de Datos"]


    def get_value(self, row, column):
        return self.sh[f"{row}{column}"].value
