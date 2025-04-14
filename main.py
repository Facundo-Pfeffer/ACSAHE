import sys
import traceback
from tkinter import messagebox
from PyQt5.QtWidgets import QApplication
from gui.gui_launcher import ACSAHEUserInterface

if __name__ == '__main__':
    try:
        app = QApplication(sys.argv)
        window = ACSAHEUserInterface()
        window.init_ui()
        sys.exit(app.exec_())
    except Exception as e:
        traceback.print_exc()
        messagebox.showinfo("Error", str(e))
        print(e)
