from diagramas_de_interaccion import ObtenerDiagramaDeInteraccion2D, ObtenerDiagramaDeInteraccion3D

# resolver = ObtenerDiagramaDeInteraccion2D(file_path="Archivos Excel/Ejemplo 1.xlsm", angulo_de_plano_de_carga=0, mostrar_resultado=False)
resolver = ObtenerDiagramaDeInteraccion3D(file_path="Archivos Excel/Ejemplo 1.xlsm", usar_plotly=True, mostrar_seccion=False,
                                          titulo="VIGA A FLEXIÓN")
