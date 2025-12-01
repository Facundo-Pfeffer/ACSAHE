"""
LEGACY ENTRY POINT - Excel/VBA Integration
==========================================

This is the entry point for the legacy Excel/VBA integration version of ACSAHE.
This version is maintained but deprecated. New users should use the modern desktop version.

Modern version entry point: main.py
Legacy implementation: legacy/excel_input_acsahe.py
Build spec: ACSAHE_excel.spec

See LEGACY.md for detailed documentation.
"""

import sys
import traceback
from tkinter import messagebox
from PyQt5.QtWidgets import QApplication

from legacy.excel_input_acsahe import ExcelInputACSAHEGUI

if __name__ == '__main__':
    # Obtiene la ruta a la planilla
    path_exe = sys.argv[0]
    nombre_del_archivo = sys.argv[1].split("--wb=")[-1]
    path_archivo = '\\'.join(path_exe.split('\\')[:-2])
    file_path = path_archivo + "\\" + nombre_del_archivo
    #
    # path_archivo = "\\".join(path_exe.split("\\")[:-1])
    # nombre_del_archivo = "ACSAHE Drinco 2D.xlsm"

    app_gui = QApplication(sys.argv)
    try:
        # Start engine
        ex = ExcelInputACSAHEGUI(app_gui, nombre_del_archivo, path_archivo)
    except Exception as e:
        traceback.print_exc()
        messagebox.showinfo("Error", str(e))
        QApplication.quit()
