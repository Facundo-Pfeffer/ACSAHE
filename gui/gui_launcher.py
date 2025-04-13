from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QProgressBar,
    QPushButton, QFileDialog, QCheckBox, QHBoxLayout,
    QFormLayout, QMainWindow
)

from PyQt5.QtGui import QIcon, QFont, QPixmap
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QObject


import sys
import os


class ACSAHEUserInterface(QMainWindow):
    def __init__(self):
        super().__init__()

    def launch_acsahe(self):
        from acsahe import ACSAHE
        file_path = self.excel_file_paths[0]
        file_name = os.path.basename(file_path)

        self.acsahe_instance = ACSAHE(
            app_gui=self,
            nombre_del_archivo=file_name,
            file_path=file_path,
            save_html=self.html_checkbox.isChecked(),
            generate_pdf=self.pdf_checkbox.isChecked()
        )

    def init_ui(self):
        self.setup_window()

        main_layout = QHBoxLayout()
        main_layout.setSpacing(30)
        main_layout.setContentsMargins(40, 20, 40, 20)
        main_layout.setAlignment(Qt.AlignTop)

        main_layout.addWidget(self.build_logo_section())
        main_layout.addLayout(self.build_controls_section())

        central_widget = QWidget()
        central_widget.setLayout(main_layout)

        self.setCentralWidget(central_widget)

        self.setStyleSheet(self.stylesheet())
        self.show()

    def build_logo_section(self):
        outer_container = QWidget()
        outer_layout = QVBoxLayout()
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)
        outer_layout.setAlignment(Qt.AlignVCenter | Qt.AlignHCenter)

        # Logo block
        logo_container = QWidget()
        logo_layout = QVBoxLayout()
        logo_layout.setContentsMargins(0, 0, 0, 0)
        logo_layout.setAlignment(Qt.AlignCenter)

        self.logoLabel = QLabel()
        self.logoLabel.setObjectName("logoLabel")
        logo_path = "build/images/LOGO ACSAHE.webp"
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path).scaled(280, 280, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.logoLabel.setPixmap(pixmap)
        self.logoLabel.setAlignment(Qt.AlignCenter)
        self.logoLabel.setFixedSize(280, 280)
        logo_layout.addWidget(self.logoLabel)
        logo_container.setLayout(logo_layout)

        # Credit block
        credit_container = QWidget()
        credit_layout = QVBoxLayout()
        credit_layout.setContentsMargins(0, 0, 0, 0)
        credit_layout.setAlignment(Qt.AlignBottom | Qt.AlignHCenter)

        label_text = (
            "Creado por el Ing. Facundo Pfeffer & el Dr. Ing. Oscar Möller.<br>"
            "2025 Universidad Nacional de Rosario<br>"
            "Protegido bajo la <a href='https://opensource.org/licenses/MIT'>Licencia MIT de código libre</a>."
        )
        self.creditsLabel = QLabel(label_text)
        self.creditsLabel.setTextFormat(Qt.RichText)
        self.creditsLabel.setOpenExternalLinks(True)
        self.creditsLabel.setAlignment(Qt.AlignCenter)
        self.creditsLabel.setStyleSheet("color: gray; font-size: 9px; margin-top: 6px; line-height: 1.1em;")
        credit_layout.addWidget(self.creditsLabel)
        credit_container.setLayout(credit_layout)

        outer_layout.addWidget(logo_container)
        outer_layout.addWidget(credit_container)
        outer_container.setLayout(outer_layout)
        return outer_container

    def build_controls_section(self):
        font = QFont("Lato", 10)
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)
        layout.addWidget(self.create_excel_selector(font))
        layout.addLayout(self.create_html_toggle(font))
        layout.addLayout(self.create_pdf_toggle(font))
        layout.addWidget(self.create_process_button(font))
        layout.addWidget(self.create_message_label(font))
        layout.addWidget(self.create_progress_bar(font))
        return layout

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
        self.excel_button.clicked.connect(self.select_excel_file)
        return self.excel_button

    def create_html_toggle(self, font):
        folder_label = "📁 Seleccionar carpeta destino"
        hover_text_str = "Activar si desea guardar los resultados interactivos .html del análisis en la carpeta destino."
        layout = QHBoxLayout()
        self.html_checkbox = QCheckBox("Guardar archivos .html")
        self.html_checkbox.setFont(font)
        self.html_checkbox.stateChanged.connect(self.toggle_html_folder)
        html_help = self.create_help_icon(hover_text_str)
        html_help.setToolTip(hover_text_str)
        self.html_folder_button = QPushButton(folder_label)
        self.html_folder_button.setFont(font)
        self.html_folder_button.setEnabled(False)
        self.html_folder_button.clicked.connect(self.select_html_folder)
        html_label_wrapper = QWidget()
        html_label_layout = QHBoxLayout()
        html_label_layout.setContentsMargins(0, 0, 0, 0)
        html_label_layout.setSpacing(2)
        html_label_layout.setSpacing(2)
        html_label_layout.setContentsMargins(0, 0, 0, 0)
        html_label_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        html_label_layout.addWidget(self.html_checkbox)
        html_label_layout.addWidget(html_help)
        html_label_wrapper.setLayout(html_label_layout)
        layout.addWidget(html_label_wrapper)
        layout.addWidget(self.html_folder_button)
        return layout

    def create_pdf_toggle(self, font):
        displayed_str = "📁 Seleccionar carpeta destino"
        hover_text_str = "Activar si se desea genearar un informe .pdf con los resultados del análisis."
        layout = QHBoxLayout()
        self.pdf_checkbox = QCheckBox("Generar reporte PDF")
        self.pdf_checkbox.setFont(font)
        self.pdf_checkbox.stateChanged.connect(self.toggle_pdf_folder)
        pdf_help = self.create_help_icon("Activa esta opción para generar un informe en formato PDF.")
        pdf_help.setToolTip("Activa esta opción para generar un informe en formato PDF.")
        self.pdf_folder_button = QPushButton(displayed_str)
        self.pdf_folder_button.setFont(font)
        self.pdf_folder_button.setEnabled(False)
        self.pdf_folder_button.clicked.connect(self.select_pdf_folder)
        pdf_label_wrapper = QWidget()
        pdf_label_layout = QHBoxLayout()
        pdf_label_layout.setContentsMargins(0, 0, 0, 0)
        pdf_label_layout.setSpacing(2)
        pdf_label_layout.setSpacing(2)
        pdf_label_layout.setContentsMargins(0, 0, 0, 0)
        pdf_label_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        pdf_label_layout.addWidget(self.pdf_checkbox)
        pdf_label_layout.addWidget(pdf_help)
        pdf_label_layout.setContentsMargins(0, 0, 0, 0)
        pdf_label_layout.setSpacing(2)
        pdf_label_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        pdf_label_wrapper.setLayout(pdf_label_layout)
        layout.addWidget(pdf_label_wrapper)
        layout.addWidget(self.pdf_folder_button)
        return layout

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

    def stylesheet(self):
        with open("build/style/acsahe.qss", "r", encoding="utf-8") as file:
            return file.read()
        self.setWindowTitle("ACSAHE")
        self.resize(650, 600)
        self.setWindowIcon(QIcon("build/images/Logo H.webp"))
        self.center()

        layout = QVBoxLayout()
        font = QFont("Lato", 10)

        # Logo
        self.logoLabel = QLabel()
        logo_path = "build/images/LOGO ACSAHE.webp"
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path).scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.logoLabel.setPixmap(pixmap)
        self.logoLabel.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.logoLabel)

        # Excel File Selection
        self.excel_button = QPushButton("📁 Seleccionar archivo(s) Excel")
        self.excel_button.setFont(font)
        self.excel_button.clicked.connect(self.select_excel_file)
        layout.addWidget(self.excel_button)

        # Save HTML toggle
        html_layout = QHBoxLayout()
        self.html_checkbox = QCheckBox("Guardar archivos .html")
        self.html_checkbox.setFont(font)
        self.html_checkbox.stateChanged.connect(self.toggle_html_folder)
        html_help = QLabel()
        html_help.setCursor(Qt.WhatsThisCursor)
        html_icon_path = "build/images/question-512.webp"
        if os.path.exists(html_icon_path):
            pixmap = QPixmap(html_icon_path).scaled(22, 22, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            html_help.setPixmap(pixmap)
        html_help.setToolTip("Activa esta opción para guardar los archivos interactivos .html del análisis.")
        self.html_folder_button = QPushButton(folder_label)
        self.html_folder_button.setFont(font)
        self.html_folder_button.setEnabled(False)
        self.html_folder_button.clicked.connect(self.select_html_folder)
        html_layout.addWidget(self.html_checkbox)
        html_layout.addWidget(html_help)
        html_layout.addWidget(self.html_folder_button)
        layout.addLayout(html_layout)

        # Generate PDF toggle
        pdf_layout = QHBoxLayout()
        self.pdf_checkbox = QCheckBox("Generar reporte PDF")
        self.pdf_checkbox.setFont(font)
        self.pdf_checkbox.stateChanged.connect(self.toggle_pdf_folder)
        pdf_help = QLabel()
        pdf_help.setCursor(Qt.WhatsThisCursor)
        pdf_icon_path = "build/images/question-512.webp"
        if os.path.exists(pdf_icon_path):
            pixmap = QPixmap(pdf_icon_path).scaled(22, 22, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            pdf_help.setPixmap(pixmap)
        pdf_help.setToolTip("Activa esta opción para generar un informe en formato PDF.")
        self.pdf_folder_button = QPushButton("📁 Seleccionar carpeta destino")
        self.pdf_folder_button.setFont(font)
        self.pdf_folder_button.setEnabled(False)
        self.pdf_folder_button.clicked.connect(self.select_pdf_folder)
        pdf_layout.addWidget(self.pdf_checkbox)
        pdf_layout.addWidget(pdf_help)
        pdf_layout.addWidget(self.pdf_folder_button)
        layout.addLayout(pdf_layout)

        # Process Button
        self.process_button = QPushButton(label_execute)
        self.process_button.setFont(QFont("Lato", 11, QFont.Bold))
        self.process_button.setFixedHeight(40)
        self.process_button.clicked.connect(self.start_processing)
        layout.addWidget(self.process_button)

        # Progress Message
        self.message_label = QLabel("", self)
        self.message_label.setVisible(False)
        self.message_label.setFont(font)
        self.message_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.message_label)

        # Progress Bar
        self.progress = QProgressBar(self)
        self.progress.setVisible(False)
        self.progress.setFont(font)
        layout.addWidget(self.progress)
        self.estilo_barra_progreso()

        self.setLayout(layout)
        self.setStyleSheet(self.stylesheet())
        self.show()

    def center(self):
        qr = self.frameGeometry()
        cp = QApplication.desktop().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def create_help_icon(self, tooltip_text):
        icon_label = QLabel()
        icon_label.setCursor(Qt.WhatsThisCursor)
        icon_label.setFixedSize(28, 28)
        icon_label.setStyleSheet("padding: 0px; margin: 0px;")
        icon_path = "build/images/question-512.webp"
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path).scaled(28, 28, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            icon_label.setPixmap(pixmap)
        icon_label.setToolTip(tooltip_text)
        return icon_label

    def estilo_barra_progreso(self):
        with open("build/style/progress_bar.qss", "r", encoding="utf-8") as file:
            self.progress.setStyleSheet(file.read())

    def select_excel_file(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Seleccionar archivo(s) Excel", "", "Excel Files (*.xlsm *.xls *.xlsx)")
        if files:
            self.excel_file_paths = files
            display_names = ', '.join([os.path.basename(f) for f in files])
            self.excel_button.setText(f"📊 {display_names}")

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
                save_html=self.html_checkbox.isChecked(),
                generate_pdf=self.pdf_checkbox.isChecked(),
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

    def update_progress_message(self, message):
        self.message_label.setVisible(True)
        self.message_label.setText(message)
        QApplication.processEvents()

    def update_progress_value(self, value):
        self.progress.setVisible(True)
        self.progress.setValue(value)
        QApplication.processEvents()


class ACSAHEWorker(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal(str, int)

    def __init__(self, file_name, file_path, save_html, generate_pdf, gui):
        super().__init__()
        self.file_name = file_name
        self.file_path = file_path
        self.save_html = save_html
        self.generate_pdf = generate_pdf
        self.gui = gui

    def showNormal(self):
        self.gui.showNormal()  # Restores the window if minimized

    def raise_(self):
        self.gui.raise_()  # Brings the window to the front

    def activateWindow(self):
        self.gui.activateWindow()  # Makes the window the active window

    def run(self):
        from acsahe import ACSAHE

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
            nombre_del_archivo=self.file_name,
            file_path=self.file_path,
            save_html=self.save_html,
            generate_pdf=self.generate_pdf
        )
        self.finished.emit()

