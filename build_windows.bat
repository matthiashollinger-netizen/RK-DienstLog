@echo off
setlocal enabledelayedexpansion

for /f "delims=" %%i in ('python -c "import json; print(json.load(open('version.json', encoding='utf-8'))['version'])"') do set VERSION=%%i

echo ========================================
echo Baue RK DienstLog Version %VERSION% fuer Windows
echo ========================================

if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist "RK DienstLog.spec" del "RK DienstLog.spec"

pyinstaller --onefile --windowed ^
--name "RK DienstLog" ^
--icon="%cd%\rk_dienstlog_windows_fixed.ico" ^
--add-data "rk_dienstlog_icon.png;." ^
--add-data "rk_dienstlog_windows_fixed.ico;." ^
--add-data "version.json;." ^
rk_dienstlog.py

if errorlevel 1 (
    echo PyInstaller Build fehlgeschlagen.
    pause
    exit /b 1
)

echo.
echo Baue Installer mit Inno Setup...

if not exist dist_installer mkdir dist_installer

REM Inno Setup Script wird dynamisch mit Version erzeugt
(
echo #define MyAppName "RK DienstLog"
echo #define MyAppVersion "%VERSION%"
echo #define MyAppPublisher "Matthias Hollinger"
echo #define MyAppExeName "RK DienstLog.exe"
echo.
echo [Setup]
echo AppId={{A8B8F980-2F5E-4F35-BB96-524B4453544C}}
echo AppName={#MyAppName}
echo AppVersion={#MyAppVersion}
echo AppPublisher={#MyAppPublisher}
echo DefaultDirName={autopf}\{#MyAppName}
echo DefaultGroupName={#MyAppName}
echo OutputDir=..\dist_installer
echo OutputBaseFilename=RK_DienstLog_Setup_{#MyAppVersion}
echo SetupIconFile=..\rk_dienstlog_windows_fixed.ico
echo Compression=lzma
echo SolidCompression=yes
echo WizardStyle=modern
echo UninstallDisplayIcon={app}\{#MyAppExeName}
echo ArchitecturesInstallIn64BitMode=x64compatible
echo.
echo [Languages]
echo Name: "german"; MessagesFile: "compiler:Languages\German.isl"
echo.
echo [Tasks]
echo Name: "desktopicon"; Description: "Desktop-Verknuepfung erstellen"; GroupDescription: "Zusaetzliche Aufgaben:"; Flags: unchecked
echo.
echo [Files]
echo Source: "..\dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
echo.
echo [Icons]
echo Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
echo Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
echo.
echo [Run]
echo Filename: "{app}\{#MyAppExeName}"; Description: "{#MyAppName} starten"; Flags: nowait postinstall skipifsilent
) > installer\rk_dienstlog_setup.iss

iscc installer\rk_dienstlog_setup.iss

if errorlevel 1 (
    echo Installer Build fehlgeschlagen.
    pause
    exit /b 1
)

echo.
echo Fertig:
echo EXE: dist\RK DienstLog.exe
echo Installer: dist_installer\RK_DienstLog_Setup_%VERSION%.exe
pause
