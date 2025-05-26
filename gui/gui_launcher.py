from PyQt5.QtWidgets import (
    QApplication, QFileDialog, QMainWindow
)
from PyQt5.QtCore import QTimer, QThread, pyqtSignal, QObject
import json
from pathlib import Path

from acsahe import ACSAHE
from gui.gui_utils import *


class ACSAHEUserInterface(QMainWindow):
    def __init__(self):
        self.acsahe_instance = None
        super().__init__()

    def launch_acsahe(self):
        file_path = self.main_excel_file_path_list[0]
        file_name = os.path.basename(file_path)
        self.acsahe_instance = ACSAHE(
            app_gui=self,
            input_file_name=file_name,
            path_to_input_file=file_path,
            html_folder_path=self.html_folder_path if self.html_checkbox.isChecked() else None,
            excel_folder_path=self.excel_folder_path if self.excel_checkbox.isChecked() else None,
            docx_folder_path=self.docx_folder_path if self.docx_checkbox.isChecked() else None
        )

    def init_ui(self):
        self.setup_window()
        font = QFont("Lato", 10)

        # Before Excel selector row
        excel_label = create_text_row(
            "Para comenzar, <a href=\"#\">cree un archivo ACSAHE</a> o seleccione al menos uno existente y presione \"Ejecutar ACSAHE\"",
            on_click=self.save_excel_template
        )

        excel_row, self.main_excel_button, _ = create_select_file_row(
            label_text="📁 Seleccionar archivo(s) Excel",
            object_name="excel_button",
            on_main_click=self.select_excel_file,
            include_reset=True,
            on_reset_click=self._reset_all_selections,
            spacing=1
        )

        html_row, self.html_checkbox, self.html_folder_button = create_checkbox_folder_row(
            checkbox_text="Guardar archivos resultado .html ",
            checkbox_object_name="html_checkbox",
            tooltip_text="Activar si desea guardar los resultados interactivos .html del análisis en la carpeta destino.",
            button_text="📁 Seleccionar carpeta destino",
            button_object_name="html_folder_button",
            on_checkbox_toggle=self.toggle_html_folder,
            on_button_click=self.select_html_folder,
            button_alignment=Qt.AlignRight,
            button_fixed_width=350
        )

        excel_result_row, self.excel_checkbox, self.excel_folder_button = create_checkbox_folder_row(
            checkbox_text="Volcar resultados en planilla Excel ",
            checkbox_object_name="excel_checkbox",
            tooltip_text="Activar si desea guardar los resultados numéricos en un archivo Excel.",
            button_text="📁 Seleccionar carpeta destino",
            button_object_name="excel_folder_button",
            on_checkbox_toggle=self.toggle_excel_folder,
            on_button_click=self.select_excel_folder,
            button_alignment=Qt.AlignRight,
            button_fixed_width=350
        )

        docx_row, self.docx_checkbox, self.docx_folder_button = create_checkbox_folder_row(
            checkbox_text="Generar reporte en Word ",
            checkbox_object_name="docx_checkbox",
            tooltip_text="Activar si se desea generar un informe en formato docx con los resultados del análisis.",
            button_text="📁 Seleccionar carpeta destino",
            button_object_name="docx_folder_button",
            on_checkbox_toggle=self.toggle_docx_folder,
            on_button_click=self.select_docx_folder,
            button_fixed_width=350
        )

        control_widgets = [
            excel_label,
            excel_row,
            # excel_footer,
            html_row,
            excel_result_row,
            docx_row,
            self.create_process_button(font),
            self.create_message_label(font),
            self.create_progress_bar(font)
        ]

        main_layout = create_main_layout_with_logo_and_controls(
            logo_widget=create_logo_section(
                logo_path="build/images/LOGO ACSAHE.webp",
                logo_size=280,
                below_text_html=(
                    "Creado por el Ing. Facundo Pfeffer & el Dr. Ing. Oscar Möller.<br>"
                    "2025. Universidad Nacional de Rosario<br>"
                    "Protegido bajo la <a href='https://opensource.org/licenses/MIT'>Licencia MIT de código libre</a>."
                )
            ),
            control_widgets=control_widgets
        )

        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        self.setStyleSheet(load_stylesheet("build/style/acsahe.qss"))
        self.show()
        self._load_user_settings()

    def setup_window(self):
        self.setWindowTitle("ACSAHE")
        self.resize(900, 300)
        self.setWindowIcon(QIcon("build/images/Logo H.webp"))
        self.center()

    def create_progress_bar(self, font):
        self.progress = QProgressBar(self)
        self.progress.setVisible(False)
        self.progress.setFont(font)
        self._set_progress_bar_style()
        return self.progress

    def create_process_button(self, font):
        label_execute = "Ejecutar ACSAHE"
        self.process_button = QPushButton(label_execute)
        self.process_button.setFont(QFont("Lato", 11, QFont.Bold))
        self.process_button.setFixedHeight(40)
        self.process_button.clicked.connect(self.start_processing)
        return self.process_button

    def create_message_label(self, font):
        self.message_label = QLabel("", self)
        self.message_label.setVisible(False)
        self.message_label.setFont(font)
        self.message_label.setAlignment(Qt.AlignCenter)
        return self.message_label

    def _set_progress_bar_style(self):
        with open("build/style/progress_bar.qss", "r", encoding="utf-8") as file:
            self.progress.setStyleSheet(file.read())

    def center(self):
        qr = self.frameGeometry()
        cp = QApplication.desktop().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def select_excel_file(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Seleccionar archivo(s) Excel", "",
                                                "Excel Files (*.xlsm *.xls *.xlsx)")
        if files:
            self.main_excel_file_path_list = files
            display_names = ', '.join([os.path.basename(f) for f in files])
            icon_path = "build/icons/excel_icon.png"
            if os.path.exists(icon_path):
                self.main_excel_button.setIcon(QIcon(icon_path))
            self.main_excel_button.setText(f" {display_names}")
        else:
            self.main_excel_button.setText("📁 Seleccionar archivo(s) Excel")
            self.main_excel_button.setIcon(QIcon())

    def toggle_html_folder(self, state):
        self.html_folder_button.setEnabled(state == Qt.Checked)

    def toggle_excel_folder(self, state):
        self.excel_folder_button.setEnabled(state == Qt.Checked)

    def toggle_docx_folder(self, state):
        self.docx_folder_button.setEnabled(state == Qt.Checked)

    def select_html_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta para archivo .html")
        if folder:
            self.html_folder_path = folder
            self.html_folder_button.setText(f"📁 {os.path.basename(folder)}")

    def select_excel_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta para archivo .xls")
        if folder:
            self.excel_folder_path = folder
            self.excel_folder_button.setText(f"📁 {os.path.basename(folder)}")

    def select_docx_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta para archivo .docx")
        if folder:
            self.docx_folder_path = folder
            self.docx_folder_button.setText(f"📁 {os.path.basename(folder)}")

    def start_processing(self):
        if not self._validate_folders_selected():
            return
        self._save_user_settings()
        self.message_label.setVisible(True)
        self.progress.setVisible(True)
        self.message_label.setText("Iniciando procesamiento...")
        self.progress.setValue(0)
        QApplication.processEvents()

        if hasattr(self, "main_excel_file_path_list") and self.main_excel_file_path_list:
            file_path = self.main_excel_file_path_list[0]
            file_name = os.path.basename(file_path)

            self.thread = QThread()
            self.worker = ACSAHEWorker(
                file_name=file_name,
                file_path=file_path,
                html_folder_path=self.html_folder_path if self.html_checkbox.isChecked() else None,
                excel_folder_path=self.excel_folder_path if self.excel_checkbox.isChecked() else None,
                docx_folder_path=self.docx_folder_path if self.docx_checkbox.isChecked() else None,
                gui=self
            )
            self.worker.moveToThread(self.thread)

            self.worker.progress.connect(self.update_progress_ui)
            self.thread.started.connect(self.worker.run)
            self.worker.finished.connect(self.thread.quit)
            self.worker.finished.connect(self.worker.deleteLater)
            self.thread.finished.connect(self.thread.deleteLater)

            self.thread.start()
        else:
            self.message_label.setText("Por favor, seleccione al menos un archivo Excel.")

    def update_progress_ui(self, message, value):
        self.message_label.setVisible(True)
        self.progress.setVisible(True)
        self.message_label.setText(message)
        self.progress.setValue(value)
        self.progress.repaint()
        QApplication.processEvents()

    def _get_config_path(self):
        settings_dir = Path("build/user_settings")
        settings_dir.mkdir(parents=True, exist_ok=True)
        return settings_dir / "acsahe_config.json"

    def _load_user_settings(self):
        try:
            config_path = self._get_config_path()
            if config_path.exists():
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)

                self.main_excel_file_path_list = config.get("excel_files", [])
                if self.main_excel_file_path_list and all(Path(f).exists() for f in self.main_excel_file_path_list):
                    display_names = ', '.join([os.path.basename(f) for f in self.main_excel_file_path_list])
                    self.main_excel_button.setText(f"  {display_names}")
                icon_path = "build/icons/excel_icon.png"
                if os.path.exists(icon_path):
                    self.main_excel_button.setIcon(QIcon(icon_path))

                self.html_checkbox.setChecked(config.get("save_html", False))
                self.excel_checkbox.setChecked(config.get("generate_excel", False))
                self.docx_checkbox.setChecked(config.get("generate_docx", False))

                html_path = config.get("html_folder", "")
                if html_path and Path(html_path).exists():
                    self.html_folder_path = html_path
                    self.html_folder_button.setText(f"📁 {os.path.basename(html_path)}")

                excel_path = config.get("excel_folder", "")
                if excel_path and Path(excel_path).exists():
                    self.excel_folder_path = excel_path
                    self.excel_folder_button.setText(f"📁 {os.path.basename(excel_path)}")

                docx_path = config.get("docx_folder", "")
                if docx_path and Path(docx_path).exists():
                    self.docx_folder_path = docx_path
                    self.docx_folder_button.setText(f"📁 {os.path.basename(docx_path)}")
        except Exception as e:  # Message for debugging only, won't show to user.
            print(f"Failed to load user settings: {e}")

    def _save_user_settings(self):
        config = {
            "excel_files": getattr(self, "main_excel_file_path_list", []),
            "save_html": self.html_checkbox.isChecked(),
            "generate_excel": self.excel_checkbox.isChecked(),
            "generate_docx": self.docx_checkbox.isChecked(),
            "html_folder": getattr(self, "html_folder_path", ""),
            "excel_folder": getattr(self, "excel_folder_path", ""),
            "docx_folder": getattr(self, "docx_folder_path", ""),
        }
        try:
            with open(self._get_config_path(), "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            print(f"Failed to save user settings: {e}")

    def _validate_folders_selected(self):
        if self.html_checkbox.isChecked() and not hasattr(self, "html_folder_path"):
            self.message_label.setVisible(True)
            self.message_label.setText("Por favor seleccione una carpeta para guardar los archivos .html")
            return False
        if self.excel_checkbox.isChecked() and not hasattr(self, "excel_folder_path"):
            self.message_label.setVisible(True)
            self.message_label.setText("Por favor seleccione una carpeta para guardar los archivos .xls")
            return False
        if self.docx_checkbox.isChecked() and not hasattr(self, "docx_folder_path"):
            self.message_label.setVisible(True)
            self.message_label.setText("Por favor seleccione una carpeta para guardar el docx")
            return False
        return True

    def _reset_all_selections(self):
        self.main_excel_file_path_list = []
        self.main_excel_button.setText("📁 Seleccionar archivo(s) Excel de entrada de datos.")
        self.main_excel_button.setIcon(QIcon())

        self.html_checkbox.setChecked(False)
        self.excel_checkbox.setChecked(False)
        self.docx_checkbox.setChecked(False)

        self.html_folder_path = ""
        self.html_folder_button.setText("📁 Seleccionar carpeta destino")

        self.excel_folder_path = ""
        self.excel_folder_button.setText("📁 Seleccionar carpeta destino")

        self.docx_folder_path = ""
        self.docx_folder_button.setText("📁 Seleccionar carpeta destino")

    def save_excel_template(self):
        default_path = os.path.join(str(Path.home()), "ACSAHE.xlsm")
        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Seleccione dónde guardar el archivo de entrada de datos. Se recomienda modificar el nombre.",
            default_path,
            "Excel Files (*.xlsm)"
        )
        if save_path:
            from shutil import copyfile
            copyfile("build/ACSAHE.xlsm", save_path)

            if not hasattr(self, "main_excel_file_path_list") or not isinstance(self.main_excel_file_path_list, list):
                self.main_excel_file_path_list = [] # Initialize if empty

            # Append and deduplicate
            if save_path not in self.main_excel_file_path_list:
                self.main_excel_file_path_list.append(save_path)

            display_names = ', '.join([os.path.basename(f) for f in self.main_excel_file_path_list])
            self.main_excel_button.setText(f" {display_names}")

            icon_path = "build/icons/excel_icon.png"
            if os.path.exists(icon_path):
                self.main_excel_button.setIcon(QIcon(icon_path))

