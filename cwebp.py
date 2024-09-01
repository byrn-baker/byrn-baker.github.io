import os
import subprocess
import sys

def convert_images(directory):
    for root, _, files in os.walk(directory):
        for filename in files:
            if filename.endswith(".png") or filename.endswith(".jpg"):
                image_file = os.path.join(root, filename)
                webp_file = os.path.splitext(image_file)[0] + '.webp'
                try:
                    # Run cwebp to convert the image
                    subprocess.run(['cwebp', image_file, '-o', webp_file], check=True)
                    os.remove(image_file)  # delete the .png/.jpg file after conversion
                    print(f"Converted {image_file} to {webp_file} and deleted the original.")
                except subprocess.CalledProcessError as e:
                    print(f"Error converting {image_file}: {e}")
                except OSError as e:
                    print(f"Error deleting {image_file}: {e}")

def main():
    if len(sys.argv) == 2:
        directory = sys.argv[1]
        if os.path.isdir(directory):
            convert_images(directory)
        else:
            print("Error: The specified path is not a directory.")
            sys.exit(1)
    elif len(sys.argv) > 2:
        print("Usage: python3 cwebp.py /path/to/your/directory")
        sys.exit(1)
    else:
        print("Error: No directory specified.")
        sys.exit(1)

if __name__ == "__main__":
    main()
