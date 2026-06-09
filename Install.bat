@echo off
:: BatchGotAdmin
:-------------------------------------
REM  --> Check for permissions
>nul 2>&1 "%SYSTEMROOT%\system32\cacls.exe" "%SYSTEMROOT%\system32\config\system"

REM --> If error flag set, we do not have admin.
if '%errorlevel%' NEQ '0' (
    echo Requesting administrative privileges to install to Program Files...
    goto UACPrompt
) else ( goto gotAdmin )

:UACPrompt
    echo Set UAC = CreateObject^("Shell.Application"^) > "%temp%\getadmin.vbs"
    echo UAC.ShellExecute "%~s0", "", "", "runas", 1 >> "%temp%\getadmin.vbs"
    "%temp%\getadmin.vbs"
    exit /B

:gotAdmin
    if exist "%temp%\getadmin.vbs" ( del "%temp%\getadmin.vbs" )
    pushd "%CD%"
    CD /D "%~dp0"
:--------------------------------------

echo ====================================================
echo    Installing Controlled Print System...
echo ====================================================

set "DEST_DIR=C:\Program Files\Controlled Print System"
mkdir "%DEST_DIR%" 2>nul

echo Copying files to %DEST_DIR% ...
xcopy "dist\Controlled Print System" "%DEST_DIR%" /E /I /H /Y /F >nul

echo Granting Write Permissions to database and folders...
icacls "%DEST_DIR%" /grant Users:(OI)(CI)F /T >nul 2>&1

echo Creating Desktop Shortcut...
set "SHORTCUT_PATH=%USERPROFILE%\Desktop\Controlled Print System.lnk"
if exist "%SHORTCUT_PATH%" del "%SHORTCUT_PATH%"
powershell -Command "$wshell = New-Object -ComObject WScript.Shell; $shortcut = $wshell.CreateShortcut('%SHORTCUT_PATH%'); $shortcut.TargetPath = '%DEST_DIR%\Controlled Print System.exe'; $shortcut.WorkingDirectory = '%DEST_DIR%'; $shortcut.IconLocation = '%DEST_DIR%\app_icon.ico'; $shortcut.Save()"

echo Creating Start Menu Shortcut...
set "START_MENU_PATH=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Controlled Print System.lnk"
if exist "%START_MENU_PATH%" del "%START_MENU_PATH%"
powershell -Command "$wshell = New-Object -ComObject WScript.Shell; $shortcut = $wshell.CreateShortcut('%START_MENU_PATH%'); $shortcut.TargetPath = '%DEST_DIR%\Controlled Print System.exe'; $shortcut.WorkingDirectory = '%DEST_DIR%'; $shortcut.IconLocation = '%DEST_DIR%\app_icon.ico'; $shortcut.Save()"

echo Refreshing Windows Icon Cache...
ie4uinit.exe -show

echo ====================================================
echo    Installation Complete!
echo    You can now open the app from your Desktop.
echo ====================================================
pause
