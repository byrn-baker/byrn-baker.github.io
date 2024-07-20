import os
import subprocess
import sys

def convert_images(directory):
    for filename in os.listdir(directory):
        if filename.endswith(".png") or filename.endswith(".jpg"):
            image_file = os.path.join(directory, filename)
            webp_file = os.path.splitext(image_file)[0] + '.webp'
            subprocess.run(['cwebp', image_file, '-o', webp_file])
            os.remove(image_file)  # delete the .png/.jpg file after conversion

def main():
    if len(sys.argv) == 2:
        directory = sys.argv[1]
        convert_images(directory)
    elif len(sys.argv) > 2:
        print("Usage: python3 cwebp.py /path/to/your/directory")
        sys.exit(1)
    else:
        print("Error: No directory specified.")
        sys.exit(1)

if __name__ == "__main__":
    main()