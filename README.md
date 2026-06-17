# Western Astrology Calculator

A desktop GUI (and CLI) tool that calculates a full Western (tropical) natal chart using accurate geolocation + timezone data and the excellent [Kerykeion](https://github.com/g-battaglia/kerykeion) library.

## Key Features (v2.0)

- Accurate natal chart for any birth date/time/place (offline ephemeris after first setup)
- Handles "unknown birth time" (defaults to noon with big warning — house/angle accuracy suffers)
- **Primary output: Professional PDF report** including:
  - Birth details
  - Summary tables with proper headers (planetary positions with full sign names, aspects, houses displayed cleanly as "House X")
  - **Visual pie charts** for Elemental proportions (Fire: red/orange, Air: light gray, Water: mid blue, Earth: nice green) and Quality/Modality proportions (Cardinal: red, Fixed: green, Mutable: nice blue) — centered with left-aligned keys
  - Detailed interpretive breakdown: planet-by-planet (sign + house + retrograde notes + aspects) using editable interpretations
  - Ascendant (Rising) and Midheaven interpretations
  - The actual birth chart wheel image on its **own dedicated page at the end**
- Separate high-quality **SVG** of the natal chart wheel always saved (vector, scalable, open in browser or editor)
- **All output files written to your Desktop** for instant access
- Modern native Windows GUI appearance (uses `ttk` + `sv-ttk` Sun Valley theme — no more heavy customtkinter styling)
- Fully **editable interpretations database** in `interpretations.py` (planet sign/house placements, aspects, Ascendant, Midheaven, retrograde notes) — sourced from Cafe Astrology with placeholders for your own research as an astrologer
- CLI available for simple text-based use
- Cross-platform source + easy Windows EXE builds

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

## Build standalone Windows app (no Python needed on end-user machine)

You must run the build **on Windows** (PyInstaller does not cross-compile GUI binaries well).

```powershell
pip install -r requirements.txt
pip install pyinstaller
python build_exe.py
```

- Produces `Western_Astrology_Calculator.exe` in the `dist` folder (single-file by default)

You can also use the spec directly:

```powershell
pyinstaller astrology.spec
```

**Note on icons**: Only `icon.ico` is currently in the repo.

## Where the files go

After you click "Generate Natal Chart", look on your **Desktop**:

```
YourName_1990-05-15_natal_report.pdf   ← Main formatted report (tables, pie charts, detailed interps, chart image on last page)
YourName_1990-05-15_natal.svg          ← High-quality vector birth chart wheel
```

A message in the app tells you the exact path.

If birth time was left blank/unknown, files get a `_noon_time` suffix and prominent warnings.

Legacy TXT/HTML buttons may appear for compatibility but are no longer primary.

## Notes / Limitations

- The SVG wheel generation can be CPU intensive the first time; subsequent runs are usually fast.
- For highest house accuracy you really do need the exact birth time (minutes matter for the Ascendant).
- Location uses Nominatim (OpenStreetMap). If it fails it silently falls back to Lincoln, Nebraska.
- This is Western tropical astrology only (no sidereal, no Chinese, no numerology).
- `cairosvg` (for embedding a PNG version of the chart in the PDF) is optional — the app and PDF work fully without it (SVG is always available separately). It can be tricky to bundle into EXEs.
- Interpretations are a starter set based on Cafe Astrology (public material). Edit `interpretations.py` freely for your own research.

## Project layout (main files)

- `astrology_gui_fixed.py` — the current GUI (packaged). Uses standard `ttk` + `sv-ttk` for native Windows appearance.
- `astrology_calculator.py` — simple terminal/CLI version
- `interpretations.py` — **editable database** for all planet sign/house, aspect, Ascendant, Midheaven, and retrograde interpretations
- `build_exe.py` — PyInstaller driver (Windows-focused)
- `astrology.spec` — advanced PyInstaller spec (collects kerykeion + pyswisseph data)
- `requirements.txt` — runtime deps (reportlab for PDF, sv-ttk for GUI, etc.)
- `build.bat` — convenience builder for Windows (optional)
- `icon.ico` — app icon

## License

See LICENSE.

For entertainment/educational purposes. Interpretation of astrological data is the responsibility of the practitioner.
