from jinja2 import Environment, FileSystemLoader


class ACSAHEHtmlEngine:
    def __init__(self, project_path):
        template_dir = project_path + "/build/html"
        self.env = Environment(loader=FileSystemLoader(template_dir))

    def caracteristicas_materiales_html(self, geometria):
        template = self.env.get_template("materials_summary_template.html")
        return template.render(
            hormigon=geometria.hormigon,
            acero_pasivo=geometria.acero_pasivo,
            acero_activo=geometria.acero_activo,
            def_de_pretensado=geometria.def_de_pretensado_inicial,
            tipo_estribo=geometria.tipo_estribo,
            tiene_acero_activo=bool(geometria.EAP)
        )

    def propiedades_html(self, geometric_solution) -> str:
        """
        Generates an HTML section with geometric and reinforcement properties of the section.

        Args:
            geometric_solution (ACSAHEGeometricSolution): Object containing geometric data.

        Returns:
            str: Rendered HTML string.
        """
        template = self.env.get_template("section_properties_template.html")

        return template.render(
            area=geometric_solution.seccion_H.area,
            Ix=geometric_solution.seccion_H.Ix,
            Iy=geometric_solution.seccion_H.Iy,
            cuantia_pasiva=geometric_solution.EA.cuantia_geometrica(geometric_solution.seccion_H.area, output_str=True),
            cuantia_activa=(
                geometric_solution.EAP.cuantia_geometrica(geometric_solution.seccion_H.area, output_str=True)
                if geometric_solution.EAP else None
            ),
            nivel_disc=geometric_solution.nivel_disc,
            dx=geometric_solution.seccion_H.dx,
            dy=geometric_solution.seccion_H.dy,
            d_ang=geometric_solution.seccion_H.d_ang,
            dr=geometric_solution.seccion_H.dr,
            info_pretensado=(
                geometric_solution.mostrar_informacion_pretensado()
                if geometric_solution.EAP else None
            )
        )

