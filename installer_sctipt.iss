[Setup]
AppName=ACSAHE
AppVersion=2.0.0-alpha
DefaultDirName={pf}\ACSAHE
DefaultGroupName=ACSAHE
OutputBaseFilename=Instalador_ACSAHE
OutputDir=dist_installer
Compression=lzma
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64


AppPublisher=Facundo Leguizamón Pfeffer & Oscar Möller
AppPublisherURL=https://facundo-pfeffer.github.io/ACSAHE.github.io/
VersionInfoCompany=Facundo Leguizamón Pfeffer
VersionInfoDescription=Software de automatización del cálculo de la resistencia de secciones arbitrarias de hormigón estructural según CIRSOC 201-2005 y 201-2024
VersionInfoVersion=2.0.0.0
VersionInfoTextVersion=2.0.0-alpha
UninstallDisplayIcon={app}\ACSAHE.exe


SetupIconFile=build\gui\images\COMPLETE-LOGO-NO-TEXT-transparent-bg.ico
WizardStyle=modern
WizardImageFile=build\gui\images\ACSAHE Logo.bmp
WizardSmallImageFile=build\gui\images\Logo_H.bmp

[Files]
Source: "dist\ACSAHE.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "build\*"; DestDir: "{app}\build"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\ACSAHE"; Filename: "{app}\ACSAHE.exe"; IconFilename: "{app}\ACSAHE.exe"
Name: "{commondesktop}\ACSAHE"; Filename: "{app}\ACSAHE.exe"; Tasks: desktopicon; IconFilename: "{app}\ACSAHE.exe"


[Tasks]
Name: "desktopicon"; Description: "Crear un acceso directo en el &escritorio"; GroupDescription: "Accesos directos adicionales:"

[Run]
Filename: "{app}\ACSAHE.exe"; Description: "Lanzar ACSAHE"; Flags: nowait postinstall skipifsilent

[Messages]
WelcomeLabel1=¡Bienvenido al asistente de instalación de ACSAHE!
WelcomeLabel2=Este asistente instalará ACSAHE en su computadora.
FinishedLabel=La instalación de ACSAHE ha finalizado con éxito.

