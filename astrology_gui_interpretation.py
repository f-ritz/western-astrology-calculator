import datetime
import webbrowser
from pathlib import Path

import customtkinter as ctk
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
from timezonefinder import TimezoneFinder

# Kerykeion imports
from kerykeion import AstrologicalSubjectFactory
from kerykeion.chart_data_factory import ChartDataFactory
from kerykeion.charts.chart_drawer import ChartDrawer
from kerykeion import ReportGenerator

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# ====================== DETAILED INTERPRETATIONS ======================
# Serious, actionable interpretations you can actually use

PLANET_SIGN_INTERPS = {
    "Sun": {
        "Aries": "Sun in Aries gives raw initiating power and a need to be first. You thrive on challenge and direct action. Life rewards you when you lead boldly, but you must learn to finish what you start and manage impulsiveness. This is warrior energy — use it to carve your own path.",
        "Taurus": "Sun in Taurus is about building lasting security and value. You have exceptional stamina, sensual awareness, and a drive to create something solid. Your path is one of mastery through patience, craft, and steady effort. Stubbornness is your shadow — know when to yield.",
        "Gemini": "Sun in Gemini makes the mind your primary instrument. Curiosity, communication, and versatility are your superpowers. You need variety and mental stimulation or you stagnate. Your life mission is to gather, connect, and distribute information and ideas.",
        "Cancer": "Sun in Cancer is deeply protective and intuitive. Your core identity is tied to home, family, and emotional security. You have strong nurturing instincts and the ability to create safe spaces. Life asks you to protect your sensitivity while learning healthy boundaries.",
        "Leo": "Sun in Leo is pure creative self-expression. You are here to shine, lead, and be recognized. Generosity, warmth, and dramatic flair come naturally. Your challenge is to lead without needing constant applause and to let others shine too.",
        "Virgo": "Sun in Virgo is about refinement and service. You have an eye for detail, systems, and improvement. Your path is one of mastery through analysis, skill-building, and practical helpfulness. Perfectionism is the shadow — learn to accept 'good enough' when it serves the greater good.",
        "Libra": "Sun in Libra seeks balance, beauty, and harmonious relationships. You have a natural gift for diplomacy and aesthetics. Life pushes you to develop your own identity while learning the art of fair partnership. Avoid people-pleasing at the cost of your truth.",
        "Scorpio": "Sun in Scorpio gives intense focus and transformative power. You are drawn to depth, truth, and the hidden side of life. This placement forges unbreakable will and psychological insight. Your journey involves facing the dark, releasing control, and rising renewed.",
        "Sagittarius": "Sun in Sagittarius is the seeker and philosopher. You need freedom, truth, and expansion. Travel, higher learning, and big ideas feed your soul. Your mission is to explore, teach, and live according to your own philosophy while staying grounded in ethics.",
        "Capricorn": "Sun in Capricorn is about building legacy and mastery. You have natural authority, discipline, and long-term vision. Life rewards you for patient ambition and responsible leadership. The shadow is coldness or workaholism — remember to enjoy the climb.",
        "Aquarius": "Sun in Aquarius brings visionary, humanitarian energy. You are here to innovate, question norms, and improve the collective. Independence and originality are core to your identity. Your challenge is to stay connected to people while pursuing radical ideas.",
        "Pisces": "Sun in Pisces is compassionate, artistic, and deeply intuitive. You feel the collective and have a natural connection to the unseen. Your path is one of surrender, creativity, and service. Boundaries are essential so you don’t dissolve into everyone else’s emotions.",
    },
    # Add more planets as needed — these are the most important
    "Moon": {  # example for Moon
        "Cancer": "Moon in Cancer is the most natural placement for the Moon. Deep emotional sensitivity, strong need for security, and powerful instincts. You feel everything. Protect your energy and create safe emotional homes.",
        # ... (full Moon signs can be expanded later — this is enough to get you started)
    }
}

PLANET_HOUSE_INTERPS = {
    "Sun": {
        1: "Sun in 1st House — Your identity is front and center. Life forces you to become unmistakably yourself. Leadership and personal presence are your arenas.",
        2: "Sun in 2nd House — Self-worth and material security are central themes. You are here to build value and trust your own resources.",
        5: "Sun in 5th House — Creative self-expression, romance, and joy are your lifeblood. You regenerate through play, art, and heartfelt risk.",
        10: "Sun in 10th House — Career, reputation, and public role are where your light shines brightest. Authority and visible achievement matter deeply.",
        # ... (the code below uses a general template for missing ones)
    }
}

def get_detailed_interpretation(subject):
    interp = "\n\n🌌 DETAILED INTERPRETIVE ANALYSIS\n"
    interp += "="*70 + "\n\n"

    # Major planets
    for planet_obj in [subject.sun, subject.moon, subject.mercury, subject.venus,
                       subject.mars, subject.jupiter, subject.saturn,
                       subject.uranus, subject.neptune, subject.pluto]:
        p_name = planet_obj.name
        sign = planet_obj.sign
        house = getattr(planet_obj, 'house', None)
        degree = planet_obj.position

        interp += f"★ {p_name} in {sign} ({degree:.1f}°) — House {house}\n"

        # Sign interpretation
        sign_text = PLANET_SIGN_INTERPS.get(p_name, {}).get(sign, f"{p_name} in {sign} activates {p_name.lower()}-ruled qualities through a {sign.lower()} lens.")
        interp += sign_text + "\n\n"

        # House interpretation
        if house and isinstance(house, int):
            house_text = PLANET_HOUSE_INTERPS.get(p_name, {}).get(house, f"In the {house}th house, {p_name} directs its energy toward matters of identity, resources, communication, home, creativity, work, relationships, transformation, philosophy, career, community, or the subconscious (house {house}).")
            interp += house_text + "\n\n"

    # Angles
    interp += f"★ Ascendant {getattr(subject.first_house, 'sign', '—')} {getattr(subject.first_house, 'degree', 0):.1f}° — Your approach to life and first impression.\n"
    interp += f"★ Midheaven (MC) {getattr(subject.tenth_house, 'sign', '—')} {getattr(subject.tenth_house, 'degree', 0):.1f}° — Your public path, career, and legacy.\n"

    return interp

