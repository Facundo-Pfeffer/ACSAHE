from PyQt5.QtWidgets import (QWidget, QLabel, QProgressBar,
    QPushButton, QCheckBox, QHBoxLayout, QSizePolicy)

from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import Qt, QSize

DEFAULT_SPACING = 8
DEFAULT_MARGINS = (0, 0, 0, 0)
DEFAULT_FONT = QFont("Lato", 10)


def load_stylesheet(path="build/gui/style/acsahe.qss") -> str:
    """
    Loads and returns the stylesheet content from a QSS file.

    Args:
        path (str): Path to the QSS file.

    Returns:
        str: Stylesheet as a string.
    """
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as file:
            return file.read()
    return ""


def create_help_icon(icon_path: str, tooltip_text: str, size: int = 15) -> QLabel:
    """
    Creates a QLabel styled as a help icon with a tooltip.
    """
    label = QLabel()
    label.setCursor(Qt.WhatsThisCursor)
    label.setFixedSize(size + 10, size + 10)
    label.setStyleSheet("padding: 0px; margin: 0px;")
    label.setToolTip(tooltip_text)

    if os.path.exists(icon_path):
        pixmap = QPixmap(icon_path).scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        label.setPixmap(pixmap)

    return label


def create_row(widgets: list, spacing: int = DEFAULT_SPACING, margins: tuple = DEFAULT_MARGINS,
               alignment=Qt.AlignLeft | Qt.AlignVCenter) -> QWidget:
    """
    Creates a horizontal QWidget from a list of widgets with default spacing/margins.
    """
    layout = QHBoxLayout()
    layout.setSpacing(spacing)
    layout.setContentsMargins(*margins)
    layout.setAlignment(alignment)
    for widget in widgets:
        layout.addWidget(widget)

    container = QWidget()
    container.setLayout(layout)
    return container


def create_checkbox_tooltip_button_row(checkbox: QCheckBox, tooltip_icon: QLabel, button: QPushButton,
                                       spacing: int = DEFAULT_SPACING) -> QWidget:
    """
    Combines a QCheckBox, tooltip icon, and button into a standard aligned row:
    [checkbox + icon]                         [button]
    """
    label_layout = QHBoxLayout()
    label_layout.setContentsMargins(0, 0, 0, 0)
    label_layout.setSpacing(4)
    label_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    label_layout.addWidget(checkbox)
    label_layout.addWidget(tooltip_icon)

    label_wrapper = QWidget()
    label_wrapper.setLayout(label_layout)

    button.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
    return create_row([label_wrapper, button], spacing=spacing, alignment=Qt.AlignJustify)


def create_button_icon_row(primary_button: QPushButton, icon_button: QPushButton,
                           spacing: int = DEFAULT_SPACING) -> QWidget:
    """
    Creates a row where a main button expands and a small icon button is to the right.
    """
    primary_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    icon_button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)

    return create_row([primary_button, icon_button], spacing=spacing)


def create_select_file_row(
    label_text: str,
    object_name: str,
    font: QFont = QFont("Lato", 10),
    include_reset: bool = False,
    reset_tooltip: str = "Restablecer selección",
    reset_icon_path: str = "build/gui/icons/restablish_icon_15px.png",
    on_main_click: callable = None,
    on_reset_click: callable = None,
    spacing: int = 8
):
    """
    Creates a row for a file/folder selector with an optional reset icon button.

    Returns:
        (QWidget, QPushButton, Optional[QPushButton])
    """
    main_button = QPushButton(label_text)
    main_button.setFont(font)
    main_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
    main_button.setObjectName(object_name)
    if on_main_click:
        main_button.clicked.connect(on_main_click)

    if include_reset:
        reset_button = QPushButton()
        reset_button.setCursor(Qt.PointingHandCursor)
        reset_button.setToolTip(reset_tooltip)
        reset_button.setFixedHeight(30)
        reset_button.setStyleSheet("""
            QPushButton {
                border: 1px solid #b0c4de;
                border-radius: 6px;
                padding: 3px;
                background-color: white;
            }
            QPushButton:hover {
                background-color: #e6f0ff;
            }
            QPushButton:pressed {
                background-color: #cce0ff;
            }
        """)
        if os.path.exists(reset_icon_path):
            reset_button.setIcon(QIcon(reset_icon_path))
            reset_button.setIconSize(QSize(15, 15))
        if on_reset_click:
            reset_button.clicked.connect(on_reset_click)
        return create_row([main_button, reset_button], spacing=spacing), main_button, reset_button

    return create_row([main_button], spacing=spacing), main_button, None

