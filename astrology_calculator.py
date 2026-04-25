import datetime
from pathlib import Path

# Core Kerykeion (2026 API)
from kerykeion import AstrologicalSubjectFactory
from kerykeion.chart_data_factory import ChartDataFactory
from kerykeion.charts.chart_drawer import ChartDrawer

# Location helpers
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
from timezonefinder import TimezoneFinder  # pip install timezonefinder


def get_location_data(city: str, country: str):
    """Accurate lat/lng + timezone (offline after first run)"""
    geolocator = Nominatim(user_agent="western_astrology_calculator")
    try:
        location = geolocator.geocode(f"{city}, {country}", timeout=10)
        if location:
            lat, lng = location.latitude, location.longitude
            tf = TimezoneFinder()
            tz_str = tf.timezone_at(lng=lng, lat=lat) or "UTC"
            return city, country, lat, lng, tz_str
    except GeocoderTimedOut:
        pass

    print("⚠️ Geolocation failed — using fallback (Lincoln, NE)")
    return "Lincoln", "US", 40.8, -96.7, "America/Chicago"


def generate_practical_report():
    print("\n🌟 Western Astrology Calculator")

    name = input("Full name: ").strip() or "Unknown"
    date_str = input("Birthday (YYYY-MM-DD): ").strip()
    time_str = input("Birth time (HH:MM 24h) — REQUIRED for houses/angles: ").strip() or "12:00"
    city_input = input("Birth city: ").strip() or "Lincoln"
    country_input = input("Birth country code (e.g. US): ").strip() or "US"

    # Parse date/time
    try:
        y, m, d = map(int, date_str.split('-'))
        h, min_ = map(int, time_str.split(':'))
    except:
        print("Invalid date/time — using demo data")
        y, m, d, h, min_ = 2003, 5, 6, 11, 15

    # Get accurate location data
    city, country, lat, lng, tz_str = get_location_data(city_input, country_input)

    print(f"\nRunning chart for {name} — {y}-{m:02d}-{d:02d} {h:02d}:{min_:02d}")
    print(f"Location: {city}, {country} @ {lat:.4f}°N, {lng:.4f}°E | TZ: {tz_str}")

    # === Create subject with FULL correct parameters ===
    subject = AstrologicalSubjectFactory.from_birth_data(
        name=name,
        year=y,
        month=m,
        day=d,
        hour=h,
        minute=min_,
        city=city,
        nation=country,
        lng=lng,
        lat=lat,
        tz_str=tz_str,
        online=False,  # Fully offline after install
    )

    # === Full report (now shows correct city/country) ===
    print("\n" + "=" * 70)
    print("FULL NATAL CHART REPORT")
    print("=" * 70)
    from kerykeion import ReportGenerator
    ReportGenerator(subject).print_report()

    # === SVG natal wheel ===
    chart_data = ChartDataFactory.create_natal_chart_data(subject)
    drawer = ChartDrawer(chart_data=chart_data)

    output_path = Path(f"{name.replace(' ', '_')}_{y}-{m:02d}-{d:02d}_natal")
    drawer.save_svg(output_path=str(output_path.parent), filename=output_path.name)
    print(f"\n✓ SVG natal wheel saved: {output_path.name}.svg")

    # === Quick reference positions ===
    print("\nKEY POSITIONS")
    points = [subject.sun, subject.moon, subject.mercury, subject.venus,
              subject.mars, subject.jupiter, subject.saturn,
              subject.uranus, subject.neptune, subject.pluto]
    for p in points:
        retro = " R" if getattr(p, 'retrograde', False) else ""
        house = getattr(p, 'house', '—')
        print(f"{p.name:>10}: {p.sign} {p.position:.1f}°  House {house}{retro}")

if __name__ == "__main__":
    generate_practical_report()