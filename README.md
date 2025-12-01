# ACSAHE
![GitHub release](https://img.shields.io/github/v/release/Facundo-Pfeffer/ACSAHE?sort=semver&display_name=tag&labelColor=grey&color=blue&link=https%3A%2F%2Fgithub.com%2FFacundo-Pfeffer%2FACSAHE%2Freleases)
![language](https://img.shields.io/badge/language-Python-239120)
![University](https://img.shields.io/github/last-commit/Facundo-Pfeffer/ACSAHE?color=white)

<img src="build/gui/images/COMPLETE LOGO - README.png" align="right" alt="ACSAHE Logo" width="178" height="178">

[Versión README en Español](README_es.md)

ACSAHE is a desktop application designed to generate interaction diagrams for structural concrete sections subjected to combined axial load and biaxial bending, in full compliance with ACI 318-19(22), Chapter 22.
Built with flexibility and accessibility in mind, ACSAHE enables structural engineers, students, and researchers to perform advanced section-level strength analysis without the need for expensive commercial software.

## Key Features

- **Full Biaxial Strength Diagrams**  
  Computes complete 3D interaction surfaces representing the axial–biaxial bending strength behavior of the section.

- **Arbitrary Section Geometry**  
  Easily define and analyze **any** cross-sectional geometry, including complex or irregular shapes.

- **Prestressed Reinforcement Support**  
  Enables the user to include prestressed reinforcement directly into the analysis—**a rare feature** among similar tools.

It was developed by Facundo L. Pfeffer in collaboration with Dr. Ing. Oscar Möller at the Institute of Applied Mechanics and Structures (IMAE) of the National University of Rosario.

## Installation
There are currently **two versions** of the ACSAHE program:

#### New version: Windows app installation
The New version features a simpler installation as a Windows app, the ability to run everything from a simple .exe file, generate PDF reports, and more!
Installation steps are:
1. Download the installer from the [Releases](https://github.com/Facundo-Pfeffer/ACSAHE/releases) section.
2. Run the **Instalador_ACSAHE.exe** file.
3. Follow the installation wizard instructions.
4. Once installed, you can start the program from the **start menu** or the **desktop shortcut**.

#### Legacy Excel/VBA Version
The original version of the program that integrates with Excel via VBA. This version is **maintained but deprecated** - new users should use the modern Windows app version.

For installation, simply download the compressed file, open the "ACSAHE" base spreadsheet, and then follow the instructions provided there. **Download link:**
https://drive.google.com/file/d/1MHzbSE-l57YmWEzidX8B6qmdM4cQ-EQW/

**For developers**: See [LEGACY.md](LEGACY.md) for detailed information about the legacy Excel/VBA integration, including build instructions and architecture.

## Building from Source

To build the ACSAHE executable from source:

### Prerequisites
- Python 3.9, 3.10, or 3.11
- All dependencies from `requirements.txt`
- PyInstaller: `pip install pyinstaller`

### Quick Build

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install pyinstaller
   ```

2. **Build the executable**:
   ```bash
   pyinstaller ACSAHE.spec
   ```

3. **Output**: The executable will be created at `dist/ACSAHE.exe`

### Building the Installer (Optional)

To create a Windows installer package, you'll need Inno Setup 6+:

```bash
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer_sctipt.iss
```

The installer will be created at `dist_installer/Instalador_ACSAHE.exe`

### Detailed Documentation

For comprehensive build instructions, troubleshooting, and advanced configuration options, see [BUILD_AND_DEPLOYMENT.md](BUILD_AND_DEPLOYMENT.md).

## Tutorials on YouTube Channel
To achieve better user understanding and software learning, a YouTube channel has been created where tutorials will be progressively added. https://www.youtube.com/playlist?list=PL2vqHDQzjyupe7ISb2vA9EGn0Qr31nW7g

## Featured YouTube Videos
[![ACSAHE Presentation](https://ytcards.demolab.com/?id=QqawT_ZerwE&title=ARGENTINA+PRESENTATION+AT+COLEIC+PANAMA:+FIRST+PLACE+WINNER+-+Facundo+L.+Pfeffer&lang=en&timestamp=1638183600&background_color=%230d1117&title_color=%23ffffff&stats_color=%23dedede&max_title_lines=1&width=250&border_radius=5&duration=380 "ARGENTINA PRESENTATION AT COLEIC PANAMA: FIRST PLACE WINNER - Facundo L. Pfeffer")](https://youtu.be/QqawT_ZerwE?si=gV1tgwvtkunF_Gk4)

## References
[1] Instituto Nacional de Tecnología Industrial (INTI), CIRSOC 201- REGLAMENTO ARGENTINO DE ESTRUCTURAS DE HORMIGÓN. 2005.  
[2] American Concrete Institute, 318-19(22): Building Code Requirements for Structural Concrete and Commentary. American Concrete Institute, 2022. doi: 10.14359/51716937.  
[3] Oscar Möller, HORMIGÓN ESTRUCTURAL, Segunda Edición. Rosario: UNR Editora, 2022.  
[4] Mauro Poliotti, “HORMIGÓN ARMADO DIMENSIONAMIENTO DE SECCIONES DE HORMIGÓN ARMADO DE FORMA GENÉRICA SOLICITADAS A FLEXIÓN COMPUESTA OBLICUA,” Rosario, Argentina., 2013.  
[5] Exacadesign, “Exacad,” www.exacadesign.com. Accessed: Jul. 14, 2024. [Online]. Available: www.exacadesign.com  
[6] ENERCALC., “ENERCALC Structural Engineering Library,” 2024. Accessed: Aug. 27, 2024. [Online]. Available: https://enercalc.com/structural-engineering-library-sel/  
[7] M. Menegotto, “Method of analysis of cyclically loaded RC plane frames including changes in geometry and non-elastic behavior of elements under normal force and bending,” 1973.  
[8] Instituto Nacional de Tecnología Industrial, “REGLAMENTO ARGENTINO PARA CONSTRUCCIONES SISMORRESISTENTES PARTE I CONSTRUCCIONES EN GENERAL,” 2018.  
[9] American Society of Civil Engineers, ASCE 7-22. American Society of Civil Engineers, 2022. doi: 10.1061/9780784415788.  
