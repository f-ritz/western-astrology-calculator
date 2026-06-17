#!/usr/bin/env python
"""
Cross-platform build script for Western Astrology Calculator.

- On Windows: produces Western_Astrology_Calculator.exe (single file)
- On macOS:   produces a .app bundle + support files (or single binary with --onefile)
- On Linux:   produces a single binary (or folder)

Run this on the target platform you want to build for.
PyInstaller does not do true cross-compilation for GUI apps.

Usage:
    python build_exe.py                 # auto onefile + windowed
    python build_exe.py --onedir        # folder build (sometimes more reliable)

After build, your artifacts are in ./dist/
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def main():
    print("=" * 72)
    print("Western Astrology Calculator — Cross-Platform Builder")
    print("=" * 72)
    print(f"Host platform: {platform.system()} ({platform.platform()})")
    print()

    script_path = Path("astrology_gui_fixed.py")
    if not script_path.exists():
        print(f"❌ Error: {script_path} not found!")
        sys.exit(1)
    print("✓ Found astrology_gui_fixed.py")
    print("  (GUI uses ttk + sv-ttk. PDF uses reportlab. cairosvg for chart PNG in PDF is OPTIONAL and often problematic to bundle.)")
    print("   The app now runs fine without it (SVG is always saved separately + full report in PDF).")

    icon_path = Path("icon.ico")
    has_icon = icon_path.exists()
    if has_icon:
        print("✓ Found icon.ico")
    else:
        print("⚠ icon.ico not found — build will continue without a custom icon")

    onedir = "--onedir" in sys.argv
    mode = "onedir" if onedir else "onefile"

    print(f"\nBuild mode: {mode} (windowed / no console)")
    print("This may take 2–6 minutes...\n")

    system = platform.system().lower()

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--windowed",
        "--name", "Western_Astrology_Calculator",
        "astrology_gui_fixed.py",
    ]

    if mode == "onefile":
        cmd.insert(3, "--onefile")

    if has_icon:
        if system == "windows":
            cmd += ["--icon", "icon.ico"]
            # PyInstaller on Windows accepts add-data with ; or :
            cmd += ["--add-data", "icon.ico:."]
        elif system == "darwin":
            # On macOS you normally want an .icns. .ico may be ignored or cause warnings.
            # We'll still pass it; user can replace with icon.icns for best results.
            cmd += ["--icon", "icon.ico"]
        else:
            # Linux typically uses --icon with png or just skips for onefile binary
            cmd += ["--icon", "icon.ico"]

    # Include kerykeion + pyswisseph + timezonefinder data files reliably
    # Using the .spec is often better for complex data, but this CLI path works too.
    try:
        from PyInstaller.utils.hooks import collect_data_files
        datas = []
        datas += collect_data_files("kerykeion")
        datas += collect_data_files("pyswisseph")
        datas += collect_data_files("timezonefinder")
        for src, dest in datas:
            # PyInstaller expects "SRC:DEST" or "SRC;DEST" on Windows
            sep = ";" if system == "windows" else ":"
            cmd += ["--add-data", f"{src}{sep}{dest}"]
    except Exception as e:
        print(f"(Note: could not auto-collect some data files via hooks: {e})")
        print("If the resulting binary is missing ephemeris data, use the .spec file or install from source instead.")

    # Clean previous builds for this mode (optional but less confusing)
    dist_dir = Path("dist")
    if dist_dir.exists():
        print("Cleaning previous dist artifacts (keep this folder if you have other builds)...")

    print("\nRunning: " + " ".join(cmd) + "\n")

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print("\n❌ BUILD FAILED")
        print(e)
        sys.exit(1)

    print("\n" + "=" * 72)
    print("✅ BUILD COMPLETE")
    print("=" * 72)

    if system == "windows":
        exe = dist_dir / "Western_Astrology_Calculator.exe"
        if exe.exists():
            size = exe.stat().st_size / (1024*1024)
            print(f"\n📦 Windows EXE: {exe}  ({size:.1f} MB)")
        else:
            # onedir case
            folder = dist_dir / "Western_Astrology_Calculator"
            print(f"\n📦 Windows folder app: {folder}")
    elif system == "darwin":
        app = dist_dir / "Western_Astrology_Calculator.app"
        bin_ = dist_dir / "Western_Astrology_Calculator"
        if app.exists():
            print(f"\n📦 macOS app bundle: {app}")
            print("   You can right-click → Open, or drag to /Applications.")
            print("   For distribution consider creating a .dmg (e.g. with create-dmg or py2app).")
        elif bin_.exists():
            print(f"\n📦 macOS single binary: {bin_}  (chmod +x and run)")
    else:
        bin_ = dist_dir / "Western_Astrology_Calculator"
        if bin_.exists():
            print(f"\n📦 Linux binary: {bin_}")
            print("   chmod +x it and run. For wider compatibility consider AppImage or a .deb package.")

    print("\nAll output is in the ./dist/ directory.")
    print("Tip: Run this build script *on the operating system* you want to target.")
    print("=" * 72)


if __name__ == "__main__":
    main()
