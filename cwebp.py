import os
import subprocess
import sys

def convert_png_to_webp(directory):
    for filename in os.listdir(directory):
        if filename.endswith(".png"):
            png_file = os.path.join(directory, filename)
            webp_file = os.path.splitext(png_file)[0] + '.webp'
            subprocess.run(['cwebp', png_file, '-o', webp_file])
            os.remove(png_file)  # delete the .png file after conversion

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 cwebp.py /path/to/your/directory")
        sys.exit(1)

    directory = sys.argv[1]
    convert_png_to_webp(directory)