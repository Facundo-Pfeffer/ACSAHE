import traceback

import numpy as np
import os
import sys
from PyQt5.QtWidgets import (
    QApplication
)
from tkinter import messagebox

from interaction_diagram.interaction_diagram_builder import DiagramaInteraccion2D
from geometry.section_analysis import ACSAHEGeometricSolution
from build.utils.plotly_engine import ACSAHEPlotlyEngine
from report.report_engine import ACSAHEReportEngine

def show_message(message, titulo="Mensaje"):
    messagebox.showinfo(titulo, message)


class ACSAHE:
    progress_bar_messages = {
        "Inicio": "Geometría completada. Construyendo diagrama de interacción para plano de carga λ={plano_de_carga}° ...",
        "Medio": "Construyendo diagrama de interacción para plano de carga λ={plano_de_carga}° ...",
        "Ultimo": "Construyendo resultados ..."
    }

    def __init__ (self, app_gui, input_file_name, path_to_input_file, html_folder_path=None, pdf_folder_path=None):
        super().__init__()
        # Gathering useful paths on user's PC
        self.input_file_name = input_file_name
        self.path_to_input_file = path_to_input_file
        self.path_to_exe = self.get_base_path()

        self.app_gui = app_gui
        self.save_html = bool(html_folder_path)
        self.html_folder_path = html_folder_path
        self.generate_pdf = bool(pdf_folder_path)
        self.pdf_folder_path = pdf_folder_path
        self.geometric_solution = None
        self.plotly_data_subsets = {}
        self.plotly_engine = ACSAHEPlotlyEngine()

        self.x_total, self.y_total, self.z_total = [], [], []
        self.hover_text_total, self.color_total, self.is_capped_total = [], [], []
        self.nominal_x_total, self.nominal_y_total, self.nominal_z_total = [], [], []

        self.start_process()


    @staticmethod
    def get_base_path():
        if getattr(sys, 'frozen', False):
            # Running from .exe
            return os.path.dirname(sys.executable)
        else:
            # Running from .py script (debugging)
            return os.path.dirname(os.path.abspath(__file__))

    def update_ui(self, message=None, progress_bar_value: int = None):
        if hasattr(self.app_gui, "update_ui"):
            self.app_gui.update_ui(message=message, value=progress_bar_value)
        QApplication.processEvents()

    def start_process(self):
        try:
            self.update_ui("Construyendo Geometría...", 5)
            self.geometric_solution = ACSAHEGeometricSolution(file_path=self.path_to_input_file)
            geometric_solution = self.geometric_solution

            loading_path_angles = sorted(geometric_solution.lista_ang_plano_de_carga)
            self.total_steps = 2 + len(loading_path_angles)
            QApplication.processEvents()

            self.plotly_data_subsets = {}

            for step_number in range(1, self.total_steps):
                is_last_step = step_number == self.total_steps-1

                if not is_last_step:
                    angle = loading_path_angles[step_number - 1]
                    self._update_progress_message(step_number, angle)

                    partial_2d_solution = DiagramaInteraccion2D(angle if angle != -1 else 0.00, geometric_solution)

                    coordinates_3d, colors_partial, is_capped_partial = geometric_solution.get_3d_coordinates(
                        partial_2d_solution.interaction_diagram_point_list)
                    x_partial, y_partial, z_partial, phi_partial = coordinates_3d
                    is_phi_constant = isinstance(geometric_solution.problema["phi_variable"], float)
                    hover_text_partial = self._get_hover_text(
                        x_partial, y_partial, z_partial, phi_partial, angle, is_phi_constant)

                    self.plotly_data_subsets[str(angle)] = {
                        "x": x_partial.copy(),
                        "y": y_partial.copy(),
                        "z": z_partial.copy(),
                        "phi": phi_partial.copy(),
                        "text": hover_text_partial.copy(),
                        "color": colors_partial.copy(),
                        "is_capped": is_capped_partial.copy()
                    }

                    self.x_total.extend(x_partial)
                    self.y_total.extend(y_partial)
                    self.z_total.extend(z_partial)
                    self.hover_text_total.extend(hover_text_partial)
                    self.color_total.extend(colors_partial)
                    self.is_capped_total.extend(is_capped_partial)

                    self.nominal_x_total.extend((np.array(x_partial) / np.array(phi_partial)).tolist())
                    self.nominal_y_total.extend((np.array(y_partial) / np.array(phi_partial)).tolist())
                    self.nominal_z_total.extend((np.array(z_partial) / np.array(phi_partial)).tolist())

                else:
                    self.update_ui(
                        self.progress_bar_messages["Ultimo"],
                        int(step_number / self.total_steps * 100)
                    )
                    fig, fig_2d_list = self.plotly_engine.build_result_html(
                        geometric_solution,
                        self.x_total, self.y_total, self.z_total,
                        self.hover_text_total, self.color_total, self.is_capped_total,
                        self.plotly_data_subsets,
                        self.path_to_exe,
                        self.input_file_name
                    )
                    if self.generate_pdf:
                        interaction_diagram = fig if geometric_solution.problema["tipo"] == "2D" else fig_2d_list
                        engine = ACSAHEReportEngine(
                            template_path=f'{self.path_to_exe}/build/pdf/ACSAHE Report Template.docx',
                            geometric_solution=geometric_solution,
                            plots={"[Gráfico de la sección]": self.plotly_engine.section_fig,
                                "[Resultado del diagrama de interacción]":  interaction_diagram},
                            filename=f'{self.input_file_name}',
                        )
                        engine.build_report()
                        name_no_extension = ".".join(self.input_file_name.split(".")[:-1]) if "." in self.input_file_name else self.input_file_name
                        engine.save_report(f"{self.pdf_folder_path}/{name_no_extension}.docx")

        except Exception as e:
            traceback.print_exc()
            raise e
        finally:
            extra_msg = self.obtener_mensaje_hoja_de_resultados(self.geometric_solution)
            self.update_ui(f"ACSAHE ha finalizado!{extra_msg}", progress_bar_value=100)
            QApplication.processEvents()

    @staticmethod
    def obtener_mensaje_hoja_de_resultados(solucion_geometrica):
        if solucion_geometrica.problema["tipo"] == "3D" and solucion_geometrica.problema[
            "resultados_en_wb"] is True:
            return "\n\nSe ha habilitado la hoja 'Resultados 3D' en la planilla.\n"
        elif solucion_geometrica.problema["tipo"] == "2D" and solucion_geometrica.problema[
            "resultados_en_wb"] is True:
            return "\n\nSe ha habilitado la hoja 'Resultados 2D' en la planilla.\n"
        return ""

    def _update_progress_message(self, step_number, angle):
        progress = int(step_number / self.total_steps * 100)
        if step_number == 1:
            message = self.progress_bar_messages["Inicio"].format(plano_de_carga=angle)
        else:
            message = self.progress_bar_messages["Medio"].format(plano_de_carga=angle)
        self.update_ui(message, progress)

    def _get_hover_text(self, x_partial, y_partial, z_partial, phi_partial, angle, is_phi_constant):
        if self.geometric_solution.problema["tipo"] == "3D":
            return self.plotly_engine.hover_text_3d(x_partial, y_partial, z_partial, phi_partial, angle, is_phi_constant)
        else:
            return self.plotly_engine.hover_text_2d(x_partial, y_partial, z_partial, phi_partial, angle, is_phi_constant)