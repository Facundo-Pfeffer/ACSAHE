# ACSAHE: Automatización del Cálculo de la Resistencia de Secciones Arbitrarias de Hormigón Estructural.
![GitHub release](https://img.shields.io/github/v/release/Facundo-Pfeffer/ACSAHE?sort=semver&display_name=tag&labelColor=grey&color=blue&link=https%3A%2F%2Fgithub.com%2FFacundo-Pfeffer%2FACSAHE%2Freleases)
![language](https://img.shields.io/badge/language-Python-239120)
![University](https://img.shields.io/github/last-commit/Facundo-Pfeffer/ACSAHE?color=white)


<img src="build/gui/images/COMPLETE LOGO - README.png" align="right" alt="Logo ACSAHE" width="178" height="178">
ACSAHE es un programa dedicado a la elaboración de Diagramas de Interacción Momento-Normal para secciones arbitrarias de hormigón estructural, basado en la reglamentación CIRSOC 201 de la República Argentina.

Fue desarrollado por Facundo L. Pfeffer en conjunto con el Dr. Ing. Oscar Möller en el Instituto de Mecánica Aplicada y Estructuas (IMAE) de la de la Universidad Nacional de Rosario.
## Instalación
Coexisten actualmente **dos versiones** del programa ACSAHE: 
#### Nueva versión: instalación como app de Windows
La Nueva versión cuenta con una instalación más sencilla como app de Windows, la posibilidad de correr todo desde un simple archivo .exe, generar reportes en .pdf y más!
Los pasos para la instalación son:
1. Descargar el instalador desde la sección [Releases](https://github.com/Facundo-Pfeffer/ACSAHE/releases).
2. Ejecutar el archivo **Instalador_ACSAHE.exe**.
3. Seguir las instrucciones del asistente de instalación.
4. Una vez instalado, podés iniciar el programa desde el **menú de inicio** o el **acceso directo en el escritorio**.



#### Versión Legacy Excel/VBA
La versión original del programa que se integra con Excel mediante VBA. Esta versión está **mantenida pero deprecada** - los nuevos usuarios deberían usar la versión moderna de la aplicación de Windows.

Para su instalación, bastará simplemente con descargar el archivo compresible, abrir la planilla base "ACSAHE" y luego seguir el instructivo allí indicado.  **Enlace de descarga:**
https://drive.google.com/file/d/1MHzbSE-l57YmWEzidX8B6qmdM4cQ-EQW/

**Para desarrolladores**: Ver [LEGACY.md](LEGACY.md) para información detallada sobre la integración legacy Excel/VBA, incluyendo instrucciones de compilación y arquitectura.

## Compilación desde el Código Fuente

Para compilar el ejecutable de ACSAHE desde el código fuente:

### Requisitos Previos
- Python 3.9, 3.10, o 3.11
- Todas las dependencias de `requirements.txt`
- PyInstaller: `pip install pyinstaller`

### Compilación Rápida

1. **Instalar dependencias**:
   ```bash
   pip install -r requirements.txt
   pip install pyinstaller
   ```

2. **Compilar el ejecutable**:
   ```bash
   pyinstaller ACSAHE.spec
   ```

3. **Salida**: El ejecutable se creará en `dist/ACSAHE.exe`

### Compilar el Instalador (Opcional)

Para crear un paquete instalador de Windows, necesitarás Inno Setup 6+:

```bash
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer_sctipt.iss
```

El instalador se creará en `dist_installer/Instalador_ACSAHE.exe`

### Documentación Detallada

Para instrucciones de compilación completas, solución de problemas y opciones de configuración avanzadas, ver [BUILD_AND_DEPLOYMENT.md](BUILD_AND_DEPLOYMENT.md).

## Tutoriales en Canal de Youtube
Para lograr un mejor entendimiento por los usuarios y aprendizaje del software, se ha creado un canal de YouTube en el cual se adicionaran progresivamente tutoriales explicativos.  https://www.youtube.com/playlist?list=PL2vqHDQzjyupe7ISb2vA9EGn0Qr31nW7g
## Featured YouTube Videos
[![ACSAHE Presentation](https://ytcards.demolab.com/?id=QqawT_ZerwE&title=PRESENTACIÓN+ARGENTINA+EN+COLEIC+PANAMÁ:+GANADORA+DEL+PRIMER+PUESTO+-+Facundo+L.+Pfeffer&lang=en&timestamp=1638183600&background_color=%230d1117&title_color=%23ffffff&stats_color=%23dedede&max_title_lines=1&width=250&border_radius=5&duration=380 "PRESENTACIÓN ARGENTINA EN COLEIC PANAMÁ: GANADORA DEL PRIMER PUESTO - Facundo L. Pfeffer")](https://youtu.be/QqawT_ZerwE?si=gV1tgwvtkunF_Gk4)

## Bibliografía
[1] Instituto Nacional de Tecnología Industrial (INTI), CIRSOC 201- REGLAMENTO ARGENTINO DE ESTRUCTURAS DE HORMIGÓN. 2005.  
[2] American Concrete Institute, 318-19(22): Building Code Requirements for Structural Concrete and Commentary. American Concrete Institute, 2022. doi: 10.14359/51716937.  
[3] Oscar Möller, HORMIGÓN ESTRUCTURAL, Segunda Edición. Rosario: UNR Editora, 2022.  
[4] Mauro Poliotti, “HORMIGÓN ARMADO DIMENSIONAMIENTO DE SECCIONES DE HORMIGÓN ARMADO DE FORMA GENÉRICA SOLICITADAS A FLEXIÓN COMPUESTA OBLICUA,” Rosario, Argentina., 2013.  
[5] Exacadesign, “Exacad,” www.exacadesign.com. Accessed: Jul. 14, 2024. [Online]. Available: www.exacadesign.com  
[6] ENERCALC., “ENERCALC Structural Engineering Library,” 2024. Accessed: Aug. 27, 2024. [Online]. Available: https://enercalc.com/structural-engineering-library-sel/  
[7] M. Menegotto, “Method of analysis of cyclically loaded RC plane frames including changes in geometry and non-elastic behavior of elements under normal force and bending,” 1973.  
[8] Instituto Nacional de Tecnología Industrial, “REGLAMENTO ARGENTINO PARA CONSTRUCCIONES SISMORRESISTENTES PARTE I CONSTRUCCIONES EN GENERAL,” 2018.  
[9] American Society of Civil Engineers, ASCE 7-22. American Society of Civil Engineers, 2022. doi: 10.1061/9780784415788.  