# ====================== MAIN GUI ======================
class AstrologyGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Celestial Strategy — Western Astrology Calculator")
        self.geometry("1100x780")
        self.resizable(True, True)

        title = ctk.CTkLabel(self, text="🌟 Western Astrology Calculator", font=ctk.CTkFont(size=24, weight="bold"))
        title.pack(pady=15)

        input_frame = ctk.CTkFrame(self)
        input_frame.pack(padx=20, pady=10, fill="x")

        ctk.CTkLabel(input_frame, text="Full Name:").grid(row=0, column=0, padx=10, pady=8, sticky="e")
        self.name_entry = ctk.CTkEntry(input_frame, width=300)
        self.name_entry.grid(row=0, column=1, padx=10, pady=8)

        ctk.CTkLabel(input_frame, text="Birthday (YYYY-MM-DD):").grid(row=1, column=0, padx=10, pady=8, sticky="e")
        self.date_entry = ctk.CTkEntry(input_frame, width=300)
        self.date_entry.grid(row=1, column=1, padx=10, pady=8)

        ctk.CTkLabel(input_frame, text="Birth Time (HH:MM 24h):").grid(row=2, column=0, padx=10, pady=8, sticky="e")
        self.time_entry = ctk.CTkEntry(input_frame, width=300)
        self.time_entry.grid(row=2, column=1, padx=10, pady=8)

        ctk.CTkLabel(input_frame, text="Birth City:").grid(row=3, column=0, padx=10, pady=8, sticky="e")
        self.city_entry = ctk.CTkEntry(input_frame, width=300)
        self.city_entry.grid(row=3, column=1, padx=10, pady=8)

        ctk.CTkLabel(input_frame, text="Country Code (e.g. UZ, US):").grid(row=4, column=0, padx=10, pady=8, sticky="e")
        self.country_entry = ctk.CTkEntry(input_frame, width=300)
        self.country_entry.grid(row=4, column=1, padx=10, pady=8)

        self.calc_btn = ctk.CTkButton(self, text="Generate Natal Chart", font=ctk.CTkFont(size=16, weight="bold"),
                                      height=50, command=self.calculate_chart)
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

    def get_location_data(self, city: str, country: str):
        # ... (same as before - unchanged)
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
        self.status.configure(text="⚠️ Location lookup failed — using fallback", text_color="orange")
        return "Lincoln", "US", 40.8, -96.7, "America/Chicago"

    def calculate_chart(self):
        # ... (same logic as before, now calling the full interpretation function)
        self.status.configure(text="Calculating full chart...", text_color="yellow")
        self.update()

        name = self.name_entry.get().strip() or "Unknown"
        date_str = self.date_entry.get().strip()
        time_str = self.time_entry.get().strip() or "12:00"
        city_input = self.city_entry.get().strip() or "Lincoln"
        country_input = self.country_entry.get().strip() or "US"

        try:
            y, m, d = map(int, date_str.split('-'))
            h, min_ = map(int, time_str.split(':'))
        except:
            self.status.configure(text="Invalid date/time format", text_color="red")
            return

        city, country, lat, lng, tz_str = self.get_location_data(city_input, country_input)

        subject = AstrologicalSubjectFactory.from_birth_data(
            name=name, year=y, month=m, day=d, hour=h, minute=min_,
            city=city, nation=country, lng=lng, lat=lat, tz_str=tz_str, online=False
        )

        report_gen = ReportGenerator(subject)
        report_text = report_gen.generate_report()

        interpretive_text = get_detailed_interpretation(subject)

        self.report_text.delete("1.0", "end")
        self.report_text.insert("1.0", report_text + interpretive_text)

        base_name = f"{name.replace(' ', '_')}_{y}-{m:02d}-{d:02d}"
        self.svg_path = Path.cwd() / f"{base_name}_natal.svg"
        self.html_path = Path.cwd() / f"{base_name}_report.html"

        # SVG
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        drawer = ChartDrawer(chart_data=chart_data)
        drawer.save_svg(output_path=str(Path.cwd()), filename=f"{base_name}_natal")

        # HTML with interpretations
        self._create_html_report(report_text, interpretive_text, subject, base_name)

        self.svg_btn.configure(state="normal")
        self.html_btn.configure(state="normal")
        self.status.configure(text=f"✅ Complete! SVG + HTML saved", text_color="lightgreen")

    def _create_html_report(self, technical_report: str, interpretive_text: str, subject, base_name: str):
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{base_name} — Full Western Astrology Report</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500&family=Space+Grotesk:wght@500;600&display=swap');
        body {{ font-family: 'Inter', sans-serif; background:#0a0a0a; color:#e0e0e0; margin:0; padding:40px; }}
        .container {{ max-width:1100px; margin:0 auto; background:#111; border-radius:20px; padding:50px; box-shadow:0 25px 50px rgba(0,0,0,0.8); }}
        h1 {{ font-family:'Space Grotesk'; color:#a78bfa; text-align:center; }}
        h2 {{ color:#c4b5fd; border-bottom:2px solid #4c1d95; padding-bottom:8px; }}
        pre {{ background:#1a1a1a; padding:30px; border-radius:16px; font-size:15px; line-height:1.7; overflow:auto; }}
        .interp {{ background:#1a1425; padding:35px; border-radius:16px; margin-top:40px; white-space: pre-wrap; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🌟 {base_name} — Complete Natal Report</h1>
        <h2>📜 Technical Chart</h2>
        <pre>{technical_report}</pre>
        <h2>🌌 Detailed Interpretive Analysis</h2>
        <div class="interp">{interpretive_text}</div>
    </div>
</body>
</html>"""
        self.html_path.write_text(html_content, encoding="utf-8")

    def open_svg(self):
        if self.svg_path and self.svg_path.exists():
            webbrowser.open(self.svg_path.absolute().as_uri())

    def open_html(self):
        if self.html_path and self.html_path.exists():
            webbrowser.open(self.html_path.absolute().as_uri())

if __name__ == "__main__":
    app = AstrologyGUI()
    app.mainloop()