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
            ['Hormigón','Calidad del hormigón.\nEl número indica la resistencia característica a la compresión expresada en MPa.', f'H{int(self.geometric_solution.hormigon.fc)}'],
            ['Acero Pasivo', 'Tipo de acero seleccionado para armadura pasiva.', self.geometric_solution.acero_pasivo]
        ]
        if self.geometric_solution.EAP:
            rows.append([
                'Acero Activo',
                'Tipo de acero seleccionado para armadura activa.\nDeformación efectiva del acero de pretensado (producidas las pérdidas).',
                f'{self.geometric_solution.acero_activo}\n{round(self.geometric_solution.def_de_pretensado_inicial * 1000, 2)}‰'
            ])
        rows.append(['Armaduras Transversales', 'Tipo de armadura transversal seleccionada.', self.geometric_solution.tipo_estribo])
        columns = ['Material', 'Descripción', 'Valor']
        self.utils.insert_table('[Tabla de materiales]', columns, rows)

    def _generate_section_properties_table(self):
        rows = [
            ['Área', 'Área de la sección bruta de Hormigón.', f"{round(self.geometric_solution.seccion_H.area, 2)} cm²"],
            ['Ix', 'Inercia con respecto al eje x.', f"{round(self.geometric_solution.seccion_H.Ix, 2)} cm⁴"],
            ['Iy', 'Inercia con respecto al eje y.', f"{round(self.geometric_solution.seccion_H.Iy, 2)} cm⁴"],
            ['ρ', 'Cuantía geométrica de refuerzo pasivo.', self.geometric_solution.EA.cuantia_geometrica(self.geometric_solution.seccion_H.area, output_str=True)]
        ]
        if self.geometric_solution.EAP:
            rows.append(['ρp', 'Cuantía geométrica de refuerzo activo.', self.geometric_solution.EAP.cuantia_geometrica(self.geometric_solution.seccion_H.area, output_str=True)])

        disc_text = []
        if self.geometric_solution.seccion_H.dx: disc_text.append(f"ΔX={round(self.geometric_solution.seccion_H.dx, 2)} cm")
        if self.geometric_solution.seccion_H.dy: disc_text.append(f"ΔY={round(self.geometric_solution.seccion_H.dy, 2)} cm")
        if self.geometric_solution.seccion_H.d_ang: disc_text.append(f"Δθ={round(self.geometric_solution.seccion_H.d_ang, 2)} °")
        if self.geometric_solution.seccion_H.dr: disc_text.append(f"Δr={round(self.geometric_solution.seccion_H.dr, 2)} particiones\n(variación logarítmica)")
        rows.append(['Discretización', f"Tipo de discretización elegida: {self.geometric_solution.nivel_disc}.", "\n".join(disc_text)])

        if self.geometric_solution.EAP:
            rows.append(['Pretensado', 'Deformación elástica inicial causada por la fuerza de pretensado, referida al baricentro.', self.geometric_solution.mostrar_informacion_pretensado()])

        columns = ['Propiedad', 'Descripción', 'Valor']
        self.utils.insert_table('[Tabla de propiedades de la sección]', columns, rows)