class GuiWrapper:
    def __init__(self, gui, signal):
        self.gui = gui
        self.signal = signal

    def update_ui(self, message=None, value=None):
        self.signal.emit(message, value)
        QTimer.singleShot(0, QApplication.processEvents)

class ACSAHEWorker(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal(str, int)

    def __init__(self, file_name, file_path, html_folder_path, excel_folder_path, docx_folder_path, gui):
        super().__init__()
        self.input_file_name = file_name
        self.path_to_input_file = file_path
        self.html_folder_path = html_folder_path
        self.excel_folder_path = excel_folder_path
        self.docx_folder_path = docx_folder_path
        self.gui = gui

    def showNormal(self):
        self.gui.showNormal()  # Restores the window if minimized

    def raise_(self):
        self.gui.raise_()  # Brings the window to the front

    def activateWindow(self):
        self.gui.activateWindow()  # Makes the window the active window

    def run(self):
        try:
            wrapped_gui = GuiWrapper(self.gui, self.progress)
            ACSAHE(
                app_gui=wrapped_gui,
                input_file_name=self.input_file_name,
                path_to_input_file=self.path_to_input_file,
                html_folder_path=self.html_folder_path if hasattr(self, "html_folder_path") else None,
                excel_folder_path=self.excel_folder_path,
                docx_folder_path=self.docx_folder_path
            )
        except Exception as e:
            from tkinter import messagebox
            messagebox.showinfo("Error", str(e))
            self.error.emit(str(e))
        finally:
            self.finished.emit()
