@echo off
REM Strands Chat Loop - Windows Installation Script
REM
REM This script installs the chat loop globally so you can run:
REM   chat_loop <agent_path>
REM from anywhere in your terminal.
REM
REM Usage:
REM   install.bat          - Install for current user
REM   install.bat /uninstall - Remove installation

setlocal enabledelayedexpansion

REM Colors don't work well in cmd, but work in PowerShell/Windows Terminal
set "GREEN=[92m"
set "YELLOW=[93m"
set "RED=[91m"
set "BLUE=[94m"
set "NC=[0m"

REM Installation paths
set "INSTALL_DIR=%USERPROFILE%\.local\bin"
set "WRAPPER_NAME=chat_loop.bat"
set "WRAPPER_PATH=%INSTALL_DIR%\%WRAPPER_NAME%"
set "PYTHON_WRAPPER=%INSTALL_DIR%\chat_loop.py"

REM Get the directory where this script lives
set "SCRIPT_DIR=%~dp0"
set "CHAT_LOOP_PY=%SCRIPT_DIR%chat_loop.py"

REM Parse arguments
if "%1"=="/?" goto :show_help
if "%1"=="/help" goto :show_help
if "%1"=="/uninstall" goto :uninstall
if "%1"=="" goto :install
echo %RED%Error: Unknown option '%1'%NC%
goto :show_help

:show_help
echo.
echo Strands Chat Loop - Windows Installation Script
echo.
echo Usage:
echo   install.bat              Install chat loop command globally
echo   install.bat /uninstall   Remove chat loop command
echo   install.bat /help        Show this help message
echo.
echo This will:
echo   1. Install Python dependencies to your system
echo   2. Create a 'chat_loop' command in %%USERPROFILE%%\.local\bin
echo   3. Add the directory to your PATH
echo.
echo After installation, run:
echo   chat_loop path\to\agent.py
echo.
goto :eof

:check_python
echo %BLUE%Checking Python installation...%NC%
python --version >nul 2>&1
if errorlevel 1 (
    echo %RED%Error: Python is not installed or not in PATH%NC%
    echo Please install Python 3.8 or higher from python.org
    exit /b 1
)
for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PYTHON_VERSION=%%v
echo %GREEN%Found Python %PYTHON_VERSION%%NC%
goto :eof

:install_dependencies
echo.
echo %BLUE%Installing Python dependencies...%NC%
if not exist "%SCRIPT_DIR%requirements.txt" (
    echo %YELLOW%Warning: requirements.txt not found%NC%
    goto :eof
)

echo.
echo Where would you like to install dependencies?
echo   1^) User install ^(recommended^) - pip install --user
echo   2^) System install - pip install
echo   3^) Skip - dependencies already installed
set /p "install_choice=Choice [1]: "
if "%install_choice%"=="" set install_choice=1

if "%install_choice%"=="1" (
    python -m pip install --user -r "%SCRIPT_DIR%requirements.txt"
    if errorlevel 1 (
        echo %RED%Failed to install dependencies%NC%
        exit /b 1
    )
    echo %GREEN%Dependencies installed to user site-packages%NC%
) else if "%install_choice%"=="2" (
    python -m pip install -r "%SCRIPT_DIR%requirements.txt"
    if errorlevel 1 (
        echo %RED%Failed to install dependencies%NC%
        exit /b 1
    )
    echo %GREEN%Dependencies installed system-wide%NC%
) else if "%install_choice%"=="3" (
    echo %BLUE%Skipping dependency installation%NC%
) else (
    echo %RED%Invalid choice%NC%
    exit /b 1
)
goto :eof

:create_wrapper
echo.
echo %BLUE%Creating chat_loop wrapper script...%NC%

REM Create the install directory
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

