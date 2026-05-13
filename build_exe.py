#!/usr/bin/env python
"""
Build script for Western Astrology Calculator
Packages the Python app into a standalone Windows EXE file

This script handles all the heavy lifting of PyInstaller configuration.
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    print("=" * 70)
    print("Western Astrology Calculator - EXE Builder")
    print("=" * 70)
    
    # Check if the main file exists
    script_path = Path("astrology_gui_fixed.py")
    if not script_path.exists():
        print(f"❌ Error: {script_path} not found!")
        print("Make sure astrology_gui_fixed.py is in the current directory.")
        sys.exit(1)
    
    print("\n✓ Found astrology_gui_fixed.py")
    
    # Check if spec file exists
    spec_path = Path("astrology.spec")
    if not spec_path.exists():
        print(f"❌ Error: {spec_path} not found!")
        print("Make sure astrology.spec is in the current directory.")
        sys.exit(1)
    
    print("✓ Found astrology.spec")
    
    # Check if icon exists (optional)
    icon_path = Path("icon.ico")
    if icon_path.exists():
        print(f"✓ Found icon.ico (will be included)")
    else:
        print("⚠ Warning: icon.ico not found (application will work without it)")
    
    print("\n" + "=" * 70)
    print("Building EXE...")
    print("This may take 2-5 minutes depending on your system")
    print("=" * 70 + "\n")
    
    # Run PyInstaller
    cmd = [
        sys.executable,
        "-m", "PyInstaller",
        "--onefile",  # Single EXE file
        "--windowed",  # No console window
        "--name", "Western_Astrology_Calculator",
        "--icon", "icon.ico" if icon_path.exists() else None,
        "--add-data", "icon.ico:." if icon_path.exists() else None,
        "astrology_gui_fixed.py"
    ]
    
    # Remove None values from command
    cmd = [arg for arg in cmd if arg is not None]
    
    try:
        result = subprocess.run(cmd, check=True)
        
        print("\n" + "=" * 70)
        print("✅ BUILD SUCCESSFUL!")
        print("=" * 70)
        
        exe_path = Path("dist") / "Western_Astrology_Calculator.exe"
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"\n📦 EXE created: {exe_path}")
            print(f"   Size: {size_mb:.1f} MB")
            print(f"\n📍 Location: {exe_path.absolute()}")
            print(f"\nYou can now distribute this EXE to others!")
            print(f"No Python installation required on the target computer.")
        else:
            print("Warning: EXE file not found in dist/ folder")
            
    except subprocess.CalledProcessError as e:
        print("\n" + "=" * 70)
        print("❌ BUILD FAILED")
        print("=" * 70)
        print(f"\nError: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
