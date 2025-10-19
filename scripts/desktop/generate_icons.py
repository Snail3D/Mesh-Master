#!/usr/bin/env python3
"""
Generate platform-specific icon files from SVG
Creates PNG, ICO (Windows), and ICNS (macOS) formats
"""

import os
import sys
from pathlib import Path

try:
    from PIL import Image
    import cairosvg
except ImportError:
    print("Installing required dependencies: pillow, cairosvg")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pillow", "cairosvg"])
    from PIL import Image
    import cairosvg

def get_project_dir():
    """Get the Mesh Master project directory"""
    # This script is in scripts/desktop/, so go up two levels
    return Path(__file__).parent.parent.parent.absolute()

def svg_to_png(svg_path, png_path, size):
    """Convert SVG to PNG at specified size"""
    cairosvg.svg2png(
        url=str(svg_path),
        write_to=str(png_path),
        output_width=size,
        output_height=size
    )
    print(f"✓ Created {png_path.name} ({size}x{size})")

def png_to_ico(png_path, ico_path):
    """Convert PNG to ICO (Windows icon)"""
    img = Image.open(png_path)
    img.save(ico_path, format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
    print(f"✓ Created {ico_path.name} (multi-size ICO)")

def png_to_icns(png_path, icns_path):
    """Convert PNG to ICNS (macOS icon)"""
    # macOS iconutil requires a .iconset directory with specific sizes
    iconset_dir = icns_path.with_suffix('.iconset')
    iconset_dir.mkdir(exist_ok=True)

    img = Image.open(png_path)

    # Generate required sizes for macOS
    sizes = [
        (16, 'icon_16x16.png'),
        (32, 'icon_16x16@2x.png'),
        (32, 'icon_32x32.png'),
        (64, 'icon_32x32@2x.png'),
        (128, 'icon_128x128.png'),
        (256, 'icon_128x128@2x.png'),
        (256, 'icon_256x256.png'),
        (512, 'icon_256x256@2x.png'),
        (512, 'icon_512x512.png'),
        (1024, 'icon_512x512@2x.png'),
    ]

    for size, filename in sizes:
        resized = img.resize((size, size), Image.Resampling.LANCZOS)
        resized.save(iconset_dir / filename)

    # Convert iconset to icns using iconutil (macOS only)
    import platform
    if platform.system() == "Darwin":
        import subprocess
        subprocess.run(['iconutil', '-c', 'icns', str(iconset_dir), '-o', str(icns_path)], check=True)
        print(f"✓ Created {icns_path.name} (macOS icon)")

        # Clean up iconset directory
        import shutil
        shutil.rmtree(iconset_dir)
    else:
        print(f"⚠ Skipping ICNS creation (iconutil only available on macOS)")
        print(f"  Created iconset directory: {iconset_dir}")

def generate_all_icons():
    """Generate all platform-specific icon files"""
    project_dir = get_project_dir()
    static_dir = project_dir / "static"

    svg_path = static_dir / "mesh-master-icon.svg"

    if not svg_path.exists():
        print(f"✗ SVG file not found: {svg_path}")
        return False

    print(f"Generating icons from {svg_path.name}...")
    print("")

    try:
        # Generate PNG (512x512 for high quality)
        png_path = static_dir / "mesh-master-icon.png"
        svg_to_png(svg_path, png_path, 512)

        # Generate ICO (Windows)
        ico_path = static_dir / "mesh-master-icon.ico"
        png_to_ico(png_path, ico_path)

        # Generate ICNS (macOS)
        icns_path = static_dir / "mesh-master-icon.icns"
        png_to_icns(png_path, icns_path)

        print("")
        print("========================================")
        print("  Icon Generation Complete!")
        print("========================================")
        print("")
        print("Generated files:")
        print(f"  • {png_path.name} - Linux/general use")
        print(f"  • {ico_path.name} - Windows shortcuts")
        print(f"  • {icns_path.name} - macOS apps")
        print("")

        return True

    except Exception as e:
        print(f"✗ Error generating icons: {e}")
        return False

if __name__ == "__main__":
    success = generate_all_icons()
    sys.exit(0 if success else 1)
