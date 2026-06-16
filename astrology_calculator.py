import datetime
import os
import sys
from pathlib import Path

# Core Kerykeion (2026 API)
from kerykeion import AstrologicalSubjectFactory
from kerykeion.chart_data_factory import ChartDataFactory
from kerykeion.charts.chart_drawer import ChartDrawer
from kerykeion import ReportGenerator

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


def get_desktop_path() -> Path:
    """Cross-platform desktop with common fallbacks."""
    home = Path.home()
    candidates = [home / "Desktop"]
    if os.name == "nt":
        onedrive = os.environ.get("OneDrive")
        if onedrive:
            candidates.insert(0, Path(onedrive) / "Desktop")
        onedrive_c = os.environ.get("OneDriveConsumer")
        if onedrive_c:
            candidates.insert(0, Path(onedrive_c) / "Desktop")
    for c in candidates:
        if c.exists():
            return c
    d = home / "Desktop"
    try:
        d.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    return d


def _build_quick_positions(subject) -> str:
    quick = "\n\nKEY POSITIONS\n" + "=" * 50 + "\n"
    points = [subject.sun, subject.moon, subject.mercury, subject.venus,
              subject.mars, subject.jupiter, subject.saturn,
              subject.uranus, subject.neptune, subject.pluto]
    for p in points:
        retro = " R" if getattr(p, 'retrograde', False) else ""
        house = getattr(p, 'house', '—')
        quick += f"{p.name:>10}: {p.sign} {p.position:.1f}°  House {house}{retro}\n"
    return quick


def _build_aspects_text(subject) -> str:
    aspects = "\n\nASPECTS\n" + "=" * 50 + "\n"
    try:
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        if hasattr(chart_data, 'aspects') and chart_data.aspects:
            for aspect in chart_data.aspects:
                p1 = aspect.p1_name
                p2 = aspect.p2_name
                asp_type = aspect.aspect
                orb = abs(aspect.orbit)
                movement = aspect.aspect_movement
                aspects += f"{p1:>10} {asp_type:>12} {p2:<10}  Orb: {orb:5.2f}°  {movement}\n"
        else:
            aspects += "No aspects found\n"
    except Exception as e:
        aspects += f"Error extracting aspects: {e}\n"
    return aspects


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
    except Exception:
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

    # === Full report ===
    print("\n" + "=" * 70)
    print("FULL NATAL CHART REPORT")
    print("=" * 70)
    ReportGenerator(subject).print_report()

    # Build supplemental sections
    quick = _build_quick_positions(subject)
    aspects = _build_aspects_text(subject)

    print(quick)
    print(aspects)

    # === Determine output dir: Desktop (cross platform) ===
    output_dir = get_desktop_path()
    base_name = f"{name.replace(' ', '_')}_{y}-{m:02d}-{d:02d}"

    # === TEXT REPORT ===
    txt_path = output_dir / f"{base_name}_report.txt"
    txt_content = f"🌟 {base_name}\n" + "=" * 70 + "\n\n"
    # Rebuild a simple console report capture is hard; reuse what was printed + sections
    # For CLI we re-generate a clean text block
    try:
        report_gen = ReportGenerator(subject)
        report_str = report_gen.generate_report()
    except Exception:
        report_str = "(Full report printed to console above)\n"
    txt_content += report_str + quick + aspects
    txt_path.write_text(txt_content, encoding="utf-8")
    print(f"\n✓ Text report: {txt_path}")

    # === HTML REPORT ===
    html_path = output_dir / f"{base_name}_report.html"
    html_content = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>{base_name}</title>
<style>body{{font-family:monospace;margin:20px}} pre{{background:#f8f8f8;padding:12px}}</style>
</head><body>
<h1>🌟 {base_name} — Western Astrology Natal Chart</h1>
<h2>Full Report</h2><pre>{report_str}</pre>
<h2>Key Positions</h2><pre>{quick}</pre>
<h2>Aspects</h2><pre>{aspects}</pre>
<p style="color:#888;font-size:12px">Generated by Western Astrology Calculator</p>
</body></html>"""
    html_path.write_text(html_content, encoding="utf-8")
    print(f"✓ HTML report:  {html_path}")

    # === SVG birth chart ===
    svg_path = None
    try:
        print("Generating SVG birth chart wheel (may take a few seconds)...")
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        drawer = ChartDrawer(chart_data=chart_data)
        svg_name = f"{base_name}_natal"
        drawer.save_svg(output_path=str(output_dir), filename=svg_name)
        candidate = output_dir / f"{svg_name}.svg"
        if candidate.exists():
            svg_path = candidate
            print(f"✓ SVG chart:    {svg_path}")
        else:
            print("⚠️  SVG generated but path unexpected.")
    except Exception as e:
        print(f"⚠️  SVG generation failed: {e}")

    print("\n" + "=" * 70)
    print(f"✅ All results saved to your Desktop: {output_dir}")
    print("   You can open the .html, .txt, or .svg files directly from there.")
    print("=" * 70)


if __name__ == "__main__":
    generate_practical_report()