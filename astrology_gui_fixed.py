import datetime
import webbrowser
import sys
import os
import threading
import subprocess
from pathlib import Path

import customtkinter as ctk
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
from timezonefinder import TimezoneFinder

from kerykeion import AstrologicalSubjectFactory
from kerykeion.chart_data_factory import ChartDataFactory
from kerykeion.charts.chart_drawer import ChartDrawer
from kerykeion import ReportGenerator

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


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


class AstrologyGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Western Astrology Calculator")
        self.geometry("1080x800")

        icon_path = resource_path("icon.ico")
        if os.path.exists(icon_path):
            self.iconbitmap(icon_path)

        log("GUI started")

        title = ctk.CTkLabel(self, text="🌟 Western Astrology Calculator", font=ctk.CTkFont(size=24, weight="bold"))
        title.pack(pady=15)

        input_frame = ctk.CTkFrame(self)
        input_frame.pack(padx=20, pady=10, fill="x")

        ctk.CTkLabel(input_frame, text="Full Name:").grid(row=0, column=0, padx=10, pady=8, sticky="e")
        self.name_entry = ctk.CTkEntry(input_frame, width=300)
        self.name_entry.grid(row=0, column=1, padx=10, pady=8)
        self.name_entry.insert(0, "")

        ctk.CTkLabel(input_frame, text="Birthday (YYYY-MM-DD):").grid(row=1, column=0, padx=10, pady=8, sticky="e")
        self.date_entry = ctk.CTkEntry(input_frame, width=300)
        self.date_entry.grid(row=1, column=1, padx=10, pady=8)
        self.date_entry.insert(0, "")

        ctk.CTkLabel(input_frame, text="Birth Time (HH:MM 24h):").grid(row=2, column=0, padx=10, pady=8, sticky="e")
        self.time_entry = ctk.CTkEntry(input_frame, width=300)
        self.time_entry.grid(row=2, column=1, padx=10, pady=8)
        self.time_entry.insert(0, "")
        # Help text for unknown time
        time_help = ctk.CTkLabel(input_frame,
                                 text="(Leave empty or enter 'unknown' if time is not known → defaults to noon)",
                                 text_color="gray", font=ctk.CTkFont(size=10))
        time_help.grid(row=2, column=2, padx=10, pady=8, sticky="w")

        ctk.CTkLabel(input_frame, text="Birth City:").grid(row=3, column=0, padx=10, pady=8, sticky="e")
        self.city_entry = ctk.CTkEntry(input_frame, width=300)
        self.city_entry.grid(row=3, column=1, padx=10, pady=8)
        self.city_entry.insert(0, "")

        ctk.CTkLabel(input_frame, text="Two-Letter Country Code:").grid(row=4, column=0, padx=10, pady=8, sticky="e")
        self.country_entry = ctk.CTkEntry(input_frame, width=300)
        self.country_entry.grid(row=4, column=1, padx=10, pady=8)
        self.country_entry.insert(0, "")

        self.calc_btn = ctk.CTkButton(self, text="Generate Natal Chart", font=ctk.CTkFont(size=16, weight="bold"),
                                      height=50, command=self.start_calculation)
        self.calc_btn.pack(pady=20)

        self.status = ctk.CTkLabel(self, text="", text_color="lightgreen")
        self.status.pack(pady=5)

        self.report_text = ctk.CTkTextbox(self, width=960, height=320, font=ctk.CTkFont(family="Consolas", size=13))
        self.report_text.pack(padx=20, pady=10, fill="both", expand=True)

        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(pady=10)

        self.svg_btn = ctk.CTkButton(button_frame, text="Open SVG Natal Wheel", state="disabled", command=self.open_svg)
        self.svg_btn.grid(row=0, column=0, padx=10)

        self.html_btn = ctk.CTkButton(button_frame, text="Open HTML Report", state="disabled", command=self.open_html)
        self.html_btn.grid(row=0, column=1, padx=10)

        self.txt_btn = ctk.CTkButton(button_frame, text="Open Text Report", state="disabled", command=self.open_txt)
        self.txt_btn.grid(row=0, column=2, padx=10)

        self.svg_path = None
        self.html_path = None
        self.txt_path = None

    def start_calculation(self):
        self.calc_btn.configure(state="disabled")
        self.status.configure(text="Building chart...", text_color="yellow")
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

            try:
                self._create_txt_report(report_text, quick, aspects, base_name, unknown_time, output_dir)
            except Exception as e:
                log(f"TXT creation error: {e}")

            try:
                self._create_html_report(report_text, quick, aspects, base_name, unknown_time, output_dir)
            except Exception as e:
                log(f"HTML creation error: {e}")

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
            self.after(0, self.finish_calculation, report_text, quick, aspects, subject, name, y, m, d, unknown_time, svg_error)

        except Exception as e:
            log(f"ERROR: {e}")
            self.after(0, self.show_error, str(e))

    def finish_calculation(self, report_text, quick, aspects, subject, name, y, m, d, unknown_time, svg_error):
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

        if svg_error:
            self.report_text.insert("end", f"\n\n⚠️  SVG birth chart generation issue: {svg_error}\n")

        # Update buttons (paths were already set in background thread to Desktop)
        if self.svg_path and self.svg_path.exists():
            self.svg_btn.configure(state="normal")
        else:
            self.svg_btn.configure(state="disabled")

        self.html_btn.configure(state="normal")
        self.txt_btn.configure(state="normal")

        # Clear, user-friendly status that explicitly mentions the Desktop
        desktop = get_desktop_path()
        files_msg = f"✅ Done! Files saved to your Desktop:\n   • {self.txt_path.name}\n   • {self.html_path.name}"
        if self.svg_path and self.svg_path.exists():
            files_msg += f"\n   • {self.svg_path.name}"
        else:
            files_msg += "\n   (SVG chart wheel unavailable - see report for details)"

        files_msg += f"\n📍 Location: {desktop}"
        self.status.configure(text=files_msg, text_color="lightgreen")
        self.calc_btn.configure(state="normal")
        log("=== CALCULATION FINISHED SUCCESSFULLY ===")

    def show_error(self, error_msg):
        self.status.configure(text=f"❌ Error: {error_msg[:100]}", text_color="red")
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
        quick = "\n\nKEY POSITIONS\n" + "=" * 50 + "\n"
        points = [subject.sun, subject.moon, subject.mercury, subject.venus,
                  subject.mars, subject.jupiter, subject.saturn,
                  subject.uranus, subject.neptune, subject.pluto]
        for p in points:
            retro = " R" if getattr(p, 'retrograde', False) else ""
            house = getattr(p, 'house', '—')
            quick += f"{p.name:>10}: {p.sign} {p.position:.1f}°  House {house}{retro}\n"
        return quick

    def _build_aspects(self, subject):
        """Return (aspects_text_block, list_of_lines) for display + file inclusion."""
        aspects = "\n\nASPECTS\n" + "=" * 50 + "\n"
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
                    aspect_line = f"{p1:>10} {asp_type:>12} {p2:<10}  Orb: {orb:5.2f}°  {movement}\n"
                    aspects += aspect_line
                    aspects_data.append(aspect_line.strip())
                log(f"Added {len(chart_data.aspects)} aspects")
            else:
                aspects += "No aspects found\n"
        except Exception as e:
            log(f"Error extracting aspects: {e}")
            aspects += f"Error: {str(e)}\n"
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

    def _create_txt_report(self, report_text: str, quick: str, aspects: str, base_name: str, unknown_time: bool, output_dir: Path):
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

        self.txt_path = output_dir / f"{base_name}_report.txt"
        self.txt_path.write_text(txt_content, encoding="utf-8")
        log(f"Text report saved: {self.txt_path.name}")

    def _create_html_report(self, report_text: str, quick: str, aspects: str, base_name: str, unknown_time: bool, output_dir: Path):
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


if __name__ == "__main__":
    app = AstrologyGUI()
    app.mainloop()