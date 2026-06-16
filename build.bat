@echo off
REM Western Astrology Calculator - Windows EXE Builder (double-click to run)
REM For macOS / Linux use:  python build_exe.py   (after pip install -r requirements.txt)

title Building Western Astrology Calculator...
echo.
echo ====================================================================
echo          Western Astrology Calculator - Windows EXE Builder
echo ====================================================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Download from https://www.python.org/ and check "Add Python to PATH"
    pause
    exit /b 1
)

echo [1/3] Installing / updating build dependencies...
pip install pyinstaller customtkinter geopy timezonefinder kerykeion --quiet

echo [2/3] Building (onefile, windowed)...
echo.

if exist "icon.ico" (
    pyinstaller --onefile --windowed --name "Western_Astrology_Calculator" --icon icon.ico --add-data "icon.ico:." astrology_gui_fixed.py
) else (
    pyinstaller --onefile --windowed --name "Western_Astrology_Calculator" astrology_gui_fixed.py
)

echo.
echo [3/3] Verifying...
if exist "dist\Western_Astrology_Calculator.exe" (
    echo.
    echo ====================================================================
    echo                      BUILD SUCCESSFUL!
    echo ====================================================================
    echo.
    echo Your Windows EXE is ready: dist\Western_Astrology_Calculator.exe
    echo.
    echo IMPORTANT: Generated chart files (HTML + TXT + SVG) are now saved
    echo to the user's Desktop for easy access, not next to the EXE.
    echo.
    pause
) else (
    echo.
    echo Build may have failed or produced a folder (onedir). Check dist\
    pause
    exit /b 1
)
