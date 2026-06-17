# Western Astrology Calculator v2.0 Release Notes

**Major release** — complete overhaul of the reporting system, GUI modernization, and introduction of a customizable interpretive engine.

## Highlights

- **New primary deliverable: Rich PDF reports**
  - Professional multi-section PDF with birth details, summary tables (full sign names, proper headers for positions/aspects/houses shown cleanly as "House X"), visual pie charts, detailed planet-by-planet + aspect analysis, Ascendant/Midheaven interpretations, and the actual birth chart image on its **own dedicated final page**.
  - Separate high-quality **SVG** vector chart wheel always generated alongside the PDF (best for printing/sharing the graphic).
  - All files saved directly to the user's **Desktop** for easy access.
- **Visual pie charts** (no more plain text percentages):
  - Elements: Fire (red/orange), Air (light gray), Water (mid blue), Earth (nice green).
  - Qualities: Cardinal (red), Fixed (green), Mutable (nice blue).
  - Centered in the report with left-aligned keys/legends (no more overlap).
- **Deep interpretive content** (planet-by-planet flow as requested):
  - For each planet: sign placement (full name), house (clean "House X"), degree, retrograde status + note, sign interpretation, house interpretation, and every aspect involving that planet with its interpretation.
  - Includes Ascendant (Rising) and Midheaven interpretations.
  - All powered by an **easy-to-edit central database** (`interpretations.py`).
- **Customizable for astrologers**:
  - `interpretations.py` contains all planet sign/house, aspect (general + extensible), Ascendant, Midheaven, and retrograde interpretations.
  - Starter content based on Cafe Astrology public material.
  - Add/replace with your own research — no other code changes required. Clear comments mark customization points (no "customize" text leaks into the final report).
- **GUI modernization**:
  - Switched from customtkinter to standard `tkinter.ttk` + `sv-ttk` (Sun Valley/Windows 11 theme) for a true native Windows desktop app feel.
  - Cleaner fonts (Segoe UI), proper controls, less "custom library" aesthetic.
- **Other polish**:
  - Full sign names everywhere (no more 3-letter abbreviations like "Tau").
  - Clean house references ("House 9", not "House Ninth_House").
  - Tables in preview and PDF now have proper headers.
  - Chart wheel image moved to end of PDF on its own page (with caption).
  - Unknown birth time warnings preserved and prominent.
  - Legacy TXT/HTML support de-emphasized (still present for compatibility via old buttons; PDF is the focus).
  - Continued robust SVG generation and Desktop output.

## What's Changed / Breaking

- Primary outputs are now **PDF + SVG** (instead of TXT + HTML + SVG). The rich formatted report with interpretations and visuals is the PDF.
- Old `customtkinter` dependency removed from the main GUI (replaced for native look). `sv-ttk` and `reportlab` added (cairosvg remains optional for PNG chart embedding in PDF and can be omitted for EXE builds).
- CLI (`astrology_calculator.py`) still produces text/HTML for simple use but is secondary to the GUI's PDF workflow.
- Some build artifacts and duplicate specs cleaned from the repo.

## Requirements / Build

- `pip install -r requirements.txt` (includes reportlab for PDFs, sv-ttk for GUI).
- Rebuild EXE with `python build_exe.py` (or `build.bat`) on Windows after installing deps.
- `cairosvg` is optional — the app/PDF works without it (you'll get a note + the excellent separate SVG instead of an embedded raster).

## Limitations (unchanged)

- Best results require accurate birth time for houses/angles.
- Western tropical only.
- Geolocation falls back silently if needed.

## Upgrade Notes

- Delete old build/dist folders before rebuilding.
- Existing users: the new PDF workflow replaces the old HTML/TXT experience. Open the PDF for the full modern report.
- Customize interpretations by editing `interpretations.py` directly.

Thanks for the feedback that shaped v2.0 — pie charts, the detailed breakdown flow, editable DB, native GUI, and clean report formatting were all driven by user input. Enjoy the new reports!

— The project
