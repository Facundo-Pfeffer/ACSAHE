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
        super().__init__()

    def launch_acsahe(self):
        from acsahe import ACSAHE
        file_path = self.excel_file_paths[0]
        file_name = os.path.basename(file_path)

        self.acsahe_instance = ACSAHE(
            app_gui=self,
            input_file_name=file_name,
            path_to_input_file=file_path,
            html_folder_path=self.html_folder_path if self.html_checkbox.isChecked() else None,
            pdf_folder_path=self.pdf_folder_path if self.pdf_checkbox.isChecked() else None
        )

    def init_ui(self):
        self.setup_window()
        font = QFont("Lato", 10)

        # Before Excel selector row
        excel_label = create_text_row(
            "Para comenzar, <a href=\"#\">cree un archivo ACSAHE</a> o seleccione al menos uno existente y presione \"Ejecutar ACSAHE\"",
            on_click=self.save_excel_template
        )

        excel_row, self.excel_button, _ = create_select_file_row(
            label_text="📁 Seleccionar archivo(s) Excel",
            object_name="excel_button",
            on_main_click=self.select_excel_file,
            include_reset=True,
            on_reset_click=self._reset_all_selections,
            spacing=1
        )

        excel_footer = create_text_row(
            "Generar nuevo archivo de entrada de datos",
            on_click=self.save_excel_template
        )

        html_row, self.html_checkbox, self.html_folder_button = create_checkbox_folder_row(
            checkbox_text="Guardar archivos .html ",
            checkbox_object_name="html_checkbox",
            tooltip_text="Activar si desea guardar los resultados interactivos .html del análisis en la carpeta destino.",
            button_text="📁 Seleccionar carpeta destino",
            button_object_name="html_folder_button",
            on_checkbox_toggle=self.toggle_html_folder,
            on_button_click=self.select_html_folder,
            button_alignment=Qt.AlignRight,
            button_fixed_width=350
        )

        pdf_row, self.pdf_checkbox, self.pdf_folder_button = create_checkbox_folder_row(
            checkbox_text="Generar reporte en PDF ",
            checkbox_object_name="pdf_checkbox",
            tooltip_text="Activar si se desea generar un informe en formato PDF con los resultados del análisis.",
            button_text="📁 Seleccionar carpeta destino",
            button_object_name="pdf_folder_button",
            on_checkbox_toggle=self.toggle_pdf_folder,
            on_button_click=self.select_pdf_folder,
            button_fixed_width=350
        )

        control_widgets = [
            excel_label,
            excel_row,
            # excel_footer,
            html_row,
            pdf_row,
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

    def create_logo(self):
        self.logoLabel = QLabel()
        logo_path = "build/images/LOGO ACSAHE.webp"
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path).scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.logoLabel.setPixmap(pixmap)
        self.logoLabel.setAlignment(Qt.AlignCenter)
        return self.logoLabel

    def create_excel_selector(self, font):
        self.excel_button = QPushButton("📁 Seleccionar archivo(s) Excel")
        self.excel_button.setFont(font)
        self.excel_button.setIcon(QIcon())  # Reset icon when default text is used
        self.excel_button.clicked.connect(self.select_excel_file)
        return self.excel_button

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

    def create_progress_bar(self, font):
        self.progress = QProgressBar(self)
        self.progress.setVisible(False)
        self.progress.setFont(font)
        self.estilo_barra_progreso()
        return self.progress

    def center(self):
        qr = self.frameGeometry()
        cp = QApplication.desktop().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def estilo_barra_progreso(self):
        with open("build/style/progress_bar.qss", "r", encoding="utf-8") as file:
            self.progress.setStyleSheet(file.read())

    def select_excel_file(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Seleccionar archivo(s) Excel", "",
                                                "Excel Files (*.xlsm *.xls *.xlsx)")
        if files:
            self.excel_file_paths = files
            display_names = ', '.join([os.path.basename(f) for f in files])
            icon_path = "build/icons/excel_icon.png"
            if os.path.exists(icon_path):
                self.excel_button.setIcon(QIcon(icon_path))
            self.excel_button.setText(f" {display_names}")
        else:
            self.excel_button.setText("📁 Seleccionar archivo(s) Excel")
            self.excel_button.setIcon(QIcon())

    def toggle_html_folder(self, state):
        self.html_folder_button.setEnabled(state == Qt.Checked)

    def toggle_pdf_folder(self, state):
        self.pdf_folder_button.setEnabled(state == Qt.Checked)

    def select_html_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta para .html")
        if folder:
            self.html_folder_path = folder
            self.html_folder_button.setText(f"📁 {os.path.basename(folder)}")

    def select_pdf_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta para PDF")
        if folder:
            self.pdf_folder_path = folder
            self.pdf_folder_button.setText(f"📁 {os.path.basename(folder)}")

    def start_processing(self):
        if not self._validate_folders_selected():
            return
        self._save_user_settings()
        self.message_label.setVisible(True)
        self.progress.setVisible(True)
        self.message_label.setText("Iniciando procesamiento...")
        self.progress.setValue(0)
        QApplication.processEvents()

        if hasattr(self, "excel_file_paths") and self.excel_file_paths:
            file_path = self.excel_file_paths[0]
            file_name = os.path.basename(file_path)

            self.thread = QThread()
            self.worker = ACSAHEWorker(
                file_name=file_name,
                file_path=file_path,
                html_folder_path=self.html_folder_path if self.html_checkbox.isChecked() else None,
                pdf_folder_path=self.pdf_folder_path if self.pdf_checkbox.isChecked() else None,
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

    def focus_window(self):
        if self.isMinimized():
            self.showNormal()
        self.raise_()
        self.activateWindow()

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

                self.excel_file_paths = config.get("excel_files", [])
                if self.excel_file_paths and all(Path(f).exists() for f in self.excel_file_paths):
                    display_names = ', '.join([os.path.basename(f) for f in self.excel_file_paths])
                    self.excel_button.setText(f"  {display_names}")
                icon_path = "build/icons/excel_icon.png"
                if os.path.exists(icon_path):
                    self.excel_button.setIcon(QIcon(icon_path))

                self.html_checkbox.setChecked(config.get("save_html", False))
                self.pdf_checkbox.setChecked(config.get("generate_pdf", False))

                html_path = config.get("html_folder", "")
                if html_path and Path(html_path).exists():
                    self.html_folder_path = html_path
                    self.html_folder_button.setText(f"📁 {os.path.basename(html_path)}")

                pdf_path = config.get("pdf_folder", "")
                if pdf_path and Path(pdf_path).exists():
                    self.pdf_folder_path = pdf_path
                    self.pdf_folder_button.setText(f"📁 {os.path.basename(pdf_path)}")
        except Exception as e:  # Message for debugging only, won't show to user.
            print(f"Failed to load user settings: {e}")

    def _save_user_settings(self):
        try:
            config = {
                "excel_files": getattr(self, "excel_file_paths", []),
                "save_html": self.html_checkbox.isChecked(),
                "generate_pdf": self.pdf_checkbox.isChecked(),
                "html_folder": getattr(self, "html_folder_path", ""),
                "pdf_folder": getattr(self, "pdf_folder_path", ""),
            }
            with open(self._get_config_path(), "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            print(f"Failed to save user settings: {e}")

    def _validate_folders_selected(self):
        if self.html_checkbox.isChecked() and not hasattr(self, "html_folder_path"):
            self.message_label.setVisible(True)
            self.message_label.setText("Por favor seleccione una carpeta para guardar los archivos .html")
            return False
        if self.pdf_checkbox.isChecked() and not hasattr(self, "pdf_folder_path"):
            self.message_label.setVisible(True)
            self.message_label.setText("Por favor seleccione una carpeta para guardar el PDF")
            return False
        return True

    def _reset_all_selections(self):
        self.excel_file_paths = []
        self.excel_button.setText("📁 Seleccionar archivo(s) Excel de entrada de datos.")
        self.excel_button.setIcon(QIcon())

        self.html_checkbox.setChecked(False)
        self.pdf_checkbox.setChecked(False)

        self.html_folder_path = ""
        self.html_folder_button.setText("📁 Seleccionar carpeta destino")

        self.pdf_folder_path = ""
        self.pdf_folder_button.setText("📁 Seleccionar carpeta destino")

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

            # Initialize list if empty
            if not hasattr(self, "excel_file_paths") or not isinstance(self.excel_file_paths, list):
                self.excel_file_paths = []

            # Append and deduplicate
            if save_path not in self.excel_file_paths:
                self.excel_file_paths.append(save_path)

            display_names = ', '.join([os.path.basename(f) for f in self.excel_file_paths])
            self.excel_button.setText(f" {display_names}")

            icon_path = "build/icons/excel_icon.png"
            if os.path.exists(icon_path):
                self.excel_button.setIcon(QIcon(icon_path))


class ACSAHEWorker(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal(str, int)

    def __init__(self, file_name, file_path, html_folder_path, pdf_folder_path, gui):
        super().__init__()
        self.input_file_name = file_name
        self.path_to_input_file = file_path
        self.html_folder_path = html_folder_path
        self.pdf_folder_path = pdf_folder_path
        self.gui = gui

    def showNormal(self):
        self.gui.showNormal()  # Restores the window if minimized

    def raise_(self):
        self.gui.raise_()  # Brings the window to the front

    def activateWindow(self):
        self.gui.activateWindow()  # Makes the window the active window

    def run(self):
        class GuiWrapper:
            def __init__(self, gui, signal):
                self.gui = gui
                self.signal = signal

            def update_ui(self, message=None, value=None):
                self.signal.emit(message, value)
                QTimer.singleShot(0, QApplication.processEvents)  # optional: process events right away

        wrapped_gui = GuiWrapper(self.gui, self.progress)
        ACSAHE(
            app_gui=wrapped_gui,
            input_file_name=self.input_file_name,
            path_to_input_file=self.path_to_input_file,
            html_folder_path=self.html_folder_path if hasattr(self, "html_folder_path") else None,
            pdf_folder_path=self.pdf_folder_path
        )
        self.finished.emit()
