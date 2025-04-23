import plotly.graph_objects as go
import numpy as np
import base64
import math
import tempfile
import webbrowser
from pathlib import Path
from typing import Any, Dict, Tuple

from plot.html.html_engine import ACSAHEHtmlEngine


class ACSAHEPlotlyEngine(object):
    def __init__(self, fig=None, indice_color=0):
        self.fig = self.obtener_fig(fig)
        self.indice_color = indice_color
        self.strings_y_color = {}
        self.section_fig = None

    @staticmethod
    def obtener_fig(fig):
        if fig is not None:
            return fig
        fig = go.Figure(layout_template="plotly_white")
        fig.update_yaxes(
            scaleanchor="x",
            scaleratio=1,
        )
        return fig

    def plot_positive_polygon(self, elemento, color, espesor, transparencia, negative_shapes_list=None):
        negative_shapes_list = [] if negative_shapes_list is None else negative_shapes_list
        negative_polygons_list = [shape for shape in negative_shapes_list if shape.tipo != "Circular"]
        x_border_segment_list = []
        y_border_segment_list = []
        for unsplit_segment in elemento.segmentos_borde:
            split_segment_list = self._split_segment_in_negative_polygons(unsplit_segment, negative_polygons_list)
            for segment in split_segment_list:
                x_border_segment_list.append([segment.start_node.x, segment.end_node.x])
                y_border_segment_list.append([segment.start_node.y, segment.end_node.y])
        for index, x_to_plot in enumerate(x_border_segment_list):
            self.fig.add_trace(go.Scatter(
                x=x_border_segment_list[index], y=y_border_segment_list[index],
                showlegend=False,
                opacity=transparencia,
                line=dict(width=espesor),
                hoverinfo='skip',
                marker=dict(
                    size=0.1,
                    color=color,
                )))

    def plot_negative_polygon(self, elemento, color, espesor, transparencia, positive_polygons_list, negative_polygons_list):

        uncleaned_segment_list = []

        other_negative_polygons = negative_polygons_list.copy()
        other_negative_polygons.remove(elemento)

        for segment in elemento.segmentos_borde:
            if self._is_segment_in_positive_polygons(segment, positive_polygons_list):
                uncleaned_segment_list.append(segment)  # Before cleaning

        #  Cleaning shared borders among negative polygons
        cleaned_segment_list = uncleaned_segment_list.copy()
        for other_polygon in other_negative_polygons:
            for segment in uncleaned_segment_list:
                if segment in cleaned_segment_list and other_polygon.is_segment_a_border_segment(segment):
                    cleaned_segment_list.remove(segment)

        x_borde = []
        y_borde = []
        for cleaned_segment in cleaned_segment_list:
            x_borde.append([cleaned_segment.start_node.x, cleaned_segment.end_node.x])
            y_borde.append([cleaned_segment.start_node.y, cleaned_segment.end_node.y])

        for index, x_to_plot in enumerate(x_borde):
            self.fig.add_trace(go.Scatter(
                x=x_borde[index], y=y_borde[index],
                showlegend=False,
                opacity=transparencia,
                line=dict(width=espesor),
                hoverinfo='skip',
                marker=dict(
                    size=0.1,
                    color=color,
                )))

    def _split_segment_in_negative_polygons(self, segment_to_split, negative_polygons_list):
        segment_split_list = []
        if not negative_polygons_list:
            return [segment_to_split]
        for negative_polygon in negative_polygons_list:
            for negative_segment in negative_polygon.segmentos_borde:
                if len(segment_split_list) == 0:
                    segment_split_list = [segment_to_split]
                segment_split_list_temp = segment_split_list.copy()  # Shallow copy, same objects.
                for positive_segment in segment_split_list_temp:
                    if positive_segment.segment_line & negative_segment.segment_line is None:  # Segments are parallel.
                        substract_result = positive_segment - negative_segment
                        if substract_result is None:  # The entire positive element is inside a negative segment.
                            segment_split_list.remove(positive_segment)
                            continue
                        if isinstance(substract_result, list):
                            segment_split_list.remove(positive_segment)
                            segment_split_list.extend(substract_result)
        return segment_split_list

    def _is_segment_in_positive_polygons(self, segment, positive_polygons_list) -> bool:
        for positive_polygon in positive_polygons_list:
            if any(positive_polygon.determinar_si_nodo_pertence_a_contorno_sin_bordes(node) for node in[segment.start_node, segment.end_node]):
                return True
        return False

    def plot_cross_section(self, seccion, lista_de_angulos_plano_de_carga):
        color = "Grey"
        for contorno in seccion.contornos_positivos:
            if contorno.tipo == "Poligonal":
                self.plot_positive_polygon(contorno, color=color, transparencia=1, espesor=3, negative_shapes_list=seccion.contornos_negativos)
            else:
                self.plot_annular_sector(contorno,
                                         arc_division=150,
                                         color=color, transparency=1, thickness=4)

        for contorno in seccion.contornos_negativos:
            if contorno.tipo == "Poligonal":
                self.plot_negative_polygon(
                    contorno, color=color, transparencia=1, espesor=4,
                    positive_polygons_list=seccion.contornos_positivos,
                    negative_polygons_list=seccion.contornos_negativos)
            else:
                self.plot_annular_sector(contorno,
                                         arc_division=150,
                                         color=color, transparency=1, thickness=4)

        x_centroide = []
        y_centroide = []
        for elemento in seccion.elementos:
            if elemento.tipo == "Poligonal":
                self.plot_positive_polygon(elemento, color=color, transparencia=0.2, espesor=1)
            else:
                self.plot_annular_sector(elemento,
                                         arc_division=100,
                                         color=color,
                                         transparency=0.2,
                                         thickness=1)

            x_centroide.append(elemento.xg)
            y_centroide.append(elemento.yg)

        self.fig.add_trace(
            go.Scatter(
                dict(x=x_centroide, y=y_centroide, mode="markers", marker=dict(color=color, size=2),
                     hoverinfo='skip',
                     showlegend=False,
                     )))

        self.plot_axes_and_equivalent_force_line(seccion, lista_de_angulos_plano_de_carga)

    def plot_axes_and_equivalent_force_line(self, seccion, lista_ang_planos_de_carga):
        lista_ang_planos_de_carga.sort()
        xmin, xmax, ymin, ymax = seccion.x_min, seccion.x_max, seccion.y_min, seccion.y_max

        line_styles = ['solid', 'dash', 'dot', 'dashdot']
        line_colors = ['grey', 'black']

        # Adjust limits to include a margin
        margin = 0.05  # 5% of each axis range
        xmin_margin = xmin - (xmax - xmin) * margin
        xmax_margin = xmax + (xmax - xmin) * margin
        ymin_margin = ymin - (ymax - ymin) * margin
        ymax_margin = ymax + (ymax - ymin) * margin

        for i, angulo in enumerate(lista_ang_planos_de_carga):

            angulo_rad = np.radians(angulo)
            x_intersect_min = xmin_margin
            x_intersect_max = xmax_margin
            if angulo != 0:
                m = np.tan(np.pi / 2 - angulo_rad)  # Slope of the line
                y_at_xmin_margin = m * xmin_margin
                y_at_xmax_margin = m * xmax_margin
                x_at_ymin_margin = ymin_margin / m if m != 0 else float('inf')  # Check for division by zero
                x_at_ymax_margin = ymax_margin / m if m != 0 else float('inf')
                puntos = []
                if ymin_margin <= y_at_xmin_margin <= ymax_margin:
                    puntos.append((xmin_margin, y_at_xmin_margin))
                if ymin_margin <= y_at_xmax_margin <= ymax_margin:
                    puntos.append((xmax_margin, y_at_xmax_margin))
                if xmin_margin <= x_at_ymin_margin <= xmax_margin:
                    puntos.append((x_at_ymin_margin, ymin_margin))
                if xmin_margin <= x_at_ymax_margin <= xmax_margin:
                    puntos.append((x_at_ymax_margin, ymax_margin))
            else:
                puntos = [(0, ymin_margin), (0, ymax_margin)]

            # Choose line style based on index, cycling through the list of styles
            line_style = line_styles[i % len(line_styles)]
            line_color = line_colors[i // len(line_styles) % len(line_colors)]

            # Add line to the figure
            x_puntos, y_puntos = zip(*puntos)
            self.fig.add_trace(go.Scatter(x=x_puntos, y=y_puntos, mode='lines',
                                          line=dict(color=line_color, width=3, dash=line_style),
                                          visible=True,
                                          legendgroup="group0",
                                          legendgrouptitle={"text": "PLANOS DE CARGA"},
                                          name=f"λ: {angulo}°"))

    def reinforcement_colour_per_string(self, string):
        crimson_scale_colors = [
            "rgb(255, 0, 0)",  # Pure Red
            "rgb(0, 0, 255)",  # Blue
            "rgb(241, 196, 15)",  # Gold
            "rgb(46, 204, 113)",  # Emerald
            "rgb(255, 0, 255)",  # Magenta
            "rgb(255, 140, 0)",  # Dark Orange
            "rgb(0, 255, 255)",  # Cyan
            "rgb(128, 0, 128)",  # Purple
            "rgb(255, 165, 0)",  # Orange,
            "rgb(139, 0, 0)",  # Dark Red

        ]

        if string not in self.strings_y_color:
            color = crimson_scale_colors[self.indice_color % len(crimson_scale_colors)]
            self.strings_y_color[string] = color
            # Incrementamos el índice para la próxima asignación
            self.indice_color += 1
        return self.strings_y_color[string]

    def plot_reinforcement_bars_as_circles(self, passive_reinforcement, active_reinforcement):
        lista_de_diametros = set()
        shapes_list = []
        x_for_hover_text = []
        y_for_hover_text = []
        text_for_hover_text = []
        color = []
        for barra in passive_reinforcement + active_reinforcement:  # Combine for simplicity
            # Determine if it's pasivo or activo based on the type of 'barra'
            tipo = "ACERO PASIVO" if barra in passive_reinforcement else "ACERO ACTIVO"
            if barra in passive_reinforcement:
                radio = barra.diametro / 20
                acero_y_diamtro_string = f"{barra.tipo}<br>Ø{round(barra.diametro)}mm"
                hover_text = f"<b>Barra {barra.identificador}</b><br>x: {barra.xg} cm<br>y: {barra.yg} cm<br>Tipo: {barra.tipo}<br>Ø{barra.diametro}mm"
            else:
                radio = (barra.area / math.pi) ** 0.5  # Equivalente
                acero_y_diamtro_string = f"{barra.tipo}<br>Área: {barra.area}cm²"
                hover_text = f"<b>Barra {barra.identificador}</b><br>x: {barra.xg} cm<br>y: {barra.yg} cm<br>Tipo: {barra.tipo}<br>Área efectiva: {barra.area}cm²"

            # Add shapes for circles
            shapes_list.append(dict(
                type="circle",
                xref="x", yref="y",
                x0=barra.xg - radio, y0=barra.yg - radio,
                x1=barra.xg + radio, y1=barra.yg + radio,
                fillcolor=self.reinforcement_colour_per_string(acero_y_diamtro_string),
                line_color=self.reinforcement_colour_per_string(acero_y_diamtro_string),
                legendgroup=f"group{1 if tipo=='ACERO PASIVO' else 2}",
                legendgrouptitle_text=tipo,
                name=acero_y_diamtro_string,
                showlegend=acero_y_diamtro_string not in lista_de_diametros
            ))
            lista_de_diametros.add(acero_y_diamtro_string)

            # Prepare hover text data
            x_for_hover_text.append(barra.xg)
            y_for_hover_text.append(barra.yg)
            text_for_hover_text.append(hover_text)
            color.append(self.reinforcement_colour_per_string(acero_y_diamtro_string))

        self.fig.update_layout(shapes=shapes_list)

        self.fig.add_trace(go.Scatter(
            x=x_for_hover_text,
            y=y_for_hover_text,
            mode='markers',
            marker=dict(size=0),
            hoverinfo='text',
            text=text_for_hover_text,
            showlegend=False,
            hoverlabel=dict(bgcolor=color),
        ))

    @staticmethod
    def plotly_arc(xc, yc, radio, angulo_inicial, angulo_final, arc_division=50, color="Cyan", espesor=1, transparencia=1.00):
        theta = np.linspace(np.radians(angulo_inicial), np.radians(angulo_final), arc_division)
        x = xc + radio * np.cos(theta)
        y = yc + radio * np.sin(theta)

        return go.Scatter(x=x, y=y, mode='lines',
                          line=dict(color=color, width=espesor, dash='solid'),
                          hoverinfo='skip',
                          showlegend=False,
                          opacity=transparencia)

    @staticmethod
    def plotly_segmento(nodo1, nodo2, color, espesor=2, transparencia=0.9, **kwargs):
        x = [nodo1.x, nodo2.x]
        y = [nodo1.y, nodo2.y]

        return go.Scatter(x=x, y=y, mode='lines', line=dict(color=color, width=espesor, dash='solid'),
                          hoverinfo='skip',
                          opacity=transparencia,
                          **kwargs)

    def plot_annular_sector(
            self, annular_sector, arc_division=100, color="Cyan", thickness=None, show_centroid=False, transparency=1.00):
        self.fig.add_trace(
            self.plotly_arc(annular_sector.xc,
                            annular_sector.yc,
                            annular_sector.radio_externo,
                            annular_sector.angulo_inicial,
                            annular_sector.angulo_final,
                            arc_division,
                            color,
                            thickness,
                            transparency))

        # Plotear el arco interno (si hay)
        if annular_sector.radio_interno > 0:
            self.fig.add_trace(
                self.plotly_arc(annular_sector.xc,
                                annular_sector.yc,
                                annular_sector.radio_interno,
                                annular_sector.angulo_inicial,
                                annular_sector.angulo_final,
                                arc_division,
                                color,
                                thickness,
                                transparency))

        # Segmentos rectos
        if annular_sector.segmentos_rectos is not None:
            for segmento in annular_sector.segmentos_rectos:
                self.fig.add_trace(self.plotly_segmento(
                    segmento.start_node, segmento.end_node, color, thickness, transparency, showlegend=False))

        # Centroide de los elementos
        if show_centroid:
            self.fig.add_trace(
                go.Scatter(x=[annular_sector.xg], y=[annular_sector.yg], mode='markers',
                           marker=dict(color=color, size=annular_sector.area / 300),
                           opacity=transparency, showlegend=False))  # Adjust size as needed

        self.fig.update_layout(showlegend=True)

    def build_result_html(
            self,
            geometric_solution: Any,
            x_list: list,
            y_list: list,
            z_list: list,
            hover_text_list: list,
            color_list: list,
            is_capped_list: list,
            data_subsets: Dict,
            project_path: str,
            file_name: str
    ):
        """
        Orchestrates the HTML result generation and opens it in the browser.
        """
        fig_interactive, fig_2d_list = self._render_fig(geometric_solution, x_list, y_list, z_list, hover_text_list, color_list, is_capped_list, data_subsets)
        static_assets = self._load_static_assets(Path(project_path))
        context = self._build_html_context(fig_interactive, geometric_solution, static_assets, project_path, file_name)
        html_path = self._write_temp_html_file(static_assets["template"], context)
        webbrowser.open(f"file://{html_path}")
        return fig_interactive, fig_2d_list

    def _render_fig(self, gs, x, y, z, text, color, is_capped, data_subsets):
        tipo = gs.problema["tipo"]
        resultados_en_wb = gs.problema.get("resultados_en_wb", False)

        if tipo == "2D":
            fig = self.print_2d(gs, x, y, z, text, color, is_capped, data_subsets)
            if resultados_en_wb:
                gs.insertar_valores_2D(data_subsets, gs.problema.get("puntos_a_verificar"))
            fig.update_layout(autosize=True)
            return fig, None
        else:
            fig = self.print_3d(gs, x, y, z, text, color, is_capped, data_subsets)
            if resultados_en_wb:
                gs.insertar_valores_3D(data_subsets)
            fig.update_layout(autosize=True)
            return fig, [self.print_2d(gs, **self._2d_arguments(subset_data, lambda_angle)) for lambda_angle, subset_data in data_subsets.items()]

    def _2d_arguments(self, subset_data, lambda_angle):
        return dict(lista_x_total=subset_data["x"], lista_y_total=subset_data["y"], lista_z_total=subset_data["z"],
                    lista_text_total=subset_data["text"], lista_color_total=subset_data["color"],
                    is_capped_list=subset_data["is_capped"], data_subsets={lambda_angle: subset_data},
                    lambda_angle_3d_only=lambda_angle)

    def _load_static_assets(self, project_path: Path) -> Dict[str, Any]:
        html_dir = project_path / "build" / "html"
        assets_dir = html_dir / "assets"
        icon_path = project_path / "build" / "images" / "Logo_H.ico"

        return {
            "template": self._read_text_file(html_dir / "result_format.html"),
            "main_css": self._read_text_file(assets_dir / "css" / "main.css"),
            "noscript_css": self._read_text_file(assets_dir / "css" / "noscript.css"),
            "ctrl_p_js": self._read_text_file(assets_dir / "js" / "ctrl_p.js"),
            "encoded_icon": self._read_binary_file(icon_path)
        }

    def _build_html_context(self, fig, gs, assets: Dict[str, str], project_path: str, file_name: str) -> Dict[str, str]:
        html_engine = ACSAHEHtmlEngine(project_path)
        self.section_fig = gs.construir_grafica_seccion_plotly()
        return {
            "icon_encoded": assets["encoded_icon"],
            "archivo": f"Archivo: {file_name}",
            "main_css": assets["main_css"],
            "noscript_css": assets["noscript_css"],
            "ctrl_p_js": assets["ctrl_p_js"],
            "html_seccion": self.section_fig.to_html(
                full_html=False,
                config=self.get_fig_html_config("ACSAHE - Sección")
            ),
            "tabla_propiedades": html_engine.propiedades_html(gs),
            "tabla_caracteristicas_materiales": html_engine.caracteristicas_materiales_html(gs),
            "html_resultado": fig.to_html(
                full_html=False,
                include_plotlyjs='cdn',
                config=self.get_fig_html_config(f"ACSAHE - Resultado {gs.problema['tipo']}")
            ),
            "foto_logo": f"{project_path}/build/images/LOGO%20ACSAHE.webp"
        }

    def _write_temp_html_file(self, template: str, context: Dict[str, str]) -> str:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.html', mode='wb') as tmp_file:
            tmp_file.write(template.format(**context).encode("utf-8"))
            return tmp_file.name

    @staticmethod
    def _read_text_file(path: Path) -> str:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    @staticmethod
    def _read_binary_file(path: Path):
        with open(path, "rb") as f:
            content = base64.b64encode(f.read())
            return content.decode("utf-8")

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
                 lista_color_total, is_capped_list, data_subsets):

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
        result = self.get_fig_3d_params(data_subsets, estados_subsets)

        for trace in result["traces"]:
            fig.add_trace(trace)


        rango_min = min(min(lista_x_total + X), min(lista_y_total + Y))
        rango_max = max(max(lista_x_total + X), max(lista_y_total + Y))

        # self.agregar_punto_estado(fig, X, Y, Z, NOMBRE)

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
                direction="down",
                buttons=result["buttons"],
                x=0.02,
                y=0.98,
                xanchor='left',
                yanchor='top',
                bgcolor='rgba(240,240,240,0.7)',
                bordercolor='gray',
                borderwidth=1
            )]
        )

        return fig

    def get_fig_3d_params(self, data_subsets, estados_subsets):
        all_traces = []
        buttons = []
        trace_indices_map = {}  # maps each lambda_angle to its exact trace indices

        for lambda_angle, lists in data_subsets.items():
            # track starting index before adding new traces
            current_trace_start_idx = len(all_traces)

            # build capped & not_capped traces
            capped_trace = self._build_scatter3d_trace(
                x=lists["x"], y=lists["y"], z=lists["z"],
                color=lists["color"], text=lists["text"],
                is_capped_list=lists["is_capped"],
                capped=True
            )
            not_capped_trace = self._build_scatter3d_trace(
                x=lists["x"], y=lists["y"], z=lists["z"],
                color=lists["color"], text=lists["text"],
                is_capped_list=lists["is_capped"],
                capped=False
            )

            all_traces.extend([capped_trace, not_capped_trace])

            # store indices for this lambda_angle
            indices_for_this_lambda = [current_trace_start_idx, current_trace_start_idx + 1]

            # add verify trace if applicable
            if estados_subsets.get(lambda_angle):
                verify_trace = self._build_verify_trace(estados_subsets[lambda_angle])
                all_traces.append(verify_trace)
                indices_for_this_lambda.append(current_trace_start_idx + 2)

            trace_indices_map[lambda_angle] = indices_for_this_lambda

        total_traces = len(all_traces)

        # add "Mostrar todos" button
        buttons.append(self._build_show_all_button(total_traces))

        # create a button for each lambda_angle
        for lambda_angle, indices in trace_indices_map.items():
            buttons.append(self._build_visibility_button(lambda_angle, indices, total_traces))

        return {"traces": all_traces, "buttons": buttons}

    def _build_scatter3d_trace(self, x, y, z, color, text, is_capped_list, capped=True):
        # filter points based on capped status
        filtered_x, filtered_y, filtered_z, filtered_color, filtered_text = [], [], [], [], []
        for i, is_capped in enumerate(is_capped_list):
            if is_capped == capped:
                filtered_x.append(x[i])
                filtered_y.append(y[i])
                filtered_z.append(z[i])
                filtered_color.append(color[i] if capped is False else "Grey")
                filtered_text.append(text[i])

        return go.Scatter3d(
            x=filtered_x,
            y=filtered_y,
            z=filtered_z,
            mode='markers',
            marker=dict(size=2, color=filtered_color),
            text=filtered_text,
            hoverinfo='text',
            name='Contorno diagrama de interacción',
            visible=True,
            showlegend=False,
            opacity=0.10 if capped else 1
        )

    def _build_verify_trace(self, estado_subset):
        return go.Scatter3d(
            x=estado_subset["x"],
            y=estado_subset["y"],
            z=estado_subset["z"],
            mode='markers',
            marker=dict(size=4, color="black", symbol='diamond-open'),
            text=self.hover_text_estados(
                estado_subset["x"], estado_subset["y"], estado_subset["z"], estado_subset["nombre"]
            ),
            hoverinfo='text',
            name='Estados de carga',
            visible=True,
            showlegend=False
        )

    def _build_show_all_button(self, total_traces):
        return dict(
            label="Mostrar todos",
            method="update",
            args=[{"visible": [True] * total_traces}]
        )

    def _build_visibility_button(self, lambda_angle, indices_to_show, total_traces):
        visible = [False] * total_traces
        for idx in indices_to_show:
            visible[idx] = True

        return dict(
            label=f"λ={lambda_angle}º",
            method="update",
            args=[{"visible": visible}]
        )

    def print_2d(self, solucion_geometrica, lista_x_total, lista_y_total, lista_z_total, lista_text_total,
                 lista_color_total, is_capped_list,
                 data_subsets, lambda_angle_3d_only=None):
        fig = go.Figure(layout_template="plotly_white")
        lista_x_total = [(1 if x > 0 else -1 if x != 0 else 1 if y >= 0 else -1) * math.sqrt(x ** 2 + y ** 2) for
                         x, y
                         in
                         zip(lista_x_total, lista_y_total)]

        if solucion_geometrica.problema["tipo"] == "3D":  # Plotting 2D in report
            # if planod_de_carga is an int, it is because Mx=My=0 and there are infinite planoes_de_carga
            X = [(1 if x["Mx"] >= 0 else -1) * math.sqrt(x["Mx"] ** 2 + x["My"] ** 2) for x in solucion_geometrica.problema["puntos_a_verificar"] if isinstance(x["plano_de_carga"], int) or x["plano_de_carga"] == float(lambda_angle_3d_only)]
            Y = [x["P"] for x in solucion_geometrica.problema["puntos_a_verificar"] if isinstance(x["plano_de_carga"], int) or x["plano_de_carga"] == float(lambda_angle_3d_only)]
        else:
            X = [x["M"] for x in solucion_geometrica.problema["puntos_a_verificar"]]
            Y = [x["P"] for x in solucion_geometrica.problema["puntos_a_verificar"]]

        nombre = [x["nombre"] for x in solucion_geometrica.problema["puntos_a_verificar"]]
        text_estados_2d = self.hover_text_estados_2d(X, Y, nombre)

        opacity_lambda = lambda bool: 0.07 if bool is True else 1.00
        modified_color_list = lista_color_total.copy()
        for i, color in enumerate(lista_color_total):
            if is_capped_list[i]:
                modified_color_list[i] = "Grey"

        fig.add_trace(go.Scatter(
            x=lista_x_total,
            y=lista_z_total,
            mode='markers',
            marker=dict(size=4, color=modified_color_list, opacity=[opacity_lambda(x) for x in is_capped_list]),
            text=lista_text_total,
            hoverinfo='text',
            name='Contorno diagrama de interacción',
            visible=True,
        ))

        fig.add_trace(go.Scatter(
            x=X,
            y=Y,
            mode='markers',
            marker=dict(size=14,
                        color='black',
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

    @staticmethod
    def get_fig_html_config(file_name="ACSAHE"):
        return {
            'responsive': True,
            'toImageButtonOptions': {
                'format': 'png',
                'filename': file_name,
                'height': 800,
                'width': 1000,
                'scale': 9  # 1 por defecto, más implica mayor resolución
            }
        }
