import tempfile
import time
import webbrowser
import base64

import numpy as np
import math

from tkinter import messagebox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QFont, QPixmap
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QProgressBar, QDesktopWidget

import plotly.graph_objects as go

from diagrama_de_interaccion.diagramas_de_interaccion import DiagramaInteraccion2D
from geometria.resolvedor_geometria import ResolucionGeometrica


def show_message(message, titulo="Mensaje"):
    messagebox.showinfo(titulo, message)


class ACSAHE(QWidget):
    progress_bar_messages = {
        "Inicio": "Geometría completada."
                  " Construyendo diagrama de interacción para plano de carga λ={plano_de_carga}° ...",
        "Medio": "Construyendo diagrama de interacción para plano de carga λ={plano_de_carga}° ...",
        "Ultimo": "Construyendo resultados ..."}

    def __init__(self, app_gui, nombre_del_archivo, path_archivo):
        super().__init__()
        self.file_name = nombre_del_archivo
        self.data_subsets = {}
        self.solucion_geometrica = None
        self.path_to_file = path_archivo
        self.app = app_gui
        self.ejecutar_acsahe()
        self.close()

    def ejecutar_acsahe(self):
        self.setWindowTitle("ACSAHE")
        logo_path = f"{self.path_to_file + '/' if self.path_to_file else ''}build\\images\\LOGO ACSAHE.webp"
        icon_path = f"{self.path_to_file + '/' if self.path_to_file else ''}build\\images\\Logo H.webp"
        self.icon_path_ico = f"{self.path_to_file + '/' if self.path_to_file else ''}build\\images\\Logo_H.ico"

        self.resize(650, 200)  # Tamaño de la pestaña
        self.center()  # La centramos
        self.layout = QVBoxLayout()

        font = QFont()
        font.setPointSize(10)
        # font.setItalic(True)
        font.setFamily("Lato")

        self.message_label = QLabel("Construyendo Geometría...", self)
        self.message_label.setFont(font)
        self.message_label.setAlignment(Qt.AlignCenter)

        self.logoLabel = QLabel(self)
        pixmap = QPixmap(logo_path)
        resizedPixmap = pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.logoLabel.setPixmap(resizedPixmap)
        self.logoLabel.setAlignment(Qt.AlignCenter)  # Centramos

        # Añadimos la imagen en la ventana, y el ícono al lado del nombre
        self.setWindowIcon(QIcon(icon_path))
        self.layout.addWidget(self.logoLabel)

        # El mensaje
        self.message_label.setFont(font)
        self.message_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.message_label)

        # Seteando la barra de progreso
        self.progress = QProgressBar(self)
        self.progress.setFont(font)
        self.layout.addWidget(self.progress)
        self.estilo_barra_progreso()

        #  Poniendo fondo blanco
        self.setStyleSheet("QWidget { background-color: #f4faff; }")
        self.setLayout(self.layout)

        self.show()
        self.update_progress_bar(int(0))
        try:
            self.start_process()
        except Exception as e:
            show_message(e)
            raise e

    def center(self):
        qr = self.frameGeometry()  # Get the window rectangle
        cp = QDesktopWidget().availableGeometry().center()  # Get the screen center point
        qr.moveCenter(cp)  # Set the window rectangle center to the screen center
        self.move(qr.topLeft())  # Move the window's top-left point

    def update_progress_bar(self, value):
        self.progress.setValue(value)

    def update_message(self, message):
        self.message_label.setText(message)

    def estilo_barra_progreso(self):
        self.progress.setStyleSheet("""

            QProgressBar {
                border: 2px solid #C0C0C0;
                border-radius: 5px;
                text-align: center; /* Ensure text is centered */
                background-color: #f4faff;
                color: #333; /* Color for the text */
            }

            QProgressBar::chunk {
                background-color: #57A0D3; /* Lighter blue color */
                width: 20px; /* Adjust width for better visibility of the dynamic effect */
                margin: 0px; /* Remove margin if you want chunks to be contiguous */
            }

            QProgressBar::chunk:indeterminate {
                background: qlineargradient(x1: 0, y1: 0.5, x2: 1, y2: 0.5, stop: 0 #57A0D3, stop: 1 #1034A6); /* Gradient from lighter blue to darker blue */
                border-radius: 5px;
            }
        """)

    def start_process(self):
        # First step

        solucion_geometrica = ResolucionGeometrica(
            file_path=f"{self.path_to_file + '/' if self.path_to_file else ''}{self.file_name}")

        lista_ang = solucion_geometrica.lista_ang_plano_de_carga
        lista_ang.sort()

        try:
            self.steps = 2 + len(lista_ang)
            time.sleep(1)
            self.update_message(self.progress_bar_messages["Inicio"].format(
                plano_de_carga=lista_ang[0]))
            self.update_progress_bar(int(10))
            # self.step_length = 100 / self.steps

            data_subsets = {}
            lista_x_total, lista_y_total, lista_z_total, lista_color, lista_text_total, lista_color_total = [], [], [], [], [], []
            lista_x_total_sin_phi, lista_y_total_sin_phi, lista_z_total_sin_phi = [], [], []

            for step in range(2, self.steps + 1):
                if step < 2 + len(lista_ang):
                    angulo_plano_de_carga = lista_ang[step - 2]
                    self.update_message(
                        self.progress_bar_messages["Medio"].format(plano_de_carga=angulo_plano_de_carga))
                    QApplication.processEvents()

                    solucion_parcial = DiagramaInteraccion2D(
                        angulo_plano_de_carga if angulo_plano_de_carga != -1 else 0.00,
                        solucion_geometrica)

                    coordenadas, lista_color_parcial, plano_de_def = solucion_geometrica.coordenadas_de_puntos_en_3d(
                        solucion_parcial.lista_resultados)

                    lista_x_parcial, lista_y_parcial, lista_z_parcial, lista_phi_parcial = coordenadas
                    es_phi_constante = isinstance(solucion_geometrica.problema["phi_variable"], float)
                    if solucion_geometrica.problema["tipo"] == "3D":
                        texto = self.hover_text_3d(lista_x_parcial, lista_y_parcial, lista_z_parcial, lista_phi_parcial,
                                                   angulo_plano_de_carga,
                                                   es_phi_constante)
                    else:
                        texto = self.hover_text_2d(lista_x_parcial, lista_y_parcial, lista_z_parcial, lista_phi_parcial,
                                                   angulo_plano_de_carga, es_phi_constante)
                    data_subsets[str(angulo_plano_de_carga)] = {
                        "x": lista_x_parcial.copy(),
                        "y": lista_y_parcial.copy(),
                        "z": lista_z_parcial.copy(),
                        "phi": lista_phi_parcial.copy(),
                        "text": texto.copy(),
                        "color": lista_color_parcial.copy()
                    }
                    lista_x_total.extend(lista_x_parcial)
                    lista_y_total.extend(lista_y_parcial)
                    lista_z_total.extend(lista_z_parcial)
                    lista_x_total_sin_phi.extend((np.array(lista_x_parcial) / np.array(lista_phi_parcial)).tolist())
                    lista_y_total_sin_phi.extend((np.array(lista_y_parcial) / np.array(lista_phi_parcial)).tolist())
                    lista_z_total_sin_phi.extend((np.array(lista_z_parcial) / np.array(lista_phi_parcial)).tolist())
                    lista_text_total.extend(texto)
                    lista_color_total.extend(lista_color_parcial)
                    self.update_progress_bar(int(step / self.steps * 100))
                else:
                    self.update_progress_bar(int(step / self.steps * 100))
                    self.update_message(self.progress_bar_messages["Ultimo"])
                    self.construir_resultado_html(solucion_geometrica, lista_x_total, lista_y_total, lista_z_total,
                                                  lista_text_total, lista_color_total, data_subsets)
        except Exception as e:
            print(e)
        finally:
            mensaje_extra = self.obtener_mensaje_hoja_de_resultados(solucion_geometrica)
            self.update_message(f"ACSAHE ha finalizado!{mensaje_extra}")
            QApplication.processEvents()
            solucion_geometrica.cerrar_hojas_de_calculo()
            time.sleep(1 if mensaje_extra else 0)
            # Ensure the window is visible, at the front, and active
            self.showNormal()  # Restores the window if minimized
            self.raise_()  # Brings the window to the front
            self.activateWindow()  # Makes the window the active window
            time.sleep(1 if not mensaje_extra else 5)

    def construir_resultado_html(self, solucion_geometrica, lista_x_total, lista_y_total, lista_z_total,
                                 lista_text_total, lista_color_total, data_subsets):

        fig_seccion = solucion_geometrica.construir_grafica_seccion_plotly()

        if solucion_geometrica.problema["tipo"] == "2D":
            fig = self.print_2d(solucion_geometrica, lista_x_total, lista_y_total, lista_z_total, lista_text_total,
                                lista_color_total, data_subsets)
            if solucion_geometrica.problema["resultados_en_wb"] is True:
                solucion_geometrica.insertar_valores_2D(data_subsets,
                                                        solucion_geometrica.problema["puntos_a_verificar"])
        else:
            fig = self.print_3d(solucion_geometrica, lista_x_total, lista_y_total, lista_z_total, lista_text_total,
                                lista_color_total, data_subsets)
            if solucion_geometrica.problema["resultados_en_wb"] is True:
                solucion_geometrica.insertar_valores_3D(data_subsets)

        pre_path = self.path_to_file + '/' if self.path_to_file else ''
        with open(f"{pre_path}build\\ext_utils/html/result_format.html", "r", encoding="UTF-8") as r, \
                open(f"{pre_path}build\\ext_utils/html/assets/css/main.css") as main_css, \
                open(f"{pre_path}build\\ext_utils/html/assets/css/noscript.css") as noscript_css, \
                open(f"{pre_path}build\\ext_utils/html/assets/js/ctrl_p.js") as ctrl_p_js, \
                open(self.icon_path_ico, 'rb') as icon_file:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.html') as tmp_result_file:
                acsahe = r.read()

                graph_html = fig.to_html(
                    full_html=False,
                    config=self.configuracion_descarga_imagen(
                        file_name=f"ACSAHE - Resultado {solucion_geometrica.problema['tipo']}"))

                logo_path = f"{self.path_to_file + '/' if self.path_to_file else ''}build\\images\\LOGO%20ACSAHE.webp"
                encoded_icon_string = base64.b64encode(icon_file.read()).decode('utf-8')
                tmp_result_file.write(acsahe.format(
                    icon_encoded=encoded_icon_string,
                    archivo=f"Archivo: {self.file_name}",
                    main_css=main_css.read(),
                    noscript_css=noscript_css.read(),
                    ctrl_p_js=ctrl_p_js.read(),
                    html_seccion=fig_seccion.to_html(
                        full_html=False,
                        config=self.configuracion_descarga_imagen(
                            file_name=f"ACSAHE - Sección")),
                    tabla_propiedades=self.propiedades_html(solucion_geometrica),
                    tabla_caracteristicas_materiales=self.caracteristicas_materiales_html(solucion_geometrica),
                    html_resultado=graph_html,
                    foto_logo=logo_path).encode("utf-8"))
                tmp_file_path = tmp_result_file.name

        fig.update_layout(autosize=True)
        # fig.show()
        webbrowser.open('file://' + tmp_file_path)

    def configuracion_descarga_imagen(self, file_name="ACSAHE"):
        return {
            'toImageButtonOptions': {
                'format': 'png',
                'filename': file_name,
                'height': 800,
                'width': 1000,
                'scale': 9  # 1 por defecto, más implica mayor resolución
            }
        }

    @staticmethod
    def obtener_mensaje_hoja_de_resultados(solucion_geometrica):
        if solucion_geometrica.problema["tipo"] == "3D" and solucion_geometrica.problema["resultados_en_wb"] is True:
            return "\n\nSe ha habilitado la hoja 'Resultados 3D' en la planilla.\n"
        elif solucion_geometrica.problema["tipo"] == "2D" and solucion_geometrica.problema["resultados_en_wb"] is True:
            return "\n\nSe ha habilitado la hoja 'Resultados 2D' en la planilla.\n"
        return ""

    @staticmethod
    def caracteristicas_materiales_html(geometria: ResolucionGeometrica):
        return f"""<h3><a href="#">CARACTERÍSTICAS DE LOS MATERIALES</a></h3>
                            <div class="table-wrapper">
                                <table class="alt">
                                    <colgroup>
                                        <col style="width: 10%;"> <!-- First column width -->
                                        <col style="width: 70%;"> <!-- Middle column width -->
                                        <col style="width: 20%;"> <!-- Third column width -->
                                    </colgroup>
                                    <thead>
                                        <tr>
                                            <th>Material</th>
                                            <th>Descripción</th>
                                            <th>Valor</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <tr>
                                            <td>Hormigón</td>
                                            <td>Calidad del hormigón.<br>El número indica la resistencia característica a la compresión expresada en MPa.</td>
                                            <td>{'H' + str(int(geometria.hormigon.fc))}</td>
                                        </tr>
                                        <tr>
                                            <td>Acero Pasivo</td>
                                            <td>Tipo de acero seleccionado para armadura pasiva.</td>
                                            <td>{geometria.acero_pasivo}</td>
                                        </tr>
                                        {'''<tr>
                                        <td>Acero Activo</td>
                                        <td>Tipo de acero seleccionado para armadura activa.<br>Deformación efectiva del acero de pretensado (producidas las pérdidas).</td>''' +
                                         '<td>' + f'{geometria.acero_activo}' + '<br>' + f'{geometria.def_de_pretensado_inicial * 1000}‰' + '</td></tr>' if geometria.EAP else ''}
                                        <tr>
                                            <td>Armaduras Transversales</td>
                                            <td>Tipo de armadura transversal seleccionada.</td>
                                            <td>{geometria.tipo_estribo}</td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>"""

    @staticmethod
    def propiedades_html(geometria: ResolucionGeometrica):
        return f"""<h3><a href="#"><br>PROPIEDADES DE LA SECCIÓN</a></h3>
                            <div class="table-wrapper">
                                <table class="alt">
                                    <colgroup>
                                        <col style="width: 10%;"> <!-- First column width -->
                                        <col style="width: 70%;"> <!-- Middle column width -->
                                        <col style="width: 20%;"> <!-- Third column width -->
                                    </colgroup>
                                    <thead>
                                        <tr>
                                            <th>Propiedad</th>
                                            <th>Descripción</th>
                                            <th>Valor</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <tr>
                                            <td>Área</td>
                                            <td>Área de la sección bruta de Hormigón.</td>
                                            <td>{round(geometria.seccion_H.area, 2)} cm²</td>
                                        </tr>
                                        <tr>
                                            <td>Ix</td>
                                            <td>Inercia con respecto al eje x.</td>
                                            <td>{geometria.seccion_H.Ix} cm⁴</td>
                                        </tr>
                                        <tr>
                                            <td>Iy</td>
                                            <td>Inercia con respecto al eje y.</td>
                                            <td>{geometria.seccion_H.Iy} cm⁴</td>
                                        </tr>
                                        <tr>
                                            <td>ρ</td>
                                            <td>Cuantía geométrica de refuerzo pasivo.</td>
                                            <td>{geometria.EA.cuantia_geometrica(geometria.seccion_H.area, output_str=True)}</td>
                                        </tr>
                                                                                {'''<tr>
            <td>ρp</td>
            <td>Cuantía geométrica de refuerzo activo.</td>''' +
                                                                                 '<td>' + f'{geometria.EAP.cuantia_geometrica(geometria.seccion_H.area, output_str=True)}' + '</td></tr>' if geometria.EAP else ''}
                                        <tr>
                                            <td>Discretización</td>
                                            <td>Tipo de discretización elegida: {geometria.nivel_disc}.</td>
                                            <td>{'ΔX=' + str(round(geometria.seccion_H.dx, 2)) + ' cm' if geometria.seccion_H.dx else ''}{'<br>ΔY=' + str(round(geometria.seccion_H.dy, 2)) + ' cm' if geometria.seccion_H.dy else ''}{'<br>' if geometria.seccion_H.dx else ''}
{'Δθ=' + str(round(geometria.seccion_H.d_ang, 2)) + ' °' if geometria.seccion_H.d_ang else ''}
{'<br>Δr:' + str(round(geometria.seccion_H.dr, 2)) + ' particiones<br>(variación logarítmica)' if geometria.seccion_H.dr else ''}</td>
                                        </tr>
                                        {'''<tr>
            <td>Pretensado</td>
            <td>Deformación elástica inicial causada por la fuerza de pretensado, referida al baricentro.</td>''' +
                                         '<td>' + f'{geometria.mostrar_informacion_pretensado()}' + '</td></tr>' if geometria.EAP else ''}
                                    </tbody>
                                </table>
                            </div>"""

    def agregar_punto_estado(self, fig, X, Y, Z, NOMBRE, **kwargs):
        fig.add_trace(go.Scatter3d(
            x=X,
            y=Y,
            z=Z,
            mode='markers',
            marker=dict(
                size=4,
                color="black",
                symbol='diamond-open',
            ),
            text=self.hover_text_estados(X, Y, Z, NOMBRE),
            hoverinfo='text',
            name='Estados de carga',
            visible=True,
            **kwargs
        ))

    def print_3d(self, solucion_geometrica, lista_x_total, lista_y_total, lista_z_total, lista_text_total,
                 lista_color_total, data_subsets):
        plano_de_carga_lista = set(x["plano_de_carga"] for x in solucion_geometrica.problema["puntos_a_verificar"])
        plano_de_carga_lista = list(plano_de_carga_lista)
        plano_de_carga_lista.sort()
        estados_subsets = {}
        for punto_a_verificar in solucion_geometrica.problema["puntos_a_verificar"]:
            plano_de_carga = str(round(float(punto_a_verificar["plano_de_carga"]), 2))
            if plano_de_carga not in estados_subsets:  # Inicialización
                estados_subsets[plano_de_carga] = {"x": [], "y": [], "z": [], "nombre": []}
            estados_subsets[plano_de_carga]["x"].append(punto_a_verificar["Mx"])
            estados_subsets[plano_de_carga]["y"].append(punto_a_verificar["My"])
            estados_subsets[plano_de_carga]["z"].append(punto_a_verificar["P"])
            estados_subsets[plano_de_carga]["nombre"].append(punto_a_verificar["nombre"])

        X = [x["Mx"] for x in solucion_geometrica.problema["puntos_a_verificar"]]
        Y = [x["My"] for x in solucion_geometrica.problema["puntos_a_verificar"]]
        Z = [x["P"] for x in
             solucion_geometrica.problema["puntos_a_verificar"]]  # Positivo para transformar a compresión positiva
        NOMBRE = [x["nombre"] for x in solucion_geometrica.problema["puntos_a_verificar"]]

        plano_de_carga_lista = [x["plano_de_carga"] for x in solucion_geometrica.problema["puntos_a_verificar"]]
        plano_de_carga_lista.sort()

        fig = go.Figure(layout_template="plotly_white")
        fig.add_trace(go.Scatter3d(
            x=lista_x_total,
            y=lista_y_total,
            z=lista_z_total,
            mode='markers',
            marker=dict(size=2, color=lista_color_total),
            text=lista_text_total,
            hoverinfo='text',
            name='Contorno diagrama de interacción',
            visible=True,
        ))

        lista_botones = self.agregar_diferentes_botones(fig, data_subsets, estados_subsets)

        rango_min = min(min(lista_x_total + X), min(lista_y_total + Y))
        rango_max = max(max(lista_x_total + X), max(lista_y_total + Y))

        self.agregar_punto_estado(fig, X, Y, Z, NOMBRE)

        fig.update_layout(
            title=dict(
                text=f'<span style="font-size: 30px;">ACSAHE</span><br><span style="font-size: 20px;">Diagrama de interacción 3D</span></span>',
                x=0.5,
                font=dict(color="rgb(142, 180, 227)",
                          family='Times New Roman')),
            scene=dict(
                xaxis_title='ϕMnx [kNm]',
                yaxis_title='ϕMny [kNm]',
                zaxis_title='ϕPn [kN]',
                xaxis=dict(
                    linecolor="Grey",
                    showline=True,
                    title_font=dict(family='Times New Roman', size=16),
                    range=[rango_min, rango_max]
                ),
                yaxis=dict(
                    linecolor="Grey",
                    showline=True,
                    title_font=dict(family='Times New Roman', size=16),
                    range=[rango_min, rango_max]
                ),
                zaxis=dict(
                    linecolor="Grey",
                    showline=True,
                    title_font=dict(family='Times New Roman', size=16),
                    range=[min(lista_z_total + Z), max(lista_z_total + Z)]),
                aspectmode='manual',  # Set aspect ratio manually
                aspectratio=dict(x=1, y=1, z=1),
            ))

        fig.update_layout(
            updatemenus=[dict(
                type="buttons",
                font={"color": "black", "size": 12},
                direction="down",
                showactive=True,
                buttons=lista_botones,
            )])

        return fig

    def print_2d(self, solucion_geometrica, lista_x_total, lista_y_total, lista_z_total, lista_text_total,
                 lista_color_total,
                 data_subsets):
        fig = go.Figure(
            layout_template="plotly_white"
        )
        lista_x_total = [(1 if x > 0 else -1 if x != 0 else 1 if y >= 0 else -1) * math.sqrt(x ** 2 + y ** 2) for x, y
                         in
                         zip(lista_x_total, lista_y_total)]

        X = [x["M"] for x in solucion_geometrica.problema["puntos_a_verificar"]]
        Y = [x["P"] for x in
             solucion_geometrica.problema["puntos_a_verificar"]]  # Menos para transformar a compresión positivo.
        nombre = [x["nombre"] for x in solucion_geometrica.problema["puntos_a_verificar"]]
        text_estados_2d = self.hover_text_estados_2d(X, Y, nombre)

        fig.add_trace(go.Scatter(
            x=lista_x_total,
            y=lista_z_total,
            mode='markers',
            marker=dict(size=2, color=lista_color_total),
            text=lista_text_total,
            hoverinfo='text',
            name='Contorno diagrama de interacción',
            visible=True,
        ))

        fig.add_trace(go.Scatter(
            x=X,
            y=Y,
            mode='markers',
            marker=dict(size=10,
                        color='#1f77b4',
                        symbol='diamond-open'),
            text=text_estados_2d,
            hoverinfo='text',
            name='Estados a verificar',
            visible=True,
        ))

        rango_min_x = min(lista_x_total + X) * 1.2
        rango_max_x = max(lista_x_total + X) * 1.2
        rango_min_y = min(lista_z_total + Y) * 1.1
        rango_max_y = max(lista_z_total + Y) * 1.2

        # Custom axis lines
        fig.add_shape(type="line", x0=rango_min_x, y0=0, x1=rango_max_x, y1=0, line=dict(color="grey", width=1))
        fig.add_shape(type="line", x0=0, y0=rango_min_y, x1=0, y1=rango_max_y, line=dict(color="grey", width=1))

        fig.update_xaxes(title_text="ϕMnλ [kNm]",
                         title_font=dict(
                             family="Times New Roman",
                             size=16))
        fig.update_yaxes(title_text="ϕPn [kN]",
                         title_font=dict(
                             family="Times New Roman",
                             size=16))

        fig.update_layout(
            title=dict(
                text=f'<span style="font-size: 30px;">ACSAHE</span><br><span style="font-size: 20px;">Diagrama de interacción para λ={list(data_subsets.keys())[0]} °</span><br>',
                # text=f"<b>ACSAHEArchivo: {self.file_name}</b>",
                x=0.5,
                font=dict(
                    color="rgb(142, 180, 227)",
                    family='Times New Roman')),
            xaxis=dict(showticklabels=True,
                       showgrid=True,
                       zeroline=True),
            yaxis=dict(showticklabels=True, showgrid=True, zeroline=True),
            showlegend=False,
        )

        fig.update_layout({
            'plot_bgcolor': 'rgba(0,0,0,0)',  # This sets the plot background to transparent
            'paper_bgcolor': 'rgba(0,0,0,0)',  # This sets the paper (overall figure) background to transparent
        })

        return fig

    def agregar_diferentes_botones(self, fig, data_subsets, estados_subsets):
        traces = [(1, "Mostrar todos")]
        # Add each subset as a separate trace, initially invisible
        for angulo, subset in sorted(data_subsets.items(), key=lambda item: float(item[0])):
            traces.append((1, f"λ={angulo}º"))
            fig.add_trace(go.Scatter3d(
                x=subset['x'],
                y=subset['y'],
                z=subset['z'],
                mode='markers',
                marker=dict(size=2, color=subset['color']),
                text=subset['text'],
                hoverinfo='text',
                name=f"λ={angulo}º",
                showlegend=False,
            visible=False  # Initially invisible
            ))
            if angulo in estados_subsets.keys():
                fig.add_trace(go.Scatter3d(
                    x=estados_subsets[angulo]['x'],
                    y=estados_subsets[angulo]['y'],
                    z=estados_subsets[angulo]['z'],
                    mode='markers',
                    marker=dict(size=4,
                                color='black',
                                symbol='diamond-open'),
                    text=self.hover_text_estados(estados_subsets[angulo]['x'],
                                                 estados_subsets[angulo]['y'],
                                                 estados_subsets[angulo]['z'],
                                                 estados_subsets[angulo]['nombre']),
                    hoverinfo='text',
                    name=f"λ={angulo}º",
                    visible=False,
                    showlegend=False
                ))
                traces.append(2)

        buttons = []
        for i, value in enumerate(traces):
            if value == 2:
                continue
            visible_state = [False] * len(traces)
            visible_state[i] = True
            if i < len(traces) - 1 and isinstance(traces[i + 1], int) and traces[i + 1] == 2:
                visible_state[i + 1] = True

            buttons.append(dict(
                label=value[1],
                method="update",
                args=[{"visible": visible_state}]
            ))
        return buttons

    @staticmethod
    def hover_text_2d(lista_x, lista_y, lista_z, lista_phi, plano_de_carga, es_phi_constante):
        M_lista = [(1 if x > 0 else -1 if x != 0 else 1 if y >= 0 else -1) * math.sqrt(x ** 2 + y ** 2) for x, y in
                   zip(lista_x, lista_y)]
        return [
            f"ϕPn: {round(z, 2)} kN<br>ϕMnλ: {round(M, 2)} kNm<br>ϕMnx: {round(x, 2)} kNm<br>ϕMny: {round(y, 2)} kNm<br>ϕ: {round(phi, 2)}{' (constante)' if es_phi_constante else ''}<br>λ={plano_de_carga}°"
            for x, y, z, phi, M in zip(lista_x, lista_y, lista_z, lista_phi, M_lista)]

    @staticmethod
    def hover_text_3d(lista_x, lista_y, lista_z, lista_phi, plano_de_carga, es_phi_constante):
        return [
            f"ϕPn: {round(z, 2)} kN<br>ϕMnx: {round(x, 2)} kNm<br>ϕMny: {round(y, 2)} kNm<br>ϕ: {round(phi, 2)}{' (constante)' if es_phi_constante else ''}<br>λ={plano_de_carga}°"
            for x, y, z, phi in zip(lista_x, lista_y, lista_z, lista_phi)]

    @staticmethod
    def hover_text_estados(lista_x, lista_y, lista_z, lista_estado):
        return [
            f"<b>Estado: {estado}</b><br>Pu: {round(z, 2)} kN<br>Mxu: {round(x, 2)} kNm<br>Myu: {round(y, 2)} kNm"
            for x, y, z, estado in zip(lista_x, lista_y, lista_z, lista_estado)]

    @staticmethod
    def hover_text_estados_2d(lista_x, lista_y, lista_estado):
        return [
            f"<b>Estado: {estado}</b><br>Pu: {round(y, 2)} kN<br>Mu: {round(x, 2)} kNm"
            for x, y, estado in zip(lista_x, lista_y, lista_estado)]
