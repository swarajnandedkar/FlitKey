#ifndef MyAppVersion
  #define MyAppVersion "0.3.0"
#endif

#define MyAppName "TypeFlux"
#define MyAppPublisher "TypeFlux contributors"
#define MyAppExeName "TypeFlux.exe"

[Setup]
AppId={{9B0E7E77-2D82-4D3A-9D0A-3EE3D1D2C3F1}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\TypeFlux
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
OutputDir=..\dist\windows
OutputBaseFilename=TypeFlux-Setup-{#MyAppVersion}-x64
SetupIconFile=..\build\windows\typeflux.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Files]
Source: "..\build\windows\dist\TypeFlux\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch TypeFlux"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"
