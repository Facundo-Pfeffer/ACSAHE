from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QProgressBar,
    QPushButton, QFileDialog, QCheckBox, QHBoxLayout,
    QFormLayout
)
from PyQt5.QtGui import QIcon, QFont, QPixmap
from PyQt5.QtCore import Qt
import sys
import os


class ACSAHEUserInterface(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setup_window()

        main_layout = QHBoxLayout()
        main_layout.setSpacing(30)
        main_layout.setContentsMargins(20, 20, 20, 20)

        main_layout.addWidget(self.build_logo_section())
        main_layout.addLayout(self.build_controls_section())

        self.setLayout(main_layout)
        self.setStyleSheet(self.stylesheet())
        self.show()

    def build_logo_section(self):
        self.logoLabel = QLabel()
        self.logoLabel.setObjectName("logoLabel")
        logo_path = "build/images/LOGO ACSAHE.webp"
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path).scaled(300, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.logoLabel.setPixmap(pixmap)
        self.logoLabel.setAlignment(Qt.AlignCenter)
        self.logoLabel.setFixedWidth(320)
        return self.logoLabel

    def build_controls_section(self):
        font = QFont("Lato", 10)
        layout = QVBoxLayout()
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
        layout = QHBoxLayout()
        self.html_checkbox = QCheckBox("Guardar archivos .html")
        self.html_checkbox.setFont(font)
        self.html_checkbox.stateChanged.connect(self.toggle_html_folder)
        html_help = self.create_help_icon("Activa esta opción para guardar los archivos interactivos .html del análisis.")
        html_help.setToolTip("Activa esta opción para guardar los archivos interactivos .html del análisis.")
        self.html_folder_button = QPushButton("📁 Seleccionar carpeta destino")
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
        layout = QHBoxLayout()
        self.pdf_checkbox = QCheckBox("Generar reporte PDF")
        self.pdf_checkbox.setFont(font)
        self.pdf_checkbox.stateChanged.connect(self.toggle_pdf_folder)
        pdf_help = self.create_help_icon("Activa esta opción para generar un informe en formato PDF.")
        pdf_help.setToolTip("Activa esta opción para generar un informe en formato PDF.")
        self.pdf_folder_button = QPushButton("📁 Seleccionar carpeta destino")
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
        self.process_button = QPushButton("Procesar")
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
        self.html_folder_button = QPushButton("📁 Seleccionar carpeta destino")
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
        self.process_button = QPushButton("Procesar")
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
        self.progress.setStyleSheet("""
            QProgressBar {
                border: 2px solid #C0C0C0;
                border-radius: 5px;
                text-align: center;
                background-color: #f4faff;
                color: #333;
                height: 25px;
            }
            QProgressBar::chunk {
                background-color: #57A0D3;
                width: 20px;
                margin: 0px;
            }
            QProgressBar::chunk:indeterminate {
                background: qlineargradient(x1: 0, y1: 0.5, x2: 1, y2: 0.5,
                                            stop: 0 #57A0D3, stop: 1 #1034A6);
                border-radius: 5px;
            }
        """)

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
        # Aquí se llamaría a la lógica principal del procesamiento


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ACSAHEUserInterface()
    sys.exit(app.exec_())
