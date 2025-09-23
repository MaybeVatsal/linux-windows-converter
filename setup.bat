@echo off
setlocal enabledelayedexpansion

echo ========================================
echo  Linux Command Wrapper Setup
echo ========================================
echo.

:menu
echo Select an option:
echo 1. Install/Compile
echo 2. Uninstall/Clean
echo 3. Exit
echo.
set /p choice="Enter your choice (1-3): "

if "%choice%"=="1" goto install
if "%choice%"=="2" goto uninstall
if "%choice%"=="3" goto exit
echo Invalid choice. Please try again.
echo.
goto menu

:install
echo.
echo Starting installation process...
echo.

:: Check if main.py exists
if not exist "main.py" (
    echo ERROR: main.py not found in current directory
    echo Please make sure main.py is in the same directory as this setup.bat
    pause
    exit /b 1
)

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python from https://python.org
    pause
    exit /b 1
)

:: Get Python version
for /f "tokens=*" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Found !PYTHON_VERSION!

:: Check if pyinstaller is installed
echo Checking for PyInstaller...
python -c "import pyinstaller" 2>nul
if errorlevel 1 (
    echo Installing PyInstaller...
    pip install pyinstaller
    if errorlevel 1 (
        echo ERROR: Failed to install PyInstaller
        pause
        exit /b 1
    )
) else (
    echo PyInstaller is already installed
)

:: Clean previous builds if they exist
if exist "build" (
    echo Cleaning previous build files...
    rmdir /s /q build
)
if exist "dist" (
    echo Cleaning previous dist files...
    rmdir /s /q dist
)
if exist "cmd-linux.spec" (
    echo Removing previous spec file...
    del /q cmd-linux.spec
)

:: Compile the Python script to executable
echo Compiling main.py to executable...
pyinstaller --onefile --name cmd-linux main.py

if errorlevel 1 (
    echo ERROR: Failed to compile the executable
    pause
    exit /b 1
)

echo.
echo Compilation successful!

:: Create cmd-linux.bat wrapper in dist folder
echo Creating wrapper script...
echo @echo off > "dist\cmd-linux.bat"
echo "%~dp0cmd-linux.exe" %%* >> "dist\cmd-linux.bat"

:: Add to PATH permanently
echo Adding to system PATH...
set "EXE_PATH=%~dp0dist"

:: Check if already in PATH
echo %PATH% | find /i "%EXE_PATH%" >nul
if errorlevel 1 (
    :: Add to user PATH
    setx PATH "%%PATH%%;%EXE_PATH%" >nul
    if errorlevel 1 (
        echo Warning: Could not update PATH permanently. You may need to run as Administrator.
        echo Temporary solution: Manually add this folder to your PATH: %EXE_PATH%
    ) else (
        echo Added to user PATH successfully.
    )
) else (
    echo Already in PATH.
)

:: Create a test batch file in Windows directory for easy access
set "WIN_DIR=%SystemRoot%\System32"
if exist "%WIN_DIR%" (
    echo Creating global command...
    echo @echo off > "%WIN_DIR%\cmd-linux.bat"
    echo "%~dp0dist\cmd-linux.exe" %%* >> "%WIN_DIR%\cmd-linux.bat"
)

echo.
echo ========================================
echo  Installation Complete!
echo ========================================
echo.
echo You can now use 'cmd-linux' command in any command prompt.
echo.
echo Usage:
echo   cmd-linux          - Start the Linux command wrapper
echo   cmd-linux ls       - Run individual Linux commands
echo   cmd-linux help     - Show help
echo.
echo The executable is located in: %~dp0dist\
echo.
echo Note: You may need to restart your command prompt for the changes to take effect.
echo.

:: Test the installation
echo Testing installation...
if exist "dist\cmd-linux.exe" (
    echo Success: cmd-linux.exe compiled successfully!
    echo.
    echo You can now:
    echo 1. Open a NEW command prompt
    echo 2. Type 'cmd-linux' to start the Linux-like environment
    echo 3. Or type 'cmd-linux help' to see available commands
) else (
    echo Warning: cmd-linux.exe not found in dist folder
)

goto end

:uninstall
echo.
echo Starting uninstall process...
echo.

:: Remove build files
if exist "build" (
    echo Removing build directory...
    rmdir /s /q build
    echo Build directory removed.
) else (
    echo Build directory not found.
)

:: Remove dist files
if exist "dist" (
    echo Removing dist directory...
    rmdir /s /q dist
    echo Dist directory removed.
) else (
    echo Dist directory not found.
)

:: Remove spec file
if exist "cmd-linux.spec" (
    echo Removing spec file...
    del /q cmd-linux.spec
    echo Spec file removed.
) else (
    echo Spec file not found.
)

:: Remove from Windows System32
set "WIN_DIR=%SystemRoot%\System32"
if exist "%WIN_DIR%\cmd-linux.bat" (
    echo Removing global command from System32...
    del /q "%WIN_DIR%\cmd-linux.bat"
    echo Global command removed.
) else (
    echo Global command not found in System32.
)

:: Note about PATH (can't easily remove from PATH automatically)
echo.
echo Note: To complete uninstallation, you may want to:
echo 1. Manually remove the following from your PATH environment variable:
echo    %~dp0dist
echo 2. Restart your command prompt
echo.

echo ========================================
echo  Uninstall Complete!
echo ========================================
goto end

:exit
echo Exiting...
exit /b 0

:end
echo.
pause