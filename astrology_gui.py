import datetime
import webbrowser
import sys
import os
import threading
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
    print(message)  # also shows in console if you run from cmd


class AstrologyGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Western Astrology Calculator")
        self.geometry("1080x760")

        icon_path = resource_path("icon.ico")
        if os.path.exists(icon_path):
            self.iconbitmap(icon_path)

        log("GUI started")

        # ... (input fields same as your version) ...
        title = ctk.CTkLabel(self, text="🌟 Western Astrology Calculator", font=ctk.CTkFont(size=24, weight="bold"))
        title.pack(pady=15)

        input_frame = ctk.CTkFrame(self)
        input_frame.pack(padx=20, pady=10, fill="x")

        ctk.CTkLabel(input_frame, text="Full Name:").grid(row=0, column=0, padx=10, pady=8, sticky="e")
        self.name_entry = ctk.CTkEntry(input_frame, width=300)
        self.name_entry.grid(row=0, column=1, padx=10, pady=8)
        self.name_entry.insert(0, "Fritz Wolfram")

        ctk.CTkLabel(input_frame, text="Birthday (YYYY-MM-DD):").grid(row=1, column=0, padx=10, pady=8, sticky="e")
        self.date_entry = ctk.CTkEntry(input_frame, width=300)
        self.date_entry.grid(row=1, column=1, padx=10, pady=8)
        self.date_entry.insert(0, "2003-05-06")

        ctk.CTkLabel(input_frame, text="Birth Time (HH:MM 24h):").grid(row=2, column=0, padx=10, pady=8, sticky="e")
        self.time_entry = ctk.CTkEntry(input_frame, width=300)
        self.time_entry.grid(row=2, column=1, padx=10, pady=8)
        self.time_entry.insert(0, "11:15")

        ctk.CTkLabel(input_frame, text="Birth City:").grid(row=3, column=0, padx=10, pady=8, sticky="e")
        self.city_entry = ctk.CTkEntry(input_frame, width=300)
        self.city_entry.grid(row=3, column=1, padx=10, pady=8)
        self.city_entry.insert(0, "Tashkent")

        ctk.CTkLabel(input_frame, text="Country Code (e.g. UZ, US):").grid(row=4, column=0, padx=10, pady=8, sticky="e")
        self.country_entry = ctk.CTkEntry(input_frame, width=300)
        self.country_entry.grid(row=4, column=1, padx=10, pady=8)
        self.country_entry.insert(0, "UZ")

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

        self.svg_path = None
        self.html_path = None

    def start_calculation(self):
        self.calc_btn.configure(state="disabled")
        self.status.configure(text="Building chart...", text_color="yellow")
        self.report_text.delete("1.0", "end")
        log("Button clicked - starting thread")
        threading.Thread(target=self.calculate_chart, daemon=True).start()

    def calculate_chart(self):
        log("=== CALCULATION THREAD STARTED ===")
        try:
            log("Parsing inputs")
            name = self.name_entry.get().strip() or "Unknown"
            date_str = self.date_entry.get().strip()
            time_str = self.time_entry.get().strip() or "12:00"
            city_input = self.city_entry.get().strip() or "Lincoln"
            country_input = self.country_entry.get().strip() or "US"

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
            self.after(0, self.finish_calculation, report_text, subject, name, y, m, d)

        except Exception as e:
            log(f"ERROR: {e}")
            self.after(0, self.show_error, str(e))

    def finish_calculation(self, report_text, subject, name, y, m, d):
        log("finish_calculation started")
        self.report_text.delete("1.0", "end")
        self.report_text.insert("1.0", report_text)

        log("Adding quick positions")
        # quick positions code here (same as before)

        base_name = f"{name.replace(' ', '_')}_{y}-{m:02d}-{d:02d}"

        # TEMPORARILY SKIP SVG to isolate freeze
        log("Skipping SVG generation for diagnosis")
        self.svg_path = None

        self.html_path = Path.cwd() / f"{base_name}_report.html"
        self._create_html_report(report_text, subject, base_name)

        self.svg_btn.configure(state="disabled")  # disabled for now
        self.html_btn.configure(state="normal")
        self.status.configure(text="✅ Report done! (SVG temporarily disabled for testing)", text_color="lightgreen")
        self.calc_btn.configure(state="normal")
        log("=== CALCULATION FINISHED SUCCESSFULLY ===")

    def show_error(self, error_msg):
        self.status.configure(text=f"❌ Error: {error_msg[:100]}", text_color="red")
        self.calc_btn.configure(state="normal")

    def get_location_data(self, city: str, country: str):
        # same as before
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

    def _create_html_report(self, report_text: str, subject, base_name: str):
        # same simple HTML as before
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>{base_name} Report</title></head>
<body><h1>🌟 {base_name}</h1><pre>{report_text}</pre></body>
</html>"""
        self.html_path.write_text(html_content, encoding="utf-8")

    def open_svg(self): pass
    def open_html(self):
        if self.html_path and self.html_path.exists():
            webbrowser.open(self.html_path.absolute().as_uri())


if __name__ == "__main__":
    app = AstrologyGUI()
    app.mainloop()