import os
import plotly.graph_objects as go
import numpy as np
import base64
import math
import tempfile
import webbrowser
from pathlib import Path
from typing import Any, Dict
from tkinter import messagebox

from plot.html.html_engine import ACSAHEHtmlEngine
from build.utils.excel_manager import ExcelManager, create_workbook_from_template


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

    def plot_positive_polygon(self, element, color, thickness, transparencia, negative_shapes_list=None):
        negative_shapes_list = [] if negative_shapes_list is None else negative_shapes_list
        negative_polygons_list = [shape for shape in negative_shapes_list if shape.tipo != "Circular"]
        
        # Combine all segments into single lists with None separators for performance
        x_combined = []
        y_combined = []
        
        for unsplit_segment in element.boundary_segments_list:
            split_segment_list = self._split_segment_in_negative_polygons(unsplit_segment, negative_polygons_list)
            for segment in split_segment_list:
                x_combined.extend([segment.start_node.x, segment.end_node.x, None])
                y_combined.extend([segment.start_node.y, segment.end_node.y, None])
        
        # Add single trace instead of multiple traces for better performance
        if x_combined:
            self.fig.add_trace(go.Scatter(
                x=x_combined,
                y=y_combined,
                showlegend=False,
                opacity=transparencia,
                line=dict(width=thickness, color=color),
                hoverinfo='skip',
                mode='lines'
            ))

    def plot_negative_polygon(
            self, element, color, thickness, transparencia, positive_polygons_list, negative_polygons_list):

        uncleaned_segment_list = []

        other_negative_polygons = negative_polygons_list.copy()
        other_negative_polygons.remove(element)

        for segment in element.boundary_segments_list:
            if self._is_segment_in_positive_polygons(segment, positive_polygons_list):
                uncleaned_segment_list.append(segment)  # Before cleaning

        #  Cleaning shared borders among negative polygons
        cleaned_segment_list = uncleaned_segment_list.copy()
        for other_polygon in other_negative_polygons:
            for segment in uncleaned_segment_list:
                if segment in cleaned_segment_list and other_polygon.is_segment_a_border_segment(segment):
                    cleaned_segment_list.remove(segment)

        # Combine all segments into single lists with None separators for performance
        x_combined = []
        y_combined = []
        
        for cleaned_segment in cleaned_segment_list:
            x_combined.extend([cleaned_segment.start_node.x, cleaned_segment.end_node.x, None])
            y_combined.extend([cleaned_segment.start_node.y, cleaned_segment.end_node.y, None])

        # Add single trace instead of multiple traces for better performance
        if x_combined:
            self.fig.add_trace(go.Scatter(
                x=x_combined,
                y=y_combined,
                showlegend=False,
                opacity=transparencia,
                line=dict(width=thickness, color=color),
                hoverinfo='skip',
                mode='lines'
            ))

    @staticmethod
    def _split_segment_in_negative_polygons(segment_to_split, negative_polygons_list):
        segment_split_list = []
        if not negative_polygons_list:
            return [segment_to_split]
        for negative_polygon in negative_polygons_list:
            for negative_segment in negative_polygon.boundary_segments_list:
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

    @staticmethod
    def _is_segment_in_positive_polygons(segment, positive_polygons_list) -> bool:
        for positive_polygon in positive_polygons_list:
            if any(positive_polygon.is_node_inside_borderless_boundaries(node) for node in
                   [segment.start_node, segment.end_node]):
                return True
        return False

    def plot_cross_section(self, seccion, lista_de_angulos_plano_de_carga):
        color = "Grey"
        for region in seccion.solid_regions_list:
            if region.tipo == "Poligonal":
                self.plot_positive_polygon(region, color=color, transparencia=1, thickness=3,
                                           negative_shapes_list=seccion.void_regions_list)
            else:
                self.plot_annular_sector(region,
                                         arc_division=150,
                                         color=color, transparency=1, thickness=4)

        for region in seccion.void_regions_list:
            if region.tipo == "Poligonal":
                self.plot_negative_polygon(
                    region, color=color, transparencia=1, thickness=4,
                    positive_polygons_list=seccion.solid_regions_list,
                    negative_polygons_list=seccion.void_regions_list)
            else:
                self.plot_annular_sector(
                    region,arc_division=150, color=color, transparency=1, thickness=4)

        x_centroide = []
        y_centroide = []
        for element in seccion.elements_list:
            if element.tipo == "Poligonal":
                self.plot_positive_polygon(element, color=color, transparencia=0.2, thickness=1)
            else:
                self.plot_annular_sector(element,
                                         arc_division=100,
                                         color=color,
                                         transparency=0.2,
                                         thickness=1)

            x_centroide.append(element.xg)
            y_centroide.append(element.yg)

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
                legendgroup=f"group{1 if tipo == 'ACERO PASIVO' else 2}",
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
    def plotly_arc(
            xc, yc, radius, start_angle, final_angle, arc_division=50, color="Cyan", thickness=1, opacity=1.00):
        theta = np.linspace(np.radians(start_angle), np.radians(final_angle), arc_division)
        x = xc + radius * np.cos(theta)
        y = yc + radius * np.sin(theta)

        return go.Scatter(x=x, y=y, mode='lines',
                          line=dict(color=color, width=thickness, dash='solid'),
                          hoverinfo='skip',
                          showlegend=False,
                          opacity=opacity)

    @staticmethod
    def plotly_segment(start_node, end_node, color, thickness=2, opacity=0.9, **kwargs):
        x = [start_node.x, end_node.x]
        y = [start_node.y, end_node.y]

        return go.Scatter(x=x, y=y, mode='lines', line=dict(color=color, width=thickness, dash='solid'),
                          hoverinfo='skip',
                          opacity=opacity,
                          **kwargs)

    def plot_annular_sector(
            self, annular_sector, arc_division=100, color="Cyan", thickness=None, show_centroid=False,
            transparency=1.00):
        self.fig.add_trace(
            self.plotly_arc(annular_sector.xc,
                            annular_sector.yc,
                            annular_sector.external_radius,
                            annular_sector.start_angle,
                            annular_sector.end_angle,
                            arc_division,
                            color,
                            thickness,
                            transparency))

        # Plotear el arco interno (si hay)
        if annular_sector.internal_radius > 0:
            self.fig.add_trace(
                self.plotly_arc(annular_sector.xc,
                                annular_sector.yc,
                                annular_sector.internal_radius,
                                annular_sector.start_angle,
                                annular_sector.end_angle,
                                arc_division,
                                color,
                                thickness,
                                transparency))

        # Segmentos rectos
        if annular_sector.boundary_straight_segments_list is not None:
            for segmento in annular_sector.boundary_straight_segments_list:
                self.fig.add_trace(self.plotly_segment(
                    segmento.start_node, segmento.end_node, color, thickness, transparency, showlegend=False))

        # Centroide de los elements_list
        if show_centroid:
            self.fig.add_trace(
                go.Scatter(x=[annular_sector.xg], y=[annular_sector.yg], mode='markers',
                           marker=dict(color=color, size=annular_sector.area / 300),
                           opacity=transparency, showlegend=False))  # Adjust size as needed

        self.fig.update_layout(showlegend=True)

    def result_builder_orchestrator(
            self,
            geometric_solution: Any,
            x_list: list,
            y_list: list,
            z_list: list,
            hover_text_list: list,
            color_list: list,
            is_capped_list: list,
            data_subsets: Dict,
            path_to_exe: str,
            excel_result_path: str,
            base_file_name_no_extension: str,
            html_folder_path: Any,
            excel_folder_path: Any
    ):
        """
        Orchestrates the result generation and opens HTML it in the browser.
        """
        path_not_available_msg = ("Usted ha seleccionado la opción {opt},"
                                  " pero la ruta a la carpeta que ha seleccionado no es válida."
                                  " Por favor, revise la configuración")

        fig_interactive, args_2d_list, fig_2d_list = self._render_fig(
            geometric_solution, x_list, y_list, z_list, hover_text_list, color_list, is_capped_list, data_subsets)

        static_assets = self._load_static_assets(Path(path_to_exe))
        context = self._build_context(fig_interactive, geometric_solution, static_assets, path_to_exe,
                                      excel_result_path)
        html_path = self._write_temp_html_file(static_assets["template"], context)
        webbrowser.open(f"file://{html_path}")
        if html_folder_path:
            if not os.path.exists(html_folder_path):
                messagebox.showinfo("Error", path_not_available_msg.format(opt="de guardar su resultado .html"))
            saved_path = self._save_file_with_increment(html_path, html_folder_path, base_file_name_no_extension,
                                                        ext="html")
        if excel_folder_path:
            if not os.path.exists(excel_folder_path):
                messagebox.showinfo("Error", path_not_available_msg.format(opt="de guardar su resultado Excel"))
            excel_result_path = self._get_file_name_with_increment(excel_folder_path, base_file_name_no_extension,
                                                                   ext="xlsx")
            template_path = context["excel_result_template"]
            excel_path = self._save_sheets_with_names(args_2d_list, excel_result_path, template_path)
        return fig_interactive, fig_2d_list


    def _save_sheets_with_names(self, args_2d_list, output_path, template_path):
        create_workbook_from_template(template_path=template_path, target_path=output_path,
                                      sheet_name=f"λ={args_2d_list[0]['lambda_angle']}°")

        all_sheet_names = []
        all_columns = []
        all_data_lists = []

        for args_2d in args_2d_list:
            lambda_angle = args_2d["lambda_angle"]
            sheet_name = f"λ={lambda_angle}°"
            all_sheet_names.append(sheet_name)

            all_columns.append(["I", "J", "K", "N", "O"])
            all_data_lists.append([
                args_2d["x_total_list"],
                args_2d["y_total_list"],
                args_2d["phi_total_list"],
                args_2d["x_to_verify"],
                args_2d["y_to_verify"],
            ])

        manager = ExcelManager(output_path, read_only=False, visible=False)
        manager.insert_data_into_multiple_sheets(
            sheet_names=all_sheet_names,
            columns_per_sheet=all_columns,
            data_per_sheet=all_data_lists,
            start_row=3,
            single_value_modifications=("G1", [x["lambda_angle"] for x in args_2d_list])
        )
        manager.close()

    def _get_file_name_with_increment(self, destination_folder: str, base_file_name: str, ext):
        """
        Gets the correct filename in the destination folder, avoiding overwrites by adding _1, _2, etc., if needed.

        :param destination_folder: Folder where the HTML should be saved.
        :param base_file_name: Desired base name for the HTML file (without extension).
        :param ext: File extension.
        :return: Path where the HTML was saved.
        """
        destination_folder = Path(destination_folder)
        destination_folder.mkdir(parents=True, exist_ok=True)

        appended_extension = '.' + str(ext) if ext else ''

        target_path = destination_folder / f"{base_file_name}{appended_extension}"
        counter = 1

        while target_path.exists():
            target_path = destination_folder / f"{base_file_name}_{counter}{appended_extension}"
            counter += 1
        return target_path

    def _save_file_with_increment(self, file_source_path: str, destination_folder: str, base_file_name: str,
                                  ext) -> Path:
        """
        Saves the file to the destination folder, avoiding overwrites by adding _1, _2, etc., if needed.

        :param file_source_path: Path to the source file.
        :param destination_folder: Folder where the HTML should be saved.
        :param base_file_name: Desired base name for the HTML file (without extension).
        :param ext: File extension.
        :return: Path where the HTML was saved.
        """
        target_path = self._get_file_name_with_increment(destination_folder, base_file_name, ext)

        with open(file_source_path, 'r', encoding='utf-8') as src_file:
            content = src_file.read()

        with open(target_path, 'w', encoding='utf-8') as dest_file:
            dest_file.write(content)

        return target_path

    def _render_fig(self, gs, x, y, z, text, color, is_capped, data_subsets):
        tipo = gs.problema["tipo"]

        if tipo == "2D":
            arguments_2d_list = [self._get_2d_args(subset_data, lambda_angle, gs) for lambda_angle, subset_data in
                                 data_subsets.items()]
            fig_2d = self.plot_2d(**arguments_2d_list[0])
            fig_2d.update_layout(autosize=True)
            return fig_2d, arguments_2d_list, [fig_2d]
        else:
            fig_3d = self.plot_3d(gs, x, y, z, text, color, is_capped, data_subsets)
            fig_3d.update_layout(autosize=True)
            arguments_2d_list = [self._get_2d_args(subset_data, lambda_angle, gs) for lambda_angle, subset_data in
                                 data_subsets.items()]
            figs_2d_list = [self.plot_2d(**args_2d) for args_2d in arguments_2d_list]
            return fig_3d, arguments_2d_list, figs_2d_list

    def _get_2d_args(self, subset_data, lambda_angle, geometric_solution):
        try:
            lambda_value = float(lambda_angle)
        except (TypeError, ValueError):
            lambda_value = 0.0

        # Angles equal to -1 are treated as 0° in the solver (legacy sentinel), keep consistent here.
        if lambda_value == -1:
            lambda_value = 0.0

        lambda_rad = math.radians(lambda_value)
        cos_lambda = math.cos(lambda_rad)
        sin_lambda = math.sin(lambda_rad)

        x_total_list = []
        plane_indices = subset_data.get("plane_indices")
        for idx, (x_coord, y_coord) in enumerate(zip(subset_data["x"], subset_data["y"])):
            # `subset_data["x"]` and `["y"]` store -Mx/100 and -My/100 respectively.
            mx_component = -x_coord
            my_component = -y_coord
            mn_lambda = mx_component * cos_lambda + my_component * sin_lambda
            if plane_indices and idx < len(plane_indices):  # Ordering by indices to avoid extreme cases for switching results consistency.
                plane_idx = plane_indices[idx]
                expected_sign = 1 if plane_idx >= 0 else -1
                if mn_lambda == 0:
                    mn_lambda = 0.0
                elif mn_lambda * expected_sign < 0:
                    mn_lambda = abs(mn_lambda) * expected_sign
            x_total_list.append(mn_lambda)

        x_to_verify, y_to_verify, comb_id_to_verify = self._get_load_combinations_data(geometric_solution, lambda_angle)
        return dict(x_total_list=x_total_list, y_total_list=subset_data["z"], phi_total_list=subset_data["phi"],
                    text_total_list=subset_data["text"], color_total_list=subset_data["color"],
                    is_capped_list=subset_data["is_capped"], data_subsets={lambda_angle: subset_data},
                    x_to_verify=x_to_verify, y_to_verify=y_to_verify, comb_id_to_verify=comb_id_to_verify,
                    lambda_angle=lambda_angle)

    def _load_static_assets(self, project_path: Path) -> Dict[str, Any]:
        html_dir = project_path / "build" / "html"
        assets_dir = html_dir / "assets"
        icon_path = project_path / "build" / "gui" / "images" / "Logo_H.ico"

        return {
            "template": self._read_text_file(html_dir / "result_format.html"),
            "main_css": self._read_text_file(assets_dir / "css" / "main.css"),
            "noscript_css": self._read_text_file(assets_dir / "css" / "noscript.css"),
            "ctrl_p_js": self._read_text_file(assets_dir / "js" / "ctrl_p.js"),
            "encoded_icon": self._read_binary_file(icon_path)
        }

    def _build_context(self, fig, gs, assets: Dict[str, str], project_path: str, file_name: str) -> Dict[str, str]:
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
                # Use CDN so this block loads Plotly.js before executing its own script.
                # This avoids 'Plotly is not defined' errors when the section is rendered
                # before the main result figure.
                include_plotlyjs='cdn',
                config=self.get_fig_html_config("ACSAHE - Sección")
            ),
            "tabla_propiedades": html_engine.propiedades_html(gs),
            "tabla_caracteristicas_materiales": html_engine.caracteristicas_materiales_html(gs),
            "html_resultado": fig.to_html(
                full_html=False,
                include_plotlyjs='cdn',
                config=self.get_fig_html_config(f"ACSAHE - Resultado {gs.problema['tipo']}")
            ),
            "foto_logo": f"{project_path}/build/gui/images/LOGO%20ACSAHE.webp",
            "excel_result_template": f"{project_path}/build/EXCEL result template.xlsx"
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

    def plot_3d(self, geometric_solution, x_total_list, y_total_list, z_total_list, text_total_list,
                color_total_list, is_capped_list, data_subsets):

        plano_de_carga_lista = set(x["plano_de_carga"] for x in geometric_solution.problema["puntos_a_verificar"])
        plano_de_carga_lista = list(plano_de_carga_lista)
        plano_de_carga_lista.sort()
        estados_subsets = {}
        for punto_a_verificar in geometric_solution.problema["puntos_a_verificar"]:
            plano_de_carga = str(round(float(punto_a_verificar["plano_de_carga"]), 2))
            if plano_de_carga not in estados_subsets:  # Inicialización
                estados_subsets[plano_de_carga] = {"x": [], "y": [], "z": [], "nombre": []}
            estados_subsets[plano_de_carga]["x"].append(punto_a_verificar["Mx"])
            estados_subsets[plano_de_carga]["y"].append(punto_a_verificar["My"])
            estados_subsets[plano_de_carga]["z"].append(punto_a_verificar["P"])
            estados_subsets[plano_de_carga]["nombre"].append(punto_a_verificar["nombre"])

        X = [x["Mx"] for x in geometric_solution.problema["puntos_a_verificar"]]
        Y = [x["My"] for x in geometric_solution.problema["puntos_a_verificar"]]
        Z = [x["P"] for x in
             geometric_solution.problema["puntos_a_verificar"]]  # Positivo para transformar a compresión positiva
        NOMBRE = [x["nombre"] for x in geometric_solution.problema["puntos_a_verificar"]]

        plano_de_carga_lista = [x["plano_de_carga"] for x in geometric_solution.problema["puntos_a_verificar"]]
        plano_de_carga_lista.sort()

        fig = go.Figure(layout_template="plotly_white")
        result = self.get_fig_3d_params(data_subsets, estados_subsets)

        for trace in result["traces"]:
            fig.add_trace(trace)

        rango_min = min(min(x_total_list + X), min(y_total_list + Y))
        rango_max = max(max(x_total_list + X), max(y_total_list + Y))

        # self.agregar_punto_estado(fig, X, Y, Z, NOMBRE)

        gridline_conf = dict(linecolor="Black",
                             showline=True,
                             linewidth=2,
                             title=dict(
                                 font=dict(
                                     family="Times New Roman",
                                     size=16,
                                     color="black"
                                 )
                             ),
                             tickfont=dict(
                                 color="Black",
                                 family='Times New Roman',
                                 size=14),
                             gridcolor="rgba(0, 0, 0, 0.3)",  # Light grey
                             gridwidth=2
                             )

        fig.update_layout(
            title=dict(
                text=f'<span style="font-size: 30px;">Diagrama de interacción 3D</span></span>',
                x=0.5,
                font=dict(color="rgba(21,82,171,0.90)",
                          family='Times New Roman')),
            scene=dict(
                xaxis_title='<b>ϕMnx [kNm]</b>',
                yaxis_title='<b>ϕMny [kNm]</b>',
                zaxis_title='<b>ϕPn [kN]</b>',
                xaxis=dict(
                    range=[rango_min, rango_max],
                    **gridline_conf
                ),
                yaxis=dict(
                    range=[rango_min, rango_max],
                    **gridline_conf
                ),
                zaxis=dict(
                    range=[min(z_total_list + Z), max(z_total_list + Z)],
                    **gridline_conf
                ),
                aspectmode='manual',  # Set aspect ratio manually
                aspectratio=dict(x=1, y=1, z=1),
            ))

        fig.update_layout(
            updatemenus=[dict(
                type="dropdown",
                direction="down",
                showactive=True,  # Highlight the active selection
                active=0,  # "Mostrar todos" is the default active option (index 0)
                buttons=result["buttons"],
                x=0.02,
                y=0.98,
                xanchor='right',
                yanchor='top',
                bgcolor='rgba(240,240,240,0.7)',
                bordercolor='Grey',
                borderwidth=1,
                font=dict(
                    family="Times New Roman",
                    size=16,
                    color="black"
                )
            )],
            annotations=[
                dict(
                    # Add spaces to match dropdown width (approximately "Mostrar todos" + arrow width)
                    text="<b>Plano de carga&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</b>",
                    x=0.02,
                    y=0.99,
                    xref="paper",
                    yref="paper",
                    xanchor='right',
                    yanchor='bottom',
                    showarrow=False,
                    font=dict(
                        family="Times New Roman",
                        size=16,
                        color="black"
                    ),
                    bgcolor='rgba(240,240,240,0.7)',
                    bordercolor='Grey',
                    borderwidth=1,
                    borderpad=8,  # Padding around the text
                    align='left'  # Align text to left like the dropdown
                )
            ]
        )

        fig.update_layout(
            scene_camera=dict(
                eye=dict(x=1.4, y=1.4, z=1.2)  # zooms out by moving the camera back
            ),
            # Performance optimizations for large datasets
            hovermode='closest',
            transition={'duration': 0},  # Disable animations for better performance
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

        # Create dropdown menu buttons: "Mostrar todos" as default, then all lambda values
        dropdown_buttons = []
        
        # Add "Mostrar todos" as the first/default option
        dropdown_buttons.append(self._build_show_all_button(total_traces))
        
        # Add all lambda angles as dropdown options
        # Sort lambda angles for better organization
        sorted_lambdas = sorted(trace_indices_map.items(), key=lambda x: float(x[0]) if x[0].replace('.', '').replace('-', '').isdigit() else float('inf'))
        for lambda_angle, indices in sorted_lambdas:
            dropdown_buttons.append(self._build_visibility_button(lambda_angle, indices, total_traces))

        return {"traces": all_traces, "buttons": dropdown_buttons}

    def _build_scatter3d_trace(self, x, y, z, color, text, is_capped_list, capped=True):
        # filter points based on capped status
        filtered_x, filtered_y, filtered_z, filtered_color, filtered_text = [], [], [], [], []
        for i, is_capped in enumerate(is_capped_list):
            if is_capped == capped:
                filtered_x.append(x[i])
                filtered_y.append(y[i])
                filtered_z.append(z[i])
                # filtered_color.append(color[i] if capped is False else "Grey")
                filtered_color.append("rgba(21,82,171,0.90)" if capped is False else "Grey")
                filtered_text.append(text[i])

        # Downsample for visualization if dataset is very large (>2000 points per trace)
        max_points = 2000
        if len(filtered_x) > max_points:
            # Keep every nth point to reduce to max_points, preserving shape
            step = len(filtered_x) // max_points
            filtered_x = filtered_x[::step]
            filtered_y = filtered_y[::step]
            filtered_z = filtered_z[::step]
            filtered_color = filtered_color[::step]
            filtered_text = filtered_text[::step]

        # Reduced marker size for better performance with large datasets
        return go.Scatter3d(
            x=filtered_x,
            y=filtered_y,
            z=filtered_z,
            mode='markers',
            marker=dict(size=2, color=filtered_color),
            text=filtered_text,
            hoverinfo='text',
            name='Region diagrama de interacción',
            visible=True,
            showlegend=False,
            opacity=0.50 if capped else 1
        )

    def _build_verify_trace(self, estado_subset):
        return go.Scatter3d(
            x=estado_subset["x"],
            y=estado_subset["y"],
            z=estado_subset["z"],
            mode='markers',
            marker=dict(size=6, color="Crimson", symbol='diamond-open'),
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
            label="<b>Mostrar todos</b>",
            method="update",
            args=[{"visible": [True] * total_traces}]
        )

    def _build_visibility_button(self, lambda_angle, indices_to_show, total_traces):
        visible = [False] * total_traces
        for idx in indices_to_show:
            visible[idx] = True

        return dict(
            label=f"<b>λ={lambda_angle}º</b>",
            method="update",
            args=[{"visible": visible}]
        )

    @staticmethod
    def _get_load_combinations_data(geometric_solution, lambda_angle_3d_only):
        if geometric_solution.problema["tipo"] == "3D":  # Plotting 2D in report
            # if planos_de_carga is an int, it is because Mx=My=0 and there are infinite planos_de_carga
            x_to_verify = [(1 if x["Mx"] >= 0 else -1) * math.sqrt(x["Mx"] ** 2 + x["My"] ** 2) for x in
                           geometric_solution.problema["puntos_a_verificar"] if
                           isinstance(x["plano_de_carga"], int) or x["plano_de_carga"] == float(lambda_angle_3d_only)]
            y_to_verify = [x["P"] for x in geometric_solution.problema["puntos_a_verificar"] if
                           isinstance(x["plano_de_carga"], int) or x["plano_de_carga"] == float(lambda_angle_3d_only)]
        else:
            x_to_verify = [x["M"] for x in geometric_solution.problema["puntos_a_verificar"]]
            y_to_verify = [x["P"] for x in geometric_solution.problema["puntos_a_verificar"]]

        comb_id_to_verify = [x["nombre"] for x in geometric_solution.problema["puntos_a_verificar"]]
        return x_to_verify, y_to_verify, comb_id_to_verify

    def plot_2d(self, x_total_list, y_total_list, text_total_list,
                color_total_list, is_capped_list,
                data_subsets, x_to_verify, y_to_verify, comb_id_to_verify, **kwargs):
        fig = go.Figure(layout_template="plotly_white")

        points_color = "rgb(21,82,171)"

        text_estados_2d = self.hover_text_estados_2d(x_to_verify, y_to_verify, comb_id_to_verify)

        opacity_lambda = lambda bool: 0.70 if bool is True else 1.00
        modified_color_list = color_total_list.copy()
        for i, color in enumerate(color_total_list):
            if is_capped_list[i]:
                modified_color_list[i] = "Grey"
            else:
                modified_color_list[i] = points_color

        # Downsample if too many points for better browser performance
        if len(x_total_list) > 3000:
            step = len(x_total_list) // 3000
            x_total_list = x_total_list[::step]
            y_total_list = y_total_list[::step]
            text_total_list = text_total_list[::step]
            modified_color_list = modified_color_list[::step]
            is_capped_list = is_capped_list[::step]

        fig.add_trace(go.Scatter(
            x=x_total_list,
            y=y_total_list,
            mode='markers',
            marker=dict(size=4, color=modified_color_list, opacity=[opacity_lambda(x) for x in is_capped_list]),
            text=text_total_list,
            hoverinfo='text',
            name='Region diagrama de interacción',
            visible=True,
        ))

        fig.add_trace(go.Scatter(
            x=x_to_verify,
            y=y_to_verify,
            mode='markers',
            marker=dict(size=14,
                        color="Crimson",
                        symbol='diamond'),
            text=text_estados_2d,
            hoverinfo='text',
            name='Estados a verificar',
            visible=True,
        ))

        rango_min_x = min(x_total_list + x_to_verify) * 1.2
        rango_max_x = max(x_total_list + x_to_verify) * 1.2
        rango_min_y = min(y_total_list + y_to_verify) * 1.2
        rango_max_y = max(y_total_list + y_to_verify) * 1.2

        # Custom axis lines
        fig.add_shape(type="line", x0=rango_min_x, y0=0, x1=rango_max_x, y1=0, line=dict(color="black", width=2))
        fig.add_shape(type="line", x0=0, y0=rango_min_y, x1=0, y1=rango_max_y, line=dict(color="black", width=2))

        fig.update_xaxes(title_text="<b>ϕMnλ [kNm]</b>",
                         title_font=dict(
                             family="Times New Roman",
                             size=25),
                         color="Black",
                         gridwidth=1,
                         gridcolor="rgba(0, 0, 0, 0.3)",
                         tickfont=dict(
                             family="Times New Roman",
                             size=25,
                             color="Black"
                         )
                         )
        fig.update_yaxes(title_text="<b>ϕPn [kN]</b>",
                         title_font=dict(
                             family="Times New Roman",
                             size=25),
                         gridwidth=1,
                         gridcolor="rgba(0, 0, 0, 0.3)",
                         tickfont=dict(
                             family="Times New Roman",
                             size=25,
                             color="Black"
                         ),
                         color="Black",
                         )

        fig.update_layout(
            title=dict(
                text=f'<span style="font-size: 30px;"><b>Diagrama de interacción para λ={list(data_subsets.keys())[0]} °</b></span><br>',
                # text=f"<b>ACSAHEArchivo: {self.file_name}</b>",
                x=0.5,
                font=dict(
                    color=points_color,
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
    def hover_text_2d(lista_x, lista_y, lista_z, lista_phi, plano_de_carga, es_phi_constante, plane_indices=None):
        M_lista = [(1 if x > 0 else -1 if x != 0 else 1 if y >= 0 else -1) * math.sqrt(x ** 2 + y ** 2) for x, y in
                   zip(lista_x, lista_y)]
        if plane_indices and len(plane_indices) == len(lista_z):
            return [
                f"ϕPn: {round(z, 2)} kN<br>ϕMnλ: {round(M, 2)} kNm<br>ϕMnx: {round(x, 2)} kNm<br>ϕMny: {round(y, 2)} kNm<br>ϕ: {round(phi, 2)}{' (constante)' if es_phi_constante else ''}<br>λ={plano_de_carga}°<br>Plano índice: {int(plane_idx)}"
                for x, y, z, phi, M, plane_idx in zip(lista_x, lista_y, lista_z, lista_phi, M_lista, plane_indices)]
        else:
            return [
                f"ϕPn: {round(z, 2)} kN<br>ϕMnλ: {round(M, 2)} kNm<br>ϕMnx: {round(x, 2)} kNm<br>ϕMny: {round(y, 2)} kNm<br>ϕ: {round(phi, 2)}{' (constante)' if es_phi_constante else ''}<br>λ={plano_de_carga}°"
                for x, y, z, phi, M in zip(lista_x, lista_y, lista_z, lista_phi, M_lista)]

    @staticmethod
    def hover_text_3d(lista_x, lista_y, lista_z, lista_phi, plano_de_carga, es_phi_constante, plane_indices=None):
        if plane_indices and len(plane_indices) == len(lista_z):
            return [
                f"ϕPn: {round(z, 2)} kN<br>ϕMnx: {round(x, 2)} kNm<br>ϕMny: {round(y, 2)} kNm<br>ϕ: {round(phi, 2)}{' (constante)' if es_phi_constante else ''}<br>λ={plano_de_carga}°<br>Plano índice: {int(plane_idx)}"
                for x, y, z, phi, plane_idx in zip(lista_x, lista_y, lista_z, lista_phi, plane_indices)]
        else:
            return [
                f"ϕPn: {round(z, 2)} kN<br>ϕMnx: {round(x, 2)} kNm<br>ϕMny: {round(y, 2)} kNm<br>ϕ: {round(phi, 2)}{' (constante)' if es_phi_constante else ''}<br>λ={plano_de_carga}°"
                for x, y, z, phi in zip(lista_x, lista_y, lista_z, lista_phi)]

    @staticmethod
    def _convert_to_int_if_possible(int_number):
        try:
            return int(int_number)
        except Exception:
            return int_number

    def hover_text_estados(self, lista_x, lista_y, lista_z, lista_estado):
        return [
            f"<b>Estado: {self._convert_to_int_if_possible(estado)}</b><br>Pu: {round(z, 2)} kN<br>Mxu: {round(x, 2)} kNm<br>Myu: {round(y, 2)} kNm"
            for x, y, z, estado in zip(lista_x, lista_y, lista_z, lista_estado)]

    def hover_text_estados_2d(self, lista_x, lista_y, lista_estado):
        return [
            f"<b>Estado: {self._convert_to_int_if_possible(estado)}</b><br>Pu: {round(y, 2)} kN<br>Mu: {round(x, 2)} kNm"
            for x, y, estado in zip(lista_x, lista_y, lista_estado)]

    @staticmethod
    def get_fig_html_config(file_name="ACSAHE"):
        return {
            'responsive': True,
            'displayModeBar': True,
            'displaylogo': False,
            'scrollZoom': True,
            'toImageButtonOptions': {
                'format': 'png',
                'filename': file_name,
                'height': 800,
                'width': 1000,
                'scale': 9  # 1 por defecto, más implica mayor resolución
            }
        }