def create_checkbox_folder_row(
    checkbox_text: str,
    checkbox_object_name: str,
    tooltip_text: str,
    button_text: str,
    button_object_name: str,
    on_checkbox_toggle: callable = None,
    on_button_click: callable = None,
    font: QFont = QFont("Lato", 10),
    icon_path: str = "build/gui/icons/information_icon_15px_b.png",
    icon_size: int = 15,
    spacing: int = 8,
    button_alignment: Qt.Alignment = Qt.AlignRight,
    label_indent: int = 0,
    button_fixed_width: int = None
):
    """
    Creates a row with a checkbox, help icon, and a file/folder selector button.

    Returns:
        (QWidget, QCheckBox, QPushButton)
    """
    checkbox = QCheckBox(checkbox_text)
    checkbox.setFont(font)
    checkbox.setObjectName(checkbox_object_name)
    if on_checkbox_toggle:
        checkbox.stateChanged.connect(on_checkbox_toggle)

    tooltip_icon = create_help_icon(icon_path, tooltip_text, size=icon_size)

    label_layout = QHBoxLayout()
    label_layout.setContentsMargins(label_indent, 0, 0, 0)
    label_layout.setSpacing(4)
    label_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    label_layout.addWidget(checkbox)
    label_layout.addWidget(tooltip_icon)

    label_wrapper = QWidget()
    label_wrapper.setLayout(label_layout)

    button = QPushButton(button_text)
    button.setFont(font)
    button.setObjectName(button_object_name)
    button.setEnabled(False)
    if button_fixed_width:
        button.setFixedWidth(button_fixed_width)
    if on_button_click:
        button.clicked.connect(on_button_click)

    row_layout = QHBoxLayout()
    row_layout.setContentsMargins(0, 0, 0, 0)
    row_layout.setSpacing(spacing)
    row_layout.addWidget(label_wrapper)
    row_layout.addStretch()
    row_layout.addWidget(button, 0, button_alignment)

    row_widget = QWidget()
    row_widget.setLayout(row_layout)

    return row_widget, checkbox, button

def create_main_layout_with_logo_and_controls(logo_widget: QWidget, control_widgets: list[QWidget]) -> QHBoxLayout:
    main_layout = QHBoxLayout()
    main_layout.setSpacing(30)
    main_layout.setContentsMargins(40, 20, 40, 20)
    main_layout.setAlignment(Qt.AlignTop)

    main_layout.addWidget(logo_widget)

    control_layout = QVBoxLayout()
    control_layout.setAlignment(Qt.AlignTop)
    for widget in control_widgets:
        control_layout.addWidget(widget)

    main_layout.addLayout(control_layout)
    return main_layout


from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QFont
import os



