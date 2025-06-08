#!/usr/bin/env python3
"""
Generate PNG icons from SVG using cairosvg
"""

import sys
import subprocess

def check_and_install_cairosvg():
    """Check if cairosvg is installed, if not, try to install it"""
    try:
        import cairosvg
        return True
    except ImportError:
        print("cairosvg is not installed. Trying to install...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "cairosvg"])
            print("cairosvg installed successfully!")
            return True
        except:
            print("Failed to install cairosvg automatically.")
            print("Please install it manually with: pip3 install cairosvg")
            return False

def generate_png_from_svg():
    """Generate PNG files from SVG"""
    if not check_and_install_cairosvg():
        return False
    
    import cairosvg
    
    sizes = [16, 48, 128]
    
    print("Generating PNG icons from icon.svg...")
    
    for size in sizes:
        input_file = "icon.svg"
        output_file = f"icon{size}.png"
        
        try:
            cairosvg.svg2png(
                url=input_file,
                write_to=output_file,
                output_width=size,
                output_height=size
            )
            print(f"✓ Created {output_file} ({size}x{size})")
        except Exception as e:
            print(f"✗ Failed to create {output_file}: {e}")
            return False
    
    print("\nAll icons generated successfully!")
    return True

if __name__ == "__main__":
    if not generate_png_from_svg():
        print("\nFalling back to placeholder generation...")
        # Run the placeholder script as fallback
        import subprocess
        subprocess.run([sys.executable, "generate_placeholders.py"])
