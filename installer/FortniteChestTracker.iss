#define AppName "Fortnite Chest Tracker"
#define AppVersion GetEnv("APP_VERSION")
#if AppVersion == ""
  #define AppVersion "0.1.0"
#endif

[Setup]
AppId={{6D1F2B7A-3C5E-4B8A-9E41-FC7A0C1E5D21}
AppName={#AppName}
AppVersion={#AppVersion}
DefaultDirName={autopf}\FortniteChestTracker
DefaultGroupName={#AppName}
OutputDir=..\dist
OutputBaseFilename=FortniteChestTracker-Setup
SetupIconFile=..\assets\icon.ico
UninstallDisplayIcon={app}\FortniteChestTracker.exe
Compression=lzma2
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=admin
WizardStyle=modern

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"

[Tasks]
Name: "desktopicon"; Description: "Créer un raccourci sur le Bureau"; Flags: checkedonce
Name: "autostart"; Description: "Lancer avec Windows"; Flags: unchecked

[Files]
Source: "..\dist\FortniteChestTracker.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\FortniteChestTracker.exe"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\FortniteChestTracker.exe"; Tasks: desktopicon

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueName: "FortniteChestTracker"; ValueType: string; ValueData: """{app}\FortniteChestTracker.exe"" --minimized"; Tasks: autostart; Flags: uninsdeletevalue

[Run]
Filename: "{app}\FortniteChestTracker.exe"; Description: "Lancer {#AppName}"; Flags: nowait postinstall skipifsilent
