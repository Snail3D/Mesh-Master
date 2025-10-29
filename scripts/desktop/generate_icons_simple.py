#!/usr/bin/env python3
"""
Generate desktop icons for Mesh Master
Creates a dark background with MM text using PIL only
"""

import os
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

def get_project_dir():
    """Get the Mesh Master project directory"""
    return Path(__file__).parent.parent.parent.absolute()

def create_mm_icon(size=512):
    """Create MM icon with dark background"""
    # Create dark background
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Draw rounded rectangle background
    padding = max(1, int(size * 0.1))
    radius = max(2, int(size * 0.15))

    # Dark background gradient effect (simulate with solid color)
    bg_color = (10, 13, 26, 255)  # Dark blue-black

    # Draw rounded rectangle (for very small sizes, just use rectangle)
    if size >= 32:
        draw.rounded_rectangle(
            [0, 0, size-1, size-1],
            radius=radius,
            fill=bg_color,
            outline=None
        )
    else:
        # Simple rectangle for tiny icons
        draw.rectangle([0, 0, size-1, size-1], fill=bg_color)

    # Skip text for very small icons (< 32px)
    if size >= 32:
        # Draw MM text
        text = "MM"
        text_color = (0, 149, 255, 255)  # Bright cyan-blue

        # Try to use a system font, fallback to default
        font_size = max(8, int(size * 0.45))
        try:
            # Try various font options
            font_paths = [
                '/System/Library/Fonts/Helvetica.ttc',
                '/Library/Fonts/Arial.ttf',
                '/System/Library/Fonts/Avenir.ttc',
            ]
            font = None
            for font_path in font_paths:
                if os.path.exists(font_path):
                    try:
                        font = ImageFont.truetype(font_path, font_size)
                        break
                    except:
                        continue

            if not font:
                # Use default font as fallback
                font = ImageFont.load_default()
        except:
            font = ImageFont.load_default()

        try:
            # Get text bounding box for centering
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            # Calculate position to center text
            x = (size - text_width) // 2
            y = (size - text_height) // 2 - max(1, int(size * 0.05))  # Slight upward adjustment

            # Draw text with glow effect (only for larger sizes)
            if size >= 64:
                # Draw glow layers
                for offset in [6, 4, 2]:
                    glow_color = (0, 149, 255, 30)  # Semi-transparent cyan
                    for dx in [-offset, 0, offset]:
                        for dy in [-offset, 0, offset]:
                            draw.text((x+dx, y+dy), text, font=font, fill=glow_color)

            # Draw main text
            draw.text((x, y), text, font=font, fill=text_color)
        except:
            # If text rendering fails, just draw a simple MM indicator
            # Draw two cyan squares for M M
            block_size = max(2, size // 6)
            spacing = max(1, size // 10)
            start_x = (size - (block_size * 2 + spacing)) // 2
            start_y = (size - block_size) // 2

            # Left M
            draw.rectangle([start_x, start_y, start_x + block_size, start_y + block_size],
                          fill=text_color)
            # Right M
            draw.rectangle([start_x + block_size + spacing, start_y,
                           start_x + block_size * 2 + spacing, start_y + block_size],
                          fill=text_color)

    else:
        # For very small icons, just add a simple cyan accent
        text_color = (0, 149, 255, 255)
        # Draw small MM indicator blocks
        if size == 16:
            draw.rectangle([4, 6, 6, 10], fill=text_color)
            draw.rectangle([9, 6, 11, 10], fill=text_color)
        else:  # size < 32
            block_size = max(2, size // 8)
            margin = max(1, size // 4)
            draw.rectangle([margin, margin, margin + block_size, size - margin], fill=text_color)
            draw.rectangle([size - margin - block_size, margin, size - margin, size - margin], fill=text_color)

    # Add corner accents (only for larger icons)
    if size >= 64:
        accent_color = (0, 149, 255, 128)  # Semi-transparent cyan
        accent_width = max(1, size // 170)
        accent_length = max(3, int(size * 0.08))

        # Top-left corner
        draw.line([(padding, padding), (padding + accent_length, padding)], fill=accent_color, width=accent_width)
        draw.line([(padding, padding), (padding, padding + accent_length)], fill=accent_color, width=accent_width)

        # Top-right corner
        draw.line([(size - padding - accent_length, padding), (size - padding, padding)], fill=accent_color, width=accent_width)
        draw.line([(size - padding, padding), (size - padding, padding + accent_length)], fill=accent_color, width=accent_width)

        # Bottom-left corner
        draw.line([(padding, size - padding - accent_length), (padding, size - padding)], fill=accent_color, width=accent_width)
        draw.line([(padding, size - padding), (padding + accent_length, size - padding)], fill=accent_color, width=accent_width)

        # Bottom-right corner
        draw.line([(size - padding - accent_length, size - padding), (size - padding, size - padding)], fill=accent_color, width=accent_width)
        draw.line([(size - padding, size - padding - accent_length), (size - padding, size - padding)], fill=accent_color, width=accent_width)

    return img

def generate_all_icons():
    """Generate all platform-specific icon files"""
    project_dir = get_project_dir()
    static_dir = project_dir / "static"

    print("Generating Mesh Master MM icons...")
    print("")

    try:
        # Generate base PNG (512x512)
        png_path = static_dir / "mesh-master-icon.png"
        img = create_mm_icon(512)
        img.save(png_path, 'PNG')
        print(f"✓ Created {png_path.name} (512x512)")

        # Generate ICO (Windows) with multiple sizes
        ico_path = static_dir / "mesh-master-icon.ico"
        sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
        ico_images = []
        for size in sizes:
            ico_img = create_mm_icon(size[0])
            ico_images.append(ico_img)

        ico_images[0].save(ico_path, format='ICO', sizes=sizes, append_images=ico_images[1:])
        print(f"✓ Created {ico_path.name} (multi-size ICO)")

        # Generate ICNS (macOS) - create iconset directory
        icns_path = static_dir / "mesh-master-icon.icns"
        iconset_dir = static_dir / "mesh-master.iconset"
        iconset_dir.mkdir(exist_ok=True)

        # Generate required sizes for macOS
        mac_sizes = [
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

        for size, filename in mac_sizes:
            mac_img = create_mm_icon(size) if size <= 512 else img.resize((size, size), Image.Resampling.LANCZOS)
            mac_img.save(iconset_dir / filename, 'PNG')

        # Try to convert to ICNS if on macOS
        import platform
        if platform.system() == "Darwin":
            import subprocess
            try:
                subprocess.run(['iconutil', '-c', 'icns', str(iconset_dir), '-o', str(icns_path)], check=True)
                print(f"✓ Created {icns_path.name} (macOS icon)")

                # Clean up iconset directory
                import shutil
                shutil.rmtree(iconset_dir)
            except subprocess.CalledProcessError:
                print(f"⚠ Could not create ICNS (iconutil failed)")
                print(f"  Iconset directory kept: {iconset_dir}")
        else:
            print(f"⚠ Skipping ICNS creation (iconutil only available on macOS)")
            print(f"  Created iconset directory: {iconset_dir}")

        print("")
        print("========================================")
        print("  MM Icon Generation Complete!")
        print("========================================")
        print("")
        print("Generated files:")
        print(f"  • {png_path.name} - Linux/general use")
        print(f"  • {ico_path.name} - Windows shortcuts")
        if icns_path.exists():
            print(f"  • {icns_path.name} - macOS apps")
        print("")
        print("The icons feature a dark background with")
        print("bright cyan 'MM' text for Mesh Master.")
        print("")

        return True

    except Exception as e:
        print(f"✗ Error generating icons: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = generate_all_icons()
    sys.exit(0 if success else 1)