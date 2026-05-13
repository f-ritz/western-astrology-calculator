import datetime
import webbrowser
import sys
import os
import threading
from pathlib import Path
import signal

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


class TimeoutError(Exception):
    pass


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

            log("Calling finish_calculation")
            self.after(0, self.finish_calculation, report_text, subject, name, y, m, d, unknown_time)

        except Exception as e:
            log(f"ERROR: {e}")
            self.after(0, self.show_error, str(e))

    def finish_calculation(self, report_text, subject, name, y, m, d, unknown_time):
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

        # Quick positions
        log("Adding quick positions")
        quick = "\n\nKEY POSITIONS\n" + "=" * 50 + "\n"
        points = [subject.sun, subject.moon, subject.mercury, subject.venus,
                  subject.mars, subject.jupiter, subject.saturn,
                  subject.uranus, subject.neptune, subject.pluto]
        for p in points:
            retro = " R" if getattr(p, 'retrograde', False) else ""
            house = getattr(p, 'house', '—')
            quick += f"{p.name:>10}: {p.sign} {p.position:.1f}°  House {house}{retro}\n"
        self.report_text.insert("end", quick)

        base_name = f"{name.replace(' ', '_')}_{y}-{m:02d}-{d:02d}"
        if unknown_time:
            base_name += "_noon_time"

        # === BUILD ASPECTS SECTION ===
        log("Building aspects section")
        aspects = "\n\nASPECTS\n" + "=" * 50 + "\n"
        aspects_data = []  # Store for later use in files
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
        self.report_text.insert("end", aspects)

        # === SVG GENERATION WITH TIMEOUT ===
        log("Starting SVG generation")
        self.svg_path = None
        try:
            chart_data = ChartDataFactory.create_natal_chart_data(subject)
            log("ChartData created, generating SVG (this may take a moment)...")

            # Try SVG generation in a thread with timeout
            svg_thread = threading.Thread(
                target=self._generate_svg_safe,
                args=(chart_data, base_name),
                daemon=True
            )
            svg_thread.start()
            svg_thread.join(timeout=30)  # 30 second timeout

            if svg_thread.is_alive():
                log("⚠️  SVG generation timed out after 30 seconds - skipping SVG")
                self.report_text.insert("end", "\n\n⚠️  SVG generation took too long - skipping.\n")
            elif self.svg_path and self.svg_path.exists():
                log("SVG saved successfully")
            else:
                log("⚠️  SVG generation failed or was not saved")
                self.report_text.insert("end", "\n\n⚠️  SVG generation failed - chart image unavailable.\n")

        except Exception as e:
            log(f"Error during SVG generation: {e}")
            self.report_text.insert("end", f"\n\n⚠️  SVG generation error: {str(e)}\n")

        # === TEXT REPORT ===
        log("Creating text report")
        self.txt_path = Path.cwd() / f"{base_name}_report.txt"
        self._create_txt_report(report_text, quick, aspects, base_name, unknown_time)

        # === HTML REPORT WITH ASPECTS ===
        log("Creating HTML report with aspects")
        self.html_path = Path.cwd() / f"{base_name}_report.html"
        self._create_html_report(report_text, quick, aspects, base_name, unknown_time)

        # Update buttons
        if self.svg_path and self.svg_path.exists():
            self.svg_btn.configure(state="normal")
        else:
            self.svg_btn.configure(state="disabled")

        self.html_btn.configure(state="normal")
        self.txt_btn.configure(state="normal")

        files_msg = f"✅ Done! Files saved:\n   • {self.txt_path.name}\n   • {self.html_path.name}"
        if self.svg_path and self.svg_path.exists():
            files_msg += f"\n   • {self.svg_path.name}"

        self.status.configure(text=files_msg, text_color="lightgreen")
        self.calc_btn.configure(state="normal")
        log("=== CALCULATION FINISHED SUCCESSFULLY ===")

    def _generate_svg_safe(self, chart_data, base_name):
        """Generate SVG in a safe way with error handling"""
        try:
            log("Creating ChartDrawer...")
            drawer = ChartDrawer(chart_data=chart_data)

            log("Saving SVG...")
            self.svg_path = Path.cwd() / f"{base_name}_natal.svg"
            drawer.save_svg(output_path=str(Path.cwd()), filename=f"{base_name}_natal")

            log("SVG saved successfully")
        except Exception as e:
            log(f"Error in SVG generation thread: {e}")
            self.svg_path = None

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

    def _create_txt_report(self, report_text: str, quick: str, aspects: str, base_name: str, unknown_time: bool):
        """Create a plain text report file"""
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

        self.txt_path.write_text(txt_content, encoding="utf-8")
        log(f"Text report saved: {self.txt_path.name}")

    def _create_html_report(self, report_text: str, quick: str, aspects: str, base_name: str, unknown_time: bool):
        """Create an HTML report file WITH ASPECTS"""
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
        self.html_path.write_text(html_content, encoding="utf-8")
        log(f"HTML report saved: {self.html_path.name}")

    def open_svg(self):
        if self.svg_path and self.svg_path.exists():
            webbrowser.open(self.svg_path.absolute().as_uri())

    def open_html(self):
        if self.html_path and self.html_path.exists():
            webbrowser.open(self.html_path.absolute().as_uri())

    def open_txt(self):
        if self.txt_path and self.txt_path.exists():
            os.startfile(self.txt_path) if sys.platform == 'win32' else os.system(
                f'open "{self.txt_path}"' if sys.platform == 'darwin' else f'xdg-open "{self.txt_path}"')


if __name__ == "__main__":
    app = AstrologyGUI()
    app.mainloop()