from jinja2 import Environment, FileSystemLoader


class ACSAHEHtmlEngine:
    def __init__(self, project_path):
        template_dir = project_path + "/build/html"
        self.env = Environment(loader=FileSystemLoader(template_dir))

    def caracteristicas_materiales_html(self, geometric_solution):
        template = self.env.get_template("materials_summary_template.html")
        return template.render(
            hormigon=geometric_solution.concrete,
            acero_pasivo=geometric_solution.acero_pasivo,
            acero_activo=geometric_solution.acero_activo,
            def_de_pretensado=geometric_solution.def_de_pretensado_inicial,
            tipo_estribo=geometric_solution.tipo_estribo,
            tiene_acero_activo=bool(geometric_solution.prestressed_rebar_array)
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
            area=geometric_solution.meshed_section.area,
            Ix=geometric_solution.meshed_section.Ix,
            Iy=geometric_solution.meshed_section.Iy,
            cuantia_pasiva=geometric_solution.rebar_array.cuantia_geometrica(geometric_solution.meshed_section.area, output_str=True),
            cuantia_activa=(
                geometric_solution.prestressed_rebar_array.cuantia_geometrica(geometric_solution.meshed_section.area, output_str=True)
                if geometric_solution.prestressed_rebar_array else None
            ),
            nivel_disc=geometric_solution.nivel_disc,
            dx=geometric_solution.meshed_section.dx,
            dy=geometric_solution.meshed_section.dy,
            d_ang=geometric_solution.meshed_section.d_ang,
            dr=geometric_solution.meshed_section.dr,
            info_pretensado=(
                f"ec: {geometric_solution.ec:.2e}<br>φx: {geometric_solution.phix:.2e}<br>φy: {geometric_solution.phiy:.2e}"
                if geometric_solution.prestressed_rebar_array else None
            )
        )

