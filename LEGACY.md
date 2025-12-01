# Legacy Excel/VBA Integration

## Overview

ACSAHE has two deployment methods:

1. **Modern Version** (Recommended): Standalone Windows application with GUI
   - Entry point: `main.py`
   - Main code: `acsahe.py`
   - Build spec: `ACSAHE.spec`
   - Installation: Windows installer or standalone `.exe`

2. **Legacy Version**: Excel/VBA integration (deprecated but maintained)
   - Entry point: `excel_input_main.py`
   - Legacy code: `legacy/excel_input_acsahe.py`
   - Build spec: `ACSAHE_excel.spec`
   - Usage: Launched from Excel via VBA button

## Legacy System Architecture

### Components

#### Entry Point
- **File**: `excel_input_main.py`
- **Purpose**: Main entry point for the Excel/VBA integration
- **Usage**: Called by Excel VBA with workbook path as argument
- **Arguments**: Receives Excel workbook path via command line (`sys.argv[1]`)

#### Legacy Implementation
- **File**: `legacy/excel_input_acsahe.py`
- **Purpose**: Contains the legacy GUI and processing logic for Excel integration
- **Class**: `ExcelInputACSAHEGUI` / `OldACSAHEGUIWidget`
- **Note**: This is the older implementation that interfaces directly with Excel workbooks

#### Build Configuration
- **File**: `ACSAHE_excel.spec`
- **Purpose**: PyInstaller spec file for building the Excel-integrated executable
- **Output**: `ACSAHE.exe` (same name as modern version, but different build)
- **Note**: Uses `excel_input_main.py` as entry point instead of `main.py`

#### Legacy Excel Utilities
- **File**: `build/utils/excel_manager.py`
- **Legacy Functions**:
  - `insert_uniaxial_result_values()` - Inserts uniaxial interaction diagram results into Excel
  - `insert_biaxial_result_values()` - Inserts biaxial interaction diagram results into Excel
- **Location**: Marked with comment `# LEGACY METHODS - Part of the previous Excel management system.`
- **Status**: These functions are only used by the legacy Excel integration

## Building the Legacy Version

To build the Excel-integrated version:

```bash
pyinstaller ACSAHE_excel.spec
```

This will create `dist/ACSAHE.exe` which can be called from Excel VBA.

## VBA Integration

The legacy version is designed to be called from Excel VBA. Example VBA code:

```vba
Sub RunACSAHE()
    Dim exePath As String
    Dim wbPath As String
    
    exePath = "path\to\ACSAHE.exe"
    wbPath = ThisWorkbook.FullName
    
    Shell exePath & " --wb=" & wbPath, vbNormalFocus
End Sub
```

## Differences from Modern Version

| Feature | Modern Version | Legacy Version |
|---------|---------------|----------------|
| Entry Point | `main.py` | `excel_input_main.py` |
| GUI | Modern PyQt5 GUI | Legacy PyQt5 GUI (simpler) |
| Excel Integration | Uses `input_orchestrators/excel_loader.py` | Direct Excel manipulation via `legacy/excel_input_acsahe.py` |
| Excel Methods | Modern `ExcelSheetManager` class | Legacy `insert_uniaxial_result_values()` and `insert_biaxial_result_values()` |
| Deployment | Windows installer | Standalone `.exe` called from Excel |
| User Experience | Standalone app with file picker | Integrated into Excel workflow |

## Maintenance Status

⚠️ **Status**: The legacy Excel/VBA integration is **maintained but deprecated**.

- ✅ **Maintained**: Bug fixes and compatibility updates will be applied
- ⚠️ **Deprecated**: No new features will be added to the legacy version
- 📝 **Recommendation**: New users should use the modern Windows application version

## Migration Path

If you're currently using the legacy Excel/VBA integration and want to migrate:

1. Install the modern version from the [Releases](https://github.com/Facundo-Pfeffer/ACSAHE/releases) page
2. Use the modern GUI to select your Excel file
3. The modern version uses the same Excel input format, so your existing workbooks should work

## File Structure

```
ACSAHE/
├── main.py                          # Modern entry point
├── excel_input_main.py              # Legacy entry point ⚠️
├── acsahe.py                        # Modern implementation
├── legacy/
│   └── excel_input_acsahe.py       # Legacy implementation ⚠️
├── ACSAHE.spec                      # Modern build spec
├── ACSAHE_excel.spec                # Legacy build spec ⚠️
└── build/utils/
    └── excel_manager.py
        ├── ExcelSheetManager        # Modern Excel utilities
        ├── insert_uniaxial_result_values()  # Legacy method ⚠️
        └── insert_biaxial_result_values()   # Legacy method ⚠️
```

⚠️ = Legacy component

## Support

For issues with the legacy version, please:
1. Check if the issue also exists in the modern version
2. If migrating is not possible, open an issue with `[LEGACY]` prefix
3. Consider migrating to the modern version for better support and features

