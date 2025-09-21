# report_engine.py
from report.report_utils import DocxReportUtils


class ACSAHEReportEngine:
    def __init__(self, template_path: str, geometric_solution, plots: dict, filename: str):
        self.utils = DocxReportUtils(template_path)
        self.geometric_solution = geometric_solution
        self.plots = plots   # dict like {'[Resultado del diagrama de interacción]': fig1, '[Gráfico de la sección]': fig2}
        self.filename = filename

    def build_report(self):
        # 1. insert filename
        self.utils.replace_text('[Nombre de archivo]', self.filename)

        # 2. generate tables
        self._generate_materials_table()
        self._generate_section_properties_table()

        # 3. insert plots
        for placeholder, fig in self.plots.items():
            self.utils.insert_image(placeholder, fig)

        # 4. (optional) handle input data placeholder if needed in future
        # self.utils.replace_text('[Pegado de la planilla de ingreso de datos]', "Input data here...")

    def save_report(self, output_path):
        self.utils.save(output_path)

    def _generate_materials_table(self):
        rows = [
            ['Hormigón','Calidad del hormigón.\nEl número indica la resistencia característica a la compresión expresada en MPa.', f'H{int(self.geometric_solution.concrete.fc)}'],
            ['Acero Pasivo', 'Tipo de acero seleccionado para armadura pasiva.', self.geometric_solution.acero_pasivo]
        ]
        if self.geometric_solution.prestressed_rebar_array:
            rows.append([
                'Acero Activo',
                'Tipo de acero seleccionado para armadura activa.\nDeformación efectiva del acero de pretensado (producidas las pérdidas).',
                f'{self.geometric_solution.acero_activo}\n{round(self.geometric_solution.def_de_pretensado_inicial * 1000, 2)}‰'
            ])
        rows.append(['Armaduras Transversales', 'Tipo de armadura transversal seleccionada.', self.geometric_solution.tipo_estribo])
        columns = ['Material', 'Descripción', 'Valor']
        column_widths = [0.15, 0.70, 0.15]
        self.utils.insert_table('[Tabla de materiales]', columns, rows, col_widths_percentage=column_widths)

    def _generate_section_properties_table(self):
        rows = [
            ['Área', 'Área de la sección bruta de Hormigón.', f"{round(self.geometric_solution.meshed_section.area, 2)} cm²"],
            ['Ix', 'Inercia con respecto al eje x.', f"{round(self.geometric_solution.meshed_section.Ix, 2)} cm⁴"],
            ['Iy', 'Inercia con respecto al eje y.', f"{round(self.geometric_solution.meshed_section.Iy, 2)} cm⁴"],
            ['ρ', 'Cuantía geométrica de refuerzo pasivo.', self.geometric_solution.rebar_array.cuantia_geometrica(self.geometric_solution.meshed_section.area, output_str=True)]
        ]
        if self.geometric_solution.prestressed_rebar_array:
            rows.append(['ρp', 'Cuantía geométrica de refuerzo activo.', self.geometric_solution.prestressed_rebar_array.cuantia_geometrica(self.geometric_solution.meshed_section.area, output_str=True)])

        disc_text = []
        if self.geometric_solution.meshed_section.dx: disc_text.append(f"ΔX={round(self.geometric_solution.meshed_section.dx, 2)} cm")
        if self.geometric_solution.meshed_section.dy: disc_text.append(f"ΔY={round(self.geometric_solution.meshed_section.dy, 2)} cm")
        if self.geometric_solution.meshed_section.d_ang: disc_text.append(f"Δθ={round(self.geometric_solution.meshed_section.d_ang, 2)} °")
        if self.geometric_solution.meshed_section.dr: disc_text.append(f"Δr={round(self.geometric_solution.meshed_section.dr, 2)} particiones\n(variación logarítmica)")
        rows.append(['Discretización', f"Tipo de discretización elegida: {self.geometric_solution.nivel_disc}.", "\n".join(disc_text)])

        if self.geometric_solution.prestressed_rebar_array:
            rows.append(['Pretensado', 'Deformación elástica inicial causada por la fuerza de pretensado, referida al baricentro.', self.show_prestressed_information()])

        columns = ['Propiedad', 'Descripción', 'Valor']
        column_widths = [0.15, 0.70, 0.15]
        self.utils.insert_table('[Tabla de propiedades de la sección]', columns, rows,  col_widths_percentage=column_widths)

    def show_prestressed_information(self):
        gs = self.geometric_solution
        if not gs.prestressed_rebar_array:
            return ''
        return f"ec: {gs.ec:.2e}<br>φx: {gs.phix:.2e}<br>φy: {gs.phiy:.2e}"