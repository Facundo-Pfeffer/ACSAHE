import sys
from diagramas_de_interaccion import ObtenerDiagramaDeInteraccion2D, ObtenerDiagramaDeInteraccion3D
from tkinter import messagebox


# Function to show the message box
def show_message(message, titulo="Mensaje"):
    messagebox.showinfo(titulo, message)


if __name__ == '__main__':
    path_to_exe = sys.argv[0]
    file_name = sys.argv[1].split("--wb=")[-1]
    path_to_file = '\\'.join(path_to_exe.split('\\')[:-2])
    file_path = path_to_file + "\\" + file_name

    show_message(path_to_exe)
    show_message(file_name)
    show_message(path_to_file)
    show_message(file_path)

    # file_path = "ACSAHE.xlsm"
    resolver = ObtenerDiagramaDeInteraccion2D(file_path=file_path)
