
from PIL import Image, ImageOps
import os

def invert_icon(filename, output_filename):
    try:
        path = os.path.join("assets", filename)
        img = Image.open(path).convert("RGBA")
        
        # Split channels
        r, g, b, a = img.split()
        
        # Invert RGB channels (black 0,0,0 -> white 255,255,255)
        # Since the icon is black, inverting it makes it white.
        r = r.point(lambda x: 255 - x)
        g = g.point(lambda x: 255 - x)
        b = b.point(lambda x: 255 - x)
        
        # Recombine with original alpha
        img_white = Image.merge("RGBA", (r, g, b, a))
        
        output_path = os.path.join("assets", output_filename)
        img_white.save(output_path)
        print(f"Created {output_path}")
    except Exception as e:
        print(f"Error processing {filename}: {e}")

if __name__ == "__main__":
    invert_icon("eye.png", "eye-white.png")
    invert_icon("eye-off.png", "eye-off-white.png")