REM Create the Python wrapper with actual script directory path
echo import sys > "%PYTHON_WRAPPER%"
echo import os >> "%PYTHON_WRAPPER%"
echo from pathlib import Path >> "%PYTHON_WRAPPER%"
echo. >> "%PYTHON_WRAPPER%"
echo # Get the actual chat_loop.py location (set during installation) >> "%PYTHON_WRAPPER%"
echo SCRIPT_DIR = Path(r"%SCRIPT_DIR%") >> "%PYTHON_WRAPPER%"
echo CHAT_LOOP_PY = SCRIPT_DIR / "chat_loop.py" >> "%PYTHON_WRAPPER%"
echo. >> "%PYTHON_WRAPPER%"
echo if not CHAT_LOOP_PY.exists(): >> "%PYTHON_WRAPPER%"
echo     print(f"Error: Could not find chat_loop.py at {CHAT_LOOP_PY}", file=sys.stderr) >> "%PYTHON_WRAPPER%"
echo     sys.exit(1) >> "%PYTHON_WRAPPER%"
echo. >> "%PYTHON_WRAPPER%"
echo sys.path.insert(0, str(SCRIPT_DIR)) >> "%PYTHON_WRAPPER%"
echo. >> "%PYTHON_WRAPPER%"
echo try: >> "%PYTHON_WRAPPER%"
echo     from chat_loop import main >> "%PYTHON_WRAPPER%"
echo     sys.exit(main()) >> "%PYTHON_WRAPPER%"
echo except Exception as e: >> "%PYTHON_WRAPPER%"
echo     print(f"Error: {e}", file=sys.stderr) >> "%PYTHON_WRAPPER%"
echo     sys.exit(1) >> "%PYTHON_WRAPPER%"

REM Create the batch wrapper
echo @echo off > "%WRAPPER_PATH%"
echo python "%%~dp0chat_loop.py" %%* >> "%WRAPPER_PATH%"

echo %GREEN%Wrapper created at %WRAPPER_PATH%%NC%
goto :eof

:update_path
echo.
echo %BLUE%Updating PATH...%NC%

REM Check if already in PATH
echo %PATH% | findstr /C:"%INSTALL_DIR%" >nul
if not errorlevel 1 (
    echo %GREEN%Install directory already in PATH%NC%
    goto :eof
)

REM Add to user PATH
setx PATH "%PATH%;%INSTALL_DIR%" >nul 2>&1
if errorlevel 1 (
    echo %YELLOW%Warning: Could not automatically update PATH%NC%
    echo Please add manually:
    echo   %INSTALL_DIR%
    echo.
    echo Instructions:
    echo 1. Open System Properties ^(Win+Pause^)
    echo 2. Click "Advanced system settings"
    echo 3. Click "Environment Variables"
    echo 4. Under "User variables", edit PATH
    echo 5. Add: %INSTALL_DIR%
) else (
    echo %GREEN%PATH updated successfully%NC%
    echo %YELLOW%Note: Restart your terminal for changes to take effect%NC%
)
goto :eof

:uninstall
echo.
echo %BLUE%Uninstalling chat_loop...%NC%

if exist "%WRAPPER_PATH%" (
    del "%WRAPPER_PATH%"
    echo %GREEN%Removed %WRAPPER_PATH%%NC%
) else (
    echo %BLUE%Wrapper not found%NC%
)

if exist "%PYTHON_WRAPPER%" (
    del "%PYTHON_WRAPPER%"
    echo %GREEN%Removed %PYTHON_WRAPPER%%NC%
)

echo.
echo %BLUE%Uninstallation complete%NC%
echo.
echo Note: Python dependencies and PATH modifications were not removed.
echo To remove dependencies:
echo   pip uninstall anthropic-bedrock pyyaml rich
goto :eof

:install
echo.
echo ╔═══════════════════════════════════════════════╗
echo ║   Strands Chat Loop - Installation Script    ║
echo ╚═══════════════════════════════════════════════╝
echo.

call :check_python
if errorlevel 1 exit /b 1

call :install_dependencies
if errorlevel 1 exit /b 1

call :create_wrapper
if errorlevel 1 exit /b 1

call :update_path

echo.
echo ╔═══════════════════════════════════════════════╗
echo ║            Installation Complete!             ║
echo ╚═══════════════════════════════════════════════╝
echo.
echo %GREEN%Chat loop installed successfully!%NC%
echo.
echo Usage:
echo   chat_loop path\to\agent.py
echo   chat_loop path\to\agent.py --config ~/.chatrc-custom
echo.
echo Example:
echo   chat_loop AWS_Strands\Product_Pete\agent.py
echo.
echo %YELLOW%Important: Restart your terminal or command prompt%NC%
echo %YELLOW%to start using the chat_loop command%NC%
echo.

goto :eof
