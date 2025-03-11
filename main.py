import sys
import traceback
from tkinter import messagebox
from PyQt5.QtWidgets import QApplication

from acsahe import ACSAHE

if __name__ == '__main__':
    # Obtiene la ruta a la planilla
    path_exe = sys.argv[0]
    nombre_del_archivo = sys.argv[1].split("--wb=")[-1]
    path_archivo = '\\'.join(path_exe.split('\\')[:-2])
    file_path = path_archivo + "\\" + nombre_del_archivo
    # app es un manager del GUI (graphical user interface - interfaz con el usuario)
    app_gui = QApplication(sys.argv)
    try:
        # Start engine
        ex = ACSAHE(app_gui, nombre_del_archivo, path_archivo)
    except Exception as e:
        traceback.print_exc()
        messagebox.showinfo("Error", str(e))
        QApplication.quit()
