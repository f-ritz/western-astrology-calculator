import datetime
import webbrowser
import sys
import os
import threading
import subprocess
from pathlib import Path

import tkinter as tk
from tkinter import ttk, font as tkfont

try:
    import sv_ttk  # Modern Windows 11 (Sun Valley) ttk theme — gives real native Windows controls
    HAS_SVTTK = True
except ImportError:
    HAS_SVTTK = False

from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
from timezonefinder import TimezoneFinder

from kerykeion import AstrologicalSubjectFactory
from kerykeion.chart_data_factory import ChartDataFactory
from kerykeion.charts.chart_drawer import ChartDrawer
from kerykeion import ReportGenerator

# Our custom interpretations database (easy for you to edit as an astrologer)
import interpretations

# PDF generation
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import cairosvg  # for SVG to PNG for embedding the chart wheel in the PDF (graceful fallback if missing)


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def log(message):
    with open("debug.log", "a", encoding="utf-8") as f:
        f.write(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {message}\n")
    print(message)


def get_desktop_path() -> Path:
    """Cross-platform desktop folder with common fallbacks (including Windows OneDrive)."""
    home = Path.home()
    candidates = [home / "Desktop"]

    # Windows: check OneDrive Desktop if present
    if os.name == "nt":
        onedrive = os.environ.get("OneDrive")
        if onedrive:
            candidates.insert(0, Path(onedrive) / "Desktop")
        # Also try OneDriveConsumer in some setups
        onedrive_consumer = os.environ.get("OneDriveConsumer")
        if onedrive_consumer:
            candidates.insert(0, Path(onedrive_consumer) / "Desktop")

    for candidate in candidates:
        if candidate.exists():
            return candidate

    # Last resort: use home (and try to ensure a Desktop subdir exists for future)
    desktop = home / "Desktop"
    try:
        desktop.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    return desktop


class AstrologyGUI(tk.Tk):
    """Native-feeling Windows app using ttk + sv_ttk (Sun Valley / Windows 11 style).
    Much less 'custom tkinter' rounded look, more like a real desktop Windows application.
    """
    def __init__(self):
        super().__init__()
        self.title("Western Astrology Calculator")
        self.geometry("1080x820")
        self.minsize(860, 620)

        # Apply the modern Windows 11 ttk theme (this is the key change for native Windows appearance)
        if HAS_SVTTK:
            try:
                sv_ttk.set_theme("dark")
            except Exception:
                pass
        # If sv_ttk is not installed the app still works with plain ttk (just less polished)

        # Prefer Windows system fonts
        try:
            for fname in ("TkDefaultFont", "TkTextFont"):
                f = tkfont.nametofont(fname)
                f.configure(family="Segoe UI", size=10)
            tkfont.nametofont("TkFixedFont").configure(family="Consolas", size=11)
        except Exception:
            pass

        icon_path = resource_path("icon.ico")
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass

        log("GUI started")

        title_font = tkfont.Font(family="Segoe UI", size=19, weight="bold")
        title = ttk.Label(self, text="Western Astrology Calculator", font=title_font)
        title.pack(pady=(14, 6))

        input_frame = ttk.LabelFrame(self, text=" Birth Data ", padding=(14, 10))
        input_frame.pack(padx=16, pady=(2, 6), fill="x")

        ttk.Label(input_frame, text="Full Name:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.name_entry = ttk.Entry(input_frame, width=40)
        self.name_entry.grid(row=0, column=1, padx=5, pady=5, columnspan=2)

        ttk.Label(input_frame, text="Birthday (YYYY-MM-DD):").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.date_entry = ttk.Entry(input_frame, width=40)
        self.date_entry.grid(row=1, column=1, padx=5, pady=5, columnspan=2)

        ttk.Label(input_frame, text="Birth Time (HH:MM 24h):").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.time_entry = ttk.Entry(input_frame, width=40)
        self.time_entry.grid(row=2, column=1, padx=5, pady=5)
        ttk.Label(input_frame, text="(leave blank or type 'unknown' to default to noon)", foreground="#555555").grid(row=2, column=3, padx=5, pady=5, sticky="w")

        ttk.Label(input_frame, text="Birth City:").grid(row=3, column=0, padx=5, pady=5, sticky="e")
        self.city_entry = ttk.Entry(input_frame, width=40)
        self.city_entry.grid(row=3, column=1, padx=5, pady=5, columnspan=2)

        ttk.Label(input_frame, text="Two-Letter Country Code:").grid(row=4, column=0, padx=5, pady=5, sticky="e")
        self.country_entry = ttk.Entry(input_frame, width=40)
        self.country_entry.grid(row=4, column=1, padx=5, pady=5, columnspan=2)

        # Main action button — with sv_ttk this will look like a proper Windows accent button
        self.calc_btn = ttk.Button(self, text="Generate Natal Chart", command=self.start_calculation)
        self.calc_btn.pack(pady=(8, 4), ipadx=16, ipady=6)

        self.status = ttk.Label(self, text="", foreground="#4ade80")
        self.status.pack(pady=2)

        # The report preview — native tk.Text feels like a real Windows text viewer / Notepad
        report_frame = ttk.Frame(self)
        report_frame.pack(padx=16, pady=4, fill="both", expand=True)

        self.report_text = tk.Text(report_frame, width=98, height=17,
                                   font=("Consolas", 11), wrap="word",
                                   borderwidth=1, relief="solid", padx=6, pady=4)
        self.report_text.pack(side="left", fill="both", expand=True)

        yscroll = ttk.Scrollbar(report_frame, orient="vertical", command=self.report_text.yview)
        yscroll.pack(side="right", fill="y")
        self.report_text.configure(yscrollcommand=yscroll.set)

        button_frame = ttk.Frame(self)
        button_frame.pack(pady=(2, 12))

        self.svg_btn = ttk.Button(button_frame, text="Open SVG Natal Wheel", state="disabled", command=self.open_svg)
        self.svg_btn.grid(row=0, column=0, padx=7)

        self.pdf_btn = ttk.Button(button_frame, text="Open PDF Report", state="disabled", command=self.open_pdf)
        self.pdf_btn.grid(row=0, column=1, padx=7)

        # Legacy buttons (kept for now, may be disabled if only PDF+SVG produced)
        self.html_btn = ttk.Button(button_frame, text="Open HTML (legacy)", state="disabled", command=self.open_html)
        self.html_btn.grid(row=0, column=2, padx=7)

        self.txt_btn = ttk.Button(button_frame, text="Open TXT (legacy)", state="disabled", command=self.open_txt)
        self.txt_btn.grid(row=0, column=3, padx=7)

        self.svg_path = None
        self.pdf_path = None  # New primary report format
        self.txt_path = None  # legacy, may be None
        self.html_path = None  # legacy, may be None

    def start_calculation(self):
        self.calc_btn.configure(state="disabled")
        self.status.configure(text="Building chart...", foreground="#facc15")
        self.report_text.delete("1.0", "end")
        log("Button clicked - starting thread")
        threading.Thread(target=self.calculate_chart, daemon=True).start()

    def calculate_chart(self):
        log("=== CALCULATION THREAD STARTED ===")
        try:
            name = self.name_entry.get().strip() or "Unknown"
            date_str = self.date_entry.get().strip()
            time_str = self.time_entry.get().strip()
            city_input = self.city_entry.get().strip() or "Lincoln"
            country_input = self.country_entry.get().strip() or "US"

            # Handle unknown time
            unknown_time = False
            if not time_str or time_str.lower() in ["unknown", "unknown time", "?", "unk", "n/a"]:
                time_str = "12:00"
                unknown_time = True
                log("⚠️  Unknown birth time - defaulting to noon (12:00)")

            y, m, d = map(int, date_str.split('-'))
            h, min_ = map(int, time_str.split(':'))

            log("Getting location")
            city, country, lat, lng, tz_str = self.get_location_data(city_input, country_input)

            log("Creating AstrologicalSubject")
            subject = AstrologicalSubjectFactory.from_birth_data(
                name=name, year=y, month=m, day=d, hour=h, minute=min_,
                city=city, nation=country, lng=lng, lat=lat, tz_str=tz_str, online=False
            )
            log("Subject created successfully")

            log("Generating report")
            report_gen = ReportGenerator(subject)
            report_text = report_gen.generate_report()
            log("Report generated")

            # Build quick positions + aspects in background thread (avoids UI work)
            log("Building key positions and aspects")
            quick = self._build_quick_positions(subject)
            aspects, _ = self._build_aspects(subject)
            elem_qual = self._build_elements_and_qualities(subject)

            base_name = f"{name.replace(' ', '_')}_{y}-{m:02d}-{d:02d}"
            if unknown_time:
                base_name += "_noon_time"

            # Determine output location: user's Desktop (cross platform)
            output_dir = get_desktop_path()
            log(f"Output directory (Desktop): {output_dir}")

            # Generate files directly here in background thread (no nested threads, no UI blocking)
            log("Generating files on Desktop...")
            self.txt_path = output_dir / f"{base_name}_report.txt"
            self.html_path = output_dir / f"{base_name}_report.html"
            self.svg_path = None
            svg_error = None

            # === NEW: PDF Report (primary) + keep SVG ===
            # We scrapped the old HTML/TXT as primary deliverables per request.
            try:
                self._create_pdf_report(report_text, quick, aspects, elem_qual, subject, base_name, unknown_time, output_dir)
            except Exception as e:
                log(f"PDF creation error: {e}")
                self.report_text.insert("end", f"\n\n⚠️  PDF generation failed: {e}\n")

            # SVG - the previously flaky part. Do it here synchronously in bg thread.
            try:
                log("Starting SVG generation (birth chart wheel)...")
                chart_data = ChartDataFactory.create_natal_chart_data(subject)
                drawer = ChartDrawer(chart_data=chart_data)
                svg_filename = f"{base_name}_natal"
                # kerykeion will write <output_dir>/<svg_filename>.svg
                drawer.save_svg(output_path=str(output_dir), filename=svg_filename)
                candidate = output_dir / f"{svg_filename}.svg"
                if candidate.exists():
                    self.svg_path = candidate
                    log(f"SVG saved successfully: {self.svg_path.name}")
                else:
                    # In case kerykeion used a different name pattern
                    self.svg_path = None
                    svg_error = "SVG file was not found after generation"
                    log("⚠️  SVG generation completed but file not located at expected path")
            except Exception as e:
                log(f"SVG generation error: {e}")
                self.svg_path = None
                svg_error = str(e)

            log("Calling finish_calculation")
            self.after(0, self.finish_calculation, report_text, quick, aspects, elem_qual, subject, name, y, m, d, unknown_time, svg_error)

        except Exception as e:
            log(f"ERROR: {e}")
            self.after(0, self.show_error, str(e))

    def finish_calculation(self, report_text, quick, aspects, elem_qual, subject, name, y, m, d, unknown_time, svg_error):
        log("finish_calculation started")
        self.report_text.delete("1.0", "end")

        # Add warning if time was unknown
        if unknown_time:
            warning = "⚠️  WARNING: Birth time was unknown. Using NOON (12:00) as default.\n"
            warning += "This means the Ascendant, Midheaven, and House positions may be INACCURATE.\n"
            warning += "For accurate readings, obtain the actual birth time.\n"
            warning += "=" * 70 + "\n\n"
            self.report_text.insert("1.0", warning)
            log("⚠️  Unknown time warning added to report")

        self.report_text.insert("end", report_text)
        self.report_text.insert("end", quick)
        self.report_text.insert("end", aspects)
        self.report_text.insert("end", elem_qual)

        if svg_error:
            self.report_text.insert("end", f"\n\n⚠️  SVG birth chart generation issue: {svg_error}\n")

        # Update buttons (paths were already set in background thread to Desktop)
        if self.svg_path and self.svg_path.exists():
            self.svg_btn.configure(state="normal")
        else:
            self.svg_btn.configure(state="disabled")

        if self.pdf_path and self.pdf_path.exists():
            self.pdf_btn.configure(state="normal")
        else:
            self.pdf_btn.configure(state="disabled")

        # Legacy
        if self.html_path and self.html_path.exists():
            self.html_btn.configure(state="normal")
        else:
            self.html_btn.configure(state="disabled")
        if self.txt_path and self.txt_path.exists():
            self.txt_btn.configure(state="normal")
        else:
            self.txt_btn.configure(state="disabled")

        # Clear, user-friendly status that explicitly mentions the Desktop
        desktop = get_desktop_path()
        files_msg = "Done! Files saved to your Desktop:"
        if self.pdf_path and self.pdf_path.exists():
            files_msg += f"\n   - {self.pdf_path.name}  (main formatted report)"
        if self.svg_path and self.svg_path.exists():
            files_msg += f"\n   - {self.svg_path.name}  (vector birth chart wheel)"
        else:
            files_msg += "\n   (SVG chart wheel unavailable)"

        files_msg += f"\nLocation: {desktop}"
        self.status.configure(text=files_msg, foreground="#4ade80")
        self.calc_btn.configure(state="normal")
        log("=== CALCULATION FINISHED SUCCESSFULLY ===")

    def show_error(self, error_msg):
        self.status.configure(text=f"Error: {error_msg[:100]}", foreground="#f87171")
        self.calc_btn.configure(state="normal")

    def get_location_data(self, city: str, country: str):
        geolocator = Nominatim(user_agent="western_astrology_calculator")
        try:
            location = geolocator.geocode(f"{city}, {country}", timeout=10)
            if location:
                lat, lng = location.latitude, location.longitude
                tf = TimezoneFinder()
                tz_str = tf.timezone_at(lng=lng, lat=lat) or "UTC"
                return city, country, lat, lng, tz_str
        except:
            pass
        return "Lincoln", "US", 40.8, -96.7, "America/Chicago"

    def _build_quick_positions(self, subject) -> str:
        quick = "\n\nKEY POSITIONS\n"
        quick += "-" * 70 + "\n"
        quick += f"{'Planet':<12} | {'Sign':<8} | {'Degree':>7} | {'House':<6} | {'Retro':<5}\n"
        quick += "-" * 70 + "\n"
        points = [subject.sun, subject.moon, subject.mercury, subject.venus,
                  subject.mars, subject.jupiter, subject.saturn,
                  subject.uranus, subject.neptune, subject.pluto]
        for p in points:
            retro = "R" if getattr(p, 'retrograde', False) else ""
            house = getattr(p, 'house', '—')
            quick += f"{p.name:<12} | {p.sign:<8} | {p.position:>6.2f}° | {str(house):<6} | {retro:<5}\n"
        quick += "-" * 70 + "\n"
        return quick

    # --- Custom element & quality calculation (user-requested restriction) ---
    _SIGN_TO_ELEMENT = {
        'Ari': 'Fire', 'Leo': 'Fire', 'Sag': 'Fire',
        'Tau': 'Earth', 'Vir': 'Earth', 'Cap': 'Earth',
        'Gem': 'Air', 'Lib': 'Air', 'Aqu': 'Air',
        'Can': 'Water', 'Sco': 'Water', 'Pis': 'Water',
    }
    _SIGN_TO_QUALITY = {
        'Ari': 'Cardinal', 'Can': 'Cardinal', 'Lib': 'Cardinal', 'Cap': 'Cardinal',
        'Tau': 'Fixed', 'Leo': 'Fixed', 'Sco': 'Fixed', 'Aqu': 'Fixed',
        'Gem': 'Mutable', 'Vir': 'Mutable', 'Sag': 'Mutable', 'Pis': 'Mutable',
    }

    def _build_elements_and_qualities(self, subject) -> str:
        """Calculate elemental and quality balance using ONLY:
        the 10 planets (incl. Sun/Moon) + Ascendant + Midheaven.
        """
        selected = [
            subject.sun, subject.moon, subject.mercury, subject.venus, subject.mars,
            subject.jupiter, subject.saturn, subject.uranus, subject.neptune, subject.pluto,
            subject.first_house, subject.tenth_house,
        ]

        elements = {'Fire': 0, 'Earth': 0, 'Air': 0, 'Water': 0}
        qualities = {'Cardinal': 0, 'Fixed': 0, 'Mutable': 0}

        for point in selected:
            sign = getattr(point, 'sign', None)
            if sign:
                sign = sign[:3]  # normalize 'Tau ♉️' or 'Taurus' etc. to 'Tau'
                elem = self._SIGN_TO_ELEMENT.get(sign)
                qual = self._SIGN_TO_QUALITY.get(sign)
                if elem:
                    elements[elem] += 1
                if qual:
                    qualities[qual] += 1

        total = sum(elements.values()) or 1

        out = "\n\nELEMENTAL BALANCE (10 planets + Ascendant + Midheaven only)\n" + "=" * 55 + "\n"
        for elem in ('Fire', 'Earth', 'Air', 'Water'):
            count = elements[elem]
            pct = (count / total) * 100
            out += f"{elem:6} : {count:2d} / {total}   ({pct:5.1f}%)\n"

        out += "\nQUALITY / MODALITY BALANCE (same restricted points)\n" + "=" * 55 + "\n"
        for qual in ('Cardinal', 'Fixed', 'Mutable'):
            count = qualities[qual]
            pct = (count / total) * 100
            out += f"{qual:8} : {count:2d} / {total}   ({pct:5.1f}%)\n"

        out += "\n(Note: This is a custom calculation. Kerykeion's internal totals may differ as they include additional points.)\n"
        return out

    def _build_aspects(self, subject):
        """Return (aspects_text_block, list_of_lines) for display + file inclusion. Now with table headers."""
        aspects = "\n\nASPECTS\n"
        aspects += "-" * 70 + "\n"
        aspects += f"{'Planet 1':<12} | {'Aspect':<12} | {'Planet 2':<12} | {'Orb':>7} | {'Movement':<12}\n"
        aspects += "-" * 70 + "\n"
        aspects_data = []
        try:
            chart_data = ChartDataFactory.create_natal_chart_data(subject)
            if hasattr(chart_data, 'aspects') and chart_data.aspects:
                for aspect in chart_data.aspects:
                    p1 = aspect.p1_name
                    p2 = aspect.p2_name
                    asp_type = aspect.aspect
                    orb = abs(aspect.orbit)
                    movement = aspect.aspect_movement
                    aspect_line = f"{p1:<12} | {asp_type:<12} | {p2:<12} | {orb:>6.2f}° | {movement:<12}\n"
                    aspects += aspect_line
                    aspects_data.append(aspect_line.strip())
                log(f"Added {len(chart_data.aspects)} aspects")
            else:
                aspects += "No aspects found\n"
        except Exception as e:
            log(f"Error extracting aspects: {e}")
            aspects += f"Error: {str(e)}\n"
        aspects += "-" * 70 + "\n"
        return aspects, aspects_data

    def _open_path(self, path: Path | None):
        """Cross-platform: open a file with its default application."""
        if not path or not path.exists():
            return
        try:
            if sys.platform == "win32":
                os.startfile(str(path))
            elif sys.platform == "darwin":
                subprocess.call(["open", str(path)])
            else:
                subprocess.call(["xdg-open", str(path)])
        except Exception:
            # Fallback
            try:
                webbrowser.open(path.as_uri())
            except Exception:
                pass

    def _open_folder(self, folder: Path):
        """Cross-platform open folder in file manager."""
        if not folder or not folder.exists():
            folder = Path.home()
        try:
            if sys.platform == "win32":
                os.startfile(str(folder))
            elif sys.platform == "darwin":
                subprocess.call(["open", str(folder)])
            else:
                subprocess.call(["xdg-open", str(folder)])
        except Exception:
            try:
                webbrowser.open(folder.as_uri())
            except Exception:
                pass

    def _create_pdf_report(self, report_text: str, quick: str, aspects: str, elem_qual: str, subject, base_name: str, unknown_time: bool, output_dir: Path):
        """Generate a professional PDF report with:
        - Birth details
        - Embedded chart wheel (PNG converted from SVG when possible)
        - Summary tables (positions, aspects, elements/qualities) WITH HEADERS
        - Detailed interpretive breakdown (planet sign + house + aspects + retro notes)
        using the editable database in interpretations.py
        """
        pdf_path = output_dir / f"{base_name}_natal_report.pdf"
        self.pdf_path = pdf_path

        # Try to produce a PNG of the chart wheel for embedding
        png_path = output_dir / f"{base_name}_natal_chart.png"
        chart_image_path = None
        if self.svg_path and self.svg_path.exists():
            try:
                cairosvg.svg2png(url=str(self.svg_path), write_to=str(png_path), output_width=700, output_height=700)
                if png_path.exists():
                    chart_image_path = png_path
                    log(f"Chart PNG created for PDF: {png_path.name}")
            except Exception as e:
                log(f"Could not convert SVG to PNG for PDF (cairosvg issue?): {e}")
                chart_image_path = None  # Will note the SVG file instead

        # Build the PDF
        doc = SimpleDocTemplate(str(pdf_path), pagesize=letter,
                                rightMargin=0.6*inch, leftMargin=0.6*inch,
                                topMargin=0.6*inch, bottomMargin=0.6*inch)

        styles = getSampleStyleSheet()
        # Custom styles for nice look
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            alignment=TA_CENTER,
            spaceAfter=12,
            textColor=colors.HexColor('#1e3a8a')
        )
        heading2 = ParagraphStyle('H2', parent=styles['Heading2'], fontSize=13, spaceAfter=6, spaceBefore=12, textColor=colors.HexColor('#1e40af'))
        body_style = ParagraphStyle('Body', parent=styles['Normal'], fontSize=9, leading=11, spaceAfter=4)
        small = ParagraphStyle('Small', parent=styles['Normal'], fontSize=8, leading=10)

        story = []

        # Title
        story.append(Paragraph(f"{base_name} — Natal Chart Report", title_style))
        story.append(Spacer(1, 6))

        # Birth details (simple)
        birth_info = f"<b>Birth Data:</b> {subject.day}/{subject.month}/{subject.year} {subject.hour:02d}:{subject.minute:02d} | {subject.city}, {subject.nation} (lat {subject.lat:.2f}, lon {subject.lng:.2f})"
        if unknown_time:
            birth_info += " <b>(time unknown — used noon)</b>"
        story.append(Paragraph(birth_info, body_style))
        story.append(Spacer(1, 8))

        # Chart image
        if chart_image_path:
            try:
                img = Image(str(chart_image_path), width=5.5*inch, height=5.5*inch)
                story.append(img)
                story.append(Paragraph("<i>Visual natal wheel (also saved as separate .svg for high-quality vector use)</i>", small))
            except Exception:
                story.append(Paragraph("<i>[Chart wheel image could not be embedded — see the separate .svg file on your Desktop]</i>", small))
        else:
            story.append(Paragraph("<i>Visual natal wheel saved separately as .svg (open in browser or vector editor). The full interpretive report is below.</i>", small))
        story.append(Spacer(1, 10))

        # Summary tables with headers
        story.append(Paragraph("Chart Summary — Positions", heading2))

        # Positions table (parsed from quick or rebuild)
        pos_data = [["Planet", "Sign", "Degree", "House", "Retro"]]
        # crude parse from the quick text we already have (or rebuild quickly)
        lines = [l for l in quick.splitlines() if "|" in l and "Planet" not in l and "---" not in l]
        for line in lines[:12]:  # the 10 planets + asc/mc if included
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 5:
                pos_data.append([parts[0][:12], parts[1], parts[2], parts[3], parts[4]])

        if len(pos_data) > 1:
            t = Table(pos_data, colWidths=[1.3*inch, 0.9*inch, 0.9*inch, 0.7*inch, 0.6*inch])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                ('FONTSIZE', (0, 1), (-1, -1), 7),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f1f5f9')]),
            ]))
            story.append(t)
        story.append(Spacer(1, 8))

        # Aspects table with headers
        story.append(Paragraph("Aspects (major)", heading2))
        asp_data = [["Planet 1", "Aspect", "Planet 2", "Orb", "Movement"]]
        asp_lines = [l for l in aspects.splitlines() if "|" in l and "Planet 1" not in l and "---" not in l]
        for line in asp_lines[:15]:  # limit for space
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 5:
                asp_data.append(parts[:5])

        if len(asp_data) > 1:
            t2 = Table(asp_data, colWidths=[1.1*inch, 1.0*inch, 1.1*inch, 0.7*inch, 1.2*inch])
            t2.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                ('FONTSIZE', (0, 1), (-1, -1), 7),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f1f5f9')]),
            ]))
            story.append(t2)
        story.append(Spacer(1, 6))

        # Elements & Qualities (already nicely formatted in elem_qual)
        story.append(Paragraph("Elemental & Quality Balance (10 planets + Asc + MC only)", heading2))
        story.append(Paragraph(elem_qual.replace("\n", "<br/>"), small))
        story.append(Spacer(1, 10))

        # Detailed Interpretive Breakdown
        story.append(PageBreak())
        story.append(Paragraph("Detailed Interpretive Breakdown", title_style))
        story.append(Paragraph("This section walks through each planet: its sign placement + house, the interpretation, retrograde notes (if any), and the aspects it forms (with interpretations from the database).", body_style))
        story.append(Spacer(1, 8))

        # Build detailed per-planet
        main_planets = [subject.sun, subject.moon, subject.mercury, subject.venus, subject.mars,
                        subject.jupiter, subject.saturn, subject.uranus, subject.neptune, subject.pluto]

        # Get aspects list for cross reference
        aspect_list = []
        try:
            cd = ChartDataFactory.create_natal_chart_data(subject)
            if hasattr(cd, 'aspects'):
                aspect_list = cd.aspects
        except:
            pass

        for p in main_planets:
            p_name = p.name
            sign = getattr(p, 'sign', '—')
            house = getattr(p, 'house', None)
            degree = getattr(p, 'position', 0)
            is_retro = getattr(p, 'retrograde', False)

            line = f"<b>{p_name} in {sign} {degree:.1f}°"
            if house:
                line += f" — House {house}"
            if is_retro:
                line += " (Retrograde)"
            line += "</b>"
            story.append(Paragraph(line, heading2))

            # Sign interp
            sign_interp = interpretations.get_planet_sign_interpretation(p_name, sign)
            story.append(Paragraph(sign_interp, body_style))

            # House interp
            if house and isinstance(house, (int, float)):
                house_interp = interpretations.get_planet_house_interpretation(p_name, int(house))
                story.append(Paragraph(f"<i>House {int(house)}:</i> {house_interp}", small))

            # Retro note
            if is_retro:
                retro_note = interpretations.get_retrograde_note(p_name)
                story.append(Paragraph(f"<b>Retrograde note:</b> {retro_note}", small))

            # Aspects for this planet
            planet_aspects = []
            for a in aspect_list:
                if a.p1_name == p_name or a.p2_name == p_name:
                    other = a.p2_name if a.p1_name == p_name else a.p1_name
                    planet_aspects.append((a, other))

            if planet_aspects:
                story.append(Paragraph("<b>Aspects:</b>", small))
                for a, other in planet_aspects[:6]:  # limit
                    asp_text = interpretations.get_aspect_interpretation(p_name, other, a.aspect)
                    story.append(Paragraph(f"• {p_name} {a.aspect} {other} (orb {abs(a.orbit):.2f}°): {asp_text}", small))

            story.append(Spacer(1, 6))

        # Asc and MC brief
        try:
            asc_sign = getattr(subject.first_house, 'sign', '—')
            mc_sign = getattr(subject.tenth_house, 'sign', '—')
            story.append(Paragraph(f"<b>Ascendant (Rising) in {asc_sign}</b> — Your approach to life and first impression. Customize interpretation in interpretations.py", body_style))
            story.append(Paragraph(f"<b>Midheaven (MC) in {mc_sign}</b> — Public path, career, and legacy. Customize in interpretations.py", body_style))
        except:
            pass

        story.append(Spacer(1, 12))
        story.append(Paragraph("— End of Report —<br/>SVG vector chart wheel and this PDF are both on your Desktop.", small))

        # Build
        doc.build(story)
        log(f"PDF report saved: {pdf_path.name}")

    def _create_txt_report(self, report_text: str, quick: str, aspects: str, elem_qual: str, base_name: str, unknown_time: bool, output_dir: Path):
        """Create a plain text report file on the given output_dir (Desktop)."""
        txt_content = f"🌟 {base_name}\n"
        txt_content += "=" * 70 + "\n\n"

        if unknown_time:
            txt_content += "⚠️  WARNING: Birth time was unknown. Using NOON (12:00) as default.\n"
            txt_content += "This means the Ascendant, Midheaven, and House positions may be INACCURATE.\n"
            txt_content += "For accurate readings, obtain the actual birth time.\n"
            txt_content += "=" * 70 + "\n\n"

        txt_content += report_text
        txt_content += quick
        txt_content += aspects
        txt_content += elem_qual

        self.txt_path = output_dir / f"{base_name}_report.txt"
        self.txt_path.write_text(txt_content, encoding="utf-8")
        log(f"Text report saved: {self.txt_path.name}")

    def _create_html_report(self, report_text: str, quick: str, aspects: str, elem_qual: str, base_name: str, unknown_time: bool, output_dir: Path):
        """Create an HTML report file WITH ASPECTS on the given output_dir (Desktop)."""
        warning_html = ""
        if unknown_time:
            warning_html = """<div style="background-color: #FFF3CD; border: 2px solid #FFC107; padding: 12px; margin: 12px 0; border-radius: 4px;">
<p><strong>⚠️  WARNING: Unknown Birth Time</strong></p>
<p>Birth time was unknown. This chart uses NOON (12:00) as default.</p>
<p><strong>This means the following may be INACCURATE:</strong></p>
<ul>
<li>Ascendant (Rising Sign)</li>
<li>Midheaven (MC)</li>
<li>House positions</li>
</ul>
<p>For accurate readings, obtain the actual birth time from the birth certificate.</p>
</div>"""

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{base_name} Report</title>
<style>
body {{ font-family: 'Courier New', monospace; margin: 20px; background-color: #f5f5f5; }}
.container {{ max-width: 900px; margin: 0 auto; background-color: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
h1 {{ color: #333; border-bottom: 2px solid #007BFF; padding-bottom: 10px; }}
h2 {{ color: #555; margin-top: 30px; border-left: 4px solid #007BFF; padding-left: 10px; }}
pre {{ background-color: #f9f9f9; padding: 15px; border-radius: 4px; overflow-x: auto; border: 1px solid #ddd; }}
.warning {{ background-color: #FFF3CD; border: 2px solid #FFC107; padding: 12px; margin: 12px 0; border-radius: 4px; }}
table {{ border-collapse: collapse; width: 100%; margin: 15px 0; }}
td {{ border: 1px solid #ddd; padding: 8px; }}
</style>
</head>
<body>
<div class="container">
<h1>🌟 {base_name}</h1>
{warning_html}

<h2>Report</h2>
<pre>{report_text}</pre>

<h2>Key Positions</h2>
<pre>{quick}</pre>

<h2>Aspects</h2>
<pre>{aspects}</pre>

<h2>Elements &amp; Qualities (restricted)</h2>
<pre>{elem_qual}</pre>

<p style="text-align: center; color: #999; margin-top: 30px; font-size: 12px;">
Generated by Western Astrology Calculator
</p>
</div>
</body>
</html>"""
        self.html_path = output_dir / f"{base_name}_report.html"
        self.html_path.write_text(html_content, encoding="utf-8")
        log(f"HTML report saved: {self.html_path.name}")

    def open_svg(self):
        self._open_path(self.svg_path)

    def open_html(self):
        self._open_path(self.html_path)

    def open_txt(self):
        self._open_path(self.txt_path)

    def open_pdf(self):
        self._open_path(self.pdf_path)


if __name__ == "__main__":
    app = AstrologyGUI()
    app.mainloop()