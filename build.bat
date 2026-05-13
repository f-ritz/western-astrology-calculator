@echo off
REM Western Astrology Calculator - One-Click EXE Builder for Windows
REM Just double-click this file to build the EXE!

title Building Western Astrology Calculator...
echo.
echo ====================================================================
echo          Western Astrology Calculator - EXE Builder
echo ====================================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python from https://www.python.org/
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

echo [1/4] Checking dependencies...
python -c "import pyinstaller" >nul 2>&1
if errorlevel 1 (
    echo [!] PyInstaller not found, installing...
    pip install pyinstaller >nul 2>&1
)

python -c "import customtkinter" >nul 2>&1
if errorlevel 1 (
    echo [!] customtkinter not found, installing...
    pip install customtkinter >nul 2>&1
)

echo [2/4] Checking source files...
if not exist "astrology_gui_fixed.py" (
    echo ERROR: astrology_gui_fixed.py not found!
    pause
    exit /b 1
)

echo [3/4] Building EXE... (this may take 2-5 minutes)
echo.

if exist "icon.ico" (
    pyinstaller --onefile --windowed --name "Western_Astrology_Calculator" --icon icon.ico astrology_gui_fixed.py
) else (
    pyinstaller --onefile --windowed --name "Western_Astrology_Calculator" astrology_gui_fixed.py
)

echo.
echo [4/4] Checking output...
if exist "dist\Western_Astrology_Calculator.exe" (
    echo.
    echo ====================================================================
    echo                      BUILD SUCCESSFUL!
    echo ====================================================================
    echo.
    echo Your EXE is ready: dist\Western_Astrology_Calculator.exe
    echo.
    echo You can now:
    echo   - Double-click the EXE to run your app
    echo   - Copy it to other computers (Windows 10/11)
    echo   - Share it with friends
    echo.
    pause
) else (
    echo.
    echo ERROR: Build failed! Check the output above for details.
    pause
    exit /b 1
)
