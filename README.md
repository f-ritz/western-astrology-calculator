# Western Astrology Calculator

A desktop GUI (and CLI) tool that calculates a full Western (tropical) natal chart using accurate geolocation + timezone data and the excellent [Kerykeion](https://github.com/g-battaglia/kerykeion) library.

**Key features**
- Accurate natal chart for any birth date/time/place (offline ephemeris after first setup)
- Handles "unknown birth time" (defaults to noon with big warning — house/angle accuracy suffers)
- Produces three artifacts every time:
  - `_report.txt` — plain text summary
  - `_report.html` — nicely formatted report you can open/print/share
  - `_natal.svg` — the actual round birth chart wheel graphic (SVG = scalable, open in any browser or vector editor)
- **All output files are written to your Desktop** for instant access (no hunting in CWD or next to the EXE)
- Cross-platform source + buildable standalone apps for Windows, macOS, and Linux

## Run from source (recommended for Mac + Linux, also works on Windows)

```bash
# 1. Clone
git clone https://github.com/yourname/western-astrology-calculator.git
cd western-astrology-calculator

# 2. Create a venv (strongly recommended)
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate

# 3. Install deps
pip install -r requirements.txt

# 4. Launch the GUI
python astrology_gui_fixed.py

# Or the simple CLI
python astrology_calculator.py
```

## Build standalone apps (no Python needed on end-user machine)

You must run the build **on the OS you want to target** (PyInstaller does not cross-compile GUI binaries well).

```bash
pip install -r requirements.txt
pip install pyinstaller
python build_exe.py
```

- Windows → `dist/Western_Astrology_Calculator.exe` (double-clickable)
- macOS   → `dist/Western_Astrology_Calculator.app` (or a single binary)
- Linux   → `dist/Western_Astrology_Calculator` (chmod +x and run)

You can also use the platform spec directly:

```bash
pyinstaller astrology.spec
```

**Note on icons**: Only `icon.ico` is currently in the repo. For best macOS results create an `icon.icns` and update the build command / spec.

## Where the files go

After you click "Generate Natal Chart" (or run the CLI), look on your **Desktop**:

```
YourName_1990-05-15_report.txt
YourName_1990-05-15_report.html     ← easiest to read
YourName_1990-05-15_natal.svg       ← the birth chart wheel
```

A message in the app also tells you the exact path.

If birth time was left blank/unknown, the files get a `_noon_time` suffix and a prominent warning is included in all outputs.

## Notes / Limitations

- The SVG wheel generation can be CPU intensive the first time; subsequent runs are usually fast.
- For highest house accuracy you really do need the exact birth time (minutes matter for the Ascendant).
- Location uses Nominatim (OpenStreetMap). If it fails it silently falls back to Lincoln, Nebraska.
- This is Western tropical astrology only (no sidereal, no Chinese, no numerology).

## Project layout (main files)

- `astrology_gui_fixed.py` — the current GUI (this one is packaged)
- `astrology_calculator.py` — simple terminal version
- `build_exe.py` — cross-platform PyInstaller driver (Windows / macOS / Linux)
- `astrology.spec` — advanced PyInstaller spec (collects kerykeion + swisseph data)
- `requirements.txt` — runtime deps
- `build.bat` — convenience builder for Windows (optional)

## License

See LICENSE.