def create_logo_section(
    logo_path: str,
    logo_size: int = 280,
    below_text_html: str = "",
    text_font: QFont = QFont("Lato", 9),
    text_color: str = "gray"
) -> QWidget:
    """
    Creates a QWidget with a centered logo and optional credits label.

    Args:
        logo_path (str): Path to the logo image.
        logo_size (int): Width and height for logo in pixels.
        below_text_html (str): HTML content for credits.
        text_font (QFont): Font used for credits text.
        text_color (str): Color of the credit text.

    Returns:
        QWidget: A widget containing the logo and optional credits.
    """
    outer_container = QWidget()
    outer_layout = QVBoxLayout()
    outer_layout.setContentsMargins(0, 0, 0, 0)
    outer_layout.setSpacing(0)
    outer_layout.setAlignment(Qt.AlignVCenter | Qt.AlignHCenter)

    # Logo
    logo_container = QWidget()
    logo_layout = QVBoxLayout()
    logo_layout.setContentsMargins(0, 0, 0, 0)
    logo_layout.setAlignment(Qt.AlignCenter)

    logo_label = QLabel()
    if os.path.exists(logo_path):
        pixmap = QPixmap(logo_path).scaled(logo_size, logo_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        logo_label.setPixmap(pixmap)
    logo_label.setAlignment(Qt.AlignCenter)
    logo_label.setFixedSize(logo_size, logo_size)
    logo_layout.addWidget(logo_label)
    logo_container.setLayout(logo_layout)
    outer_layout.addWidget(logo_container)

    # Text (optional)
    if below_text_html:
        credit_container = QWidget()
        credit_layout = QVBoxLayout()
        credit_layout.setContentsMargins(0, 0, 0, 0)
        credit_layout.setAlignment(Qt.AlignBottom | Qt.AlignHCenter)

        credit_label = QLabel(below_text_html)
        credit_label.setTextFormat(Qt.RichText)
        credit_label.setOpenExternalLinks(True)
        credit_label.setAlignment(Qt.AlignCenter)
        credit_label.setFont(text_font)
        credit_label.setStyleSheet(f"color: {text_color}; font-size: {text_font.pointSize()}px; margin-top: 6px; line-height: 1.1em;")
        credit_layout.addWidget(credit_label)
        credit_container.setLayout(credit_layout)
        outer_layout.addWidget(credit_container)

    outer_container.setLayout(outer_layout)
    return outer_container


def create_primary_action_button(
    text: str,
    on_click: callable,
    font: QFont = QFont("Lato", 11, QFont.Bold),
    height: int = 40,
    object_name: str = "main_button"
):
    btn = QPushButton(text)
    btn.setFont(font)
    btn.setFixedHeight(height)
    btn.clicked.connect(on_click)
    btn.setObjectName(object_name)
    return btn


def create_status_label(
    font: QFont = QFont("Lato", 10),
    visible: bool = False,
    object_name: str = "status_label"
):
    lbl = QLabel("")
    lbl.setFont(font)
    lbl.setAlignment(Qt.AlignCenter)
    lbl.setVisible(visible)
    lbl.setObjectName(object_name)
    return lbl


def create_styled_progress_bar(
    font: QFont = QFont("Lato", 10),
    visible: bool = False,
    style_path: str = None,
    object_name: str = "progress_bar"
):
    bar = QProgressBar()
    bar.setFont(font)
    bar.setVisible(visible)
    bar.setObjectName(object_name)
    if style_path and os.path.exists(style_path):
        with open(style_path, "r", encoding="utf-8") as f:
            bar.setStyleSheet(f.read())
    return bar


def create_text_row(
    text_html: str,
    on_click: callable = None,
    font: QFont = QFont("Lato", 9),
    alignment: Qt.Alignment = Qt.AlignCenter,
    margins: tuple = (0, 2, 0, 2),
    style_plain: str = "color: #2c3e50;",
    style_link: str = "color: #1a73e8; text-decoration: underline;",
    style_code: str = "font-family: monospace; background-color: #f4f4f4; border-radius: 3px; padding: 1px 4px;"
) -> QWidget:
    """
    Creates a text row with styled spans for plain text, links, and `inline code`.

    Supports:
    - <a href="#">...</a> for links
    - `code` for inline code blocks
    """
    import re

    def wrap_plain_code_and_links(text: str) -> str:
        # Handle inline code with backticks first
        code_wrapped = re.sub(r'`([^`]+)`', lambda m: f'<code style="{style_code}">{m.group(1)}</code>', text)

        # Then split by <a> tags and wrap remaining text in styled <span>
        parts = re.split(r'(<a\s+href=.*?>.*?</a>)', code_wrapped)
        styled = []
        for part in parts:
            if part.startswith('<a'):
                if 'style=' not in part:
                    part = part.replace('<a ', f'<a style="{style_link}" ')
                styled.append(part)
            elif part.strip():
                styled.append(f'<span style="{style_plain}">{part}</span>')
        return ''.join(styled)

    styled_text = wrap_plain_code_and_links(text_html)

    label = QLabel()
    label.setFont(font)
    label.setAlignment(alignment)
    label.setTextFormat(Qt.RichText)
    label.setTextInteractionFlags(Qt.TextBrowserInteraction)
    label.setOpenExternalLinks(False)
    label.setText(styled_text)

    if on_click:
        label.linkActivated.connect(lambda _: on_click())

    layout = QHBoxLayout()
    layout.setContentsMargins(*margins)
    layout.setAlignment(alignment)
    layout.addWidget(label)

    wrapper = QWidget()
    wrapper.setLayout(layout)
    return wrapper

