# ACSAHE Build and Deployment Guide

## Overview
ACSAHE uses a two-stage deployment process:
1. **PyInstaller** - Creates a standalone `.exe` file from Python source
2. **Inno Setup** - Creates a Windows installer from the `.exe` file

---

## Stage 1: Creating the .exe File (PyInstaller)

### Build Command (Using Spec File - Recommended)
```bash
pyinstaller ACSAHE.spec
```

The spec file has been updated to include `collect_submodules('plotly')` which automatically handles all Plotly imports. This is the recommended approach as it's cleaner and more maintainable.

#### Output:
- `dist/ACSAHE.exe` - The standalone executable
- `build/` - Temporary build files (can be deleted after verification)

### Requirements:
- Python 3.9, 3.10, or 3.11 (as per CI/CD tests)
- All dependencies from `requirements.txt`:
  - scipy
  - numpy
  - plotly==6.1.0
  - dash
  - xlwings
  - PyQt5
  - uuid
  - psutil
  - jinja2
  - python-docx
  - selenium
  - webdriver-manager
- PyInstaller: `pip install pyinstaller`

---

## Stage 2: Creating the Installer (Inno Setup)

### Configuration File: `installer_sctipt.iss`

The Inno Setup script creates a Windows installer package.

#### Key Settings:

1. **Application Info**:
   - App Name: `ACSAHE`
   - Version: `2.0.0-alpha`
   - Default Install Directory: `{pf}\ACSAHE` (Program Files)
   - Output: `dist_installer\Instalador_ACSAHE.exe`

2. **Files to Include**:
   ```iss
   Source: "dist\ACSAHE.exe"; DestDir: "{app}"
   Source: "build\*"; DestDir: "{app}\build"
   ```
   - The `.exe` file goes to the application root
   - The `build/` folder is copied alongside the `.exe`

3. **Icons Created**:
   - Start Menu shortcut
   - Desktop shortcut (optional, user choice)

4. **Installer Features**:
   - LZMA compression
   - Modern wizard style
   - Custom images and icons
   - Spanish language messages

### Build Command:
```bash
# Using Inno Setup Compiler (ISCC.exe)
iscc installer_sctipt.iss
```

This creates:
- `dist_installer/Instalador_ACSAHE.exe` - The Windows installer

### Requirements:
- Inno Setup 6+ installed on Windows
- The `dist/ACSAHE.exe` file must exist (from Stage 1)
- The `build/` directory must exist with all assets

---

## Complete Build Process

### Step-by-Step Instructions:

1. **Prepare Environment**:
   ```bash
   # Create virtual environment (recommended)
   python -m venv venv
   venv\Scripts\activate
   
   # Install dependencies
   pip install -r requirements.txt
   pip install pyinstaller
   ```

2. **Build Executable**:

   ```bash
   pyinstaller ACSAHE.spec
   ```
   - The spec file includes `collect_submodules('plotly')` to handle all Plotly imports
   - Output: `dist/ACSAHE.exe`
   - Verify the `.exe` works by running it
   - Note: The first build may take several minutes as PyInstaller analyzes dependencies

3. **Build Installer**:
   ```bash
   # Using Inno Setup Compiler
   "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer_sctipt.iss
   ```
   - Output: `dist_installer/Instalador_ACSAHE.exe`

4. **Test Installation**:
   - Run the installer on a clean Windows machine
   - Verify the application launches correctly
   - Test all features (Excel loading, HTML generation, PDF reports)

---

## Important Considerations

### Path Handling in Code

The application uses `get_base_path()` in `acsahe.py` to handle both development and packaged modes:

```python
@staticmethod
def get_base_path():
    if getattr(sys, 'frozen', False):
        # Running from .exe
        return os.path.dirname(sys.executable)
    else:
        # Running from .py script (debugging)
        return os.path.dirname(os.path.abspath(__file__))
```

This ensures the application can find the `build/` directory whether running from source or as an executable.

### Files Included in Build

The `build/` directory contains:
- `gui/` - GUI icons, images, stylesheets
- `html/` - HTML templates, CSS, JavaScript, fonts
- `pdf/` - DOCX report templates
- `user_settings/` - Default configuration
- `images/` - Application icons
- Excel templates (`.xlsm`, `.xlsx`, `.xltx`)

### Potential Issues

1. **Missing Dependencies**: PyInstaller might miss some dynamic imports (especially Plotly submodules)
   - **Solution**: Use `--collect-submodules plotly` in command line OR use the `ACSAHE.spec` file which includes `collect_submodules('plotly')`
   - The spec file approach is recommended as it's already configured correctly
   - Common error: `ModuleNotFoundError: No module named 'plotly.graph_objs._figure'` - fixed by collecting Plotly submodules

2. **Large File Size**: The executable can be large due to:
   - NumPy/SciPy libraries
   - Plotly with all submodules
   - PyQt5 framework
   - All build assets
   - Solution: UPX compression is enabled, but size will still be significant

3. **Antivirus False Positives**: Some antivirus software flags PyInstaller executables
   - Solution: Code signing (not currently implemented, but `codesign_identity` is available in spec)

4. **Excel Integration**: `xlwings` requires Excel to be installed on the target machine
   - This is a runtime dependency, not bundled

---

## Current Version Information

- **App Version**: 2.0.0-alpha
- **Version Info**: 2.0.0.0
- **Publisher**: Facundo Leguizamón Pfeffer & Oscar Möller
- **Website**: https://facundo-pfeffer.github.io/ACSAHE.github.io/

---

## Recommendations

1. **Automate Build Process**: Create a batch script or PowerShell script to automate both stages
2. **Version Management**: Update version numbers in both `installer_sctipt.iss` and potentially in code
3. **Testing**: Test the installer on clean Windows VMs before release
4. **Code Signing**: Consider code signing for better antivirus compatibility
5. **CI/CD Integration**: Consider adding a GitHub Actions workflow for automated builds on releases

---

## Build Script Example

Create `build_release.bat`:

```batch
@echo off
echo Building ACSAHE Release...

echo Step 1: Building executable...
pyinstaller ACSAHE.spec
if errorlevel 1 (
    echo Build failed!
    pause
    exit /b 1
)

echo Step 2: Building installer...
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer_sctipt.iss
if errorlevel 1 (
    echo Installer build failed!
    pause
    exit /b 1
)

echo Build complete! Installer: dist_installer\Instalador_ACSAHE.exe
pause
```

