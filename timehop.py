import os
import exifread
from datetime import datetime
from PIL import Image
import warnings
import shutil
import time

# Increase the maximum image size to avoid DecompressionBombWarning
warnings.simplefilter("ignore", Image.DecompressionBombWarning)

def is_valid_image(file_path):
    try:
        Image.open(file_path).close()
        return True
    except (IOError, SyntaxError) as e:
        return False

def get_photos_taken_on_date(directory, target_date):
    photos_taken_on_date = []
    
    for root, _, files in os.walk(directory):
        for file in files:
            _, file_ext = os.path.splitext(file)
            if file_ext.lower() == '.png':
                continue

            if file_ext.lower() in ('.jpg', '.jpeg'):
                file_path = os.path.join(root, file)
                if not is_valid_image(file_path):
                    print(f"Invalid image format: {file_path}")
                    continue

                try:
                    with open(file_path, 'rb') as f:
                        tags = exifread.process_file(f)
                        if 'EXIF DateTimeOriginal' in tags:
                            photo_date_str = str(tags['EXIF DateTimeOriginal'])
                            photo_date = parse_exif_date(photo_date_str)
                            if photo_date and photo_date.month == target_date.month and photo_date.day == target_date.day:
                                photos_taken_on_date.append((photo_date, file_path))
                except Exception as e:
                    print(f"Error processing {file_path}: {str(e)}")
    
    return photos_taken_on_date

def parse_exif_date(date_string):
    formats_to_try = ["%Y:%m:%d %H:%M:%S.%f", "%Y:%m:%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"]
    for fmt in formats_to_try:
        try:
            return datetime.strptime(date_string, fmt)
        except ValueError:
            continue
    return None

def copy_images_to_directory(photos_info, dest_directory):
    if not os.path.exists(dest_directory):
        os.makedirs(dest_directory)
    else:
        # Clear previous execution's image files from the directory
        for filename in os.listdir(dest_directory):
            file_path = os.path.join(dest_directory, filename)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(f"Error clearing previous image file: {str(e)}")
    
    for _, photo_path in photos_info:
        shutil.copy(photo_path, dest_directory)

def generate_html(photos_info, copied_images_dir):
    html = "<html><head><title>Photos Taken on Today's Date</title></head><body><h1>Photos Taken on Today's Date</h1><ul>"
    for photo_date, photo_path in photos_info:
        photo_name = os.path.basename(photo_path)
        copied_image_path = os.path.join(copied_images_dir, photo_name)
        html += f"<li><strong>Date:</strong> {photo_date.strftime('%Y-%m-%d %H:%M:%S')}<br><img src='{copied_image_path}' width='400'></li>"
    html += "</ul></body></html>"
    return html

if __name__ == "__main__":
    start_time = time.time()

    target_date = datetime.today().replace(year=1900)  # Set the target date to today's date, but with year 1900
    directory = "/srv/backups/iPhone_Photos"  # Use the specified directory path
    photos_info = get_photos_taken_on_date(directory, target_date)

    if photos_info:
        copied_images_dir = "copied_images"
        copy_images_to_directory(photos_info, copied_images_dir)
        html_content = generate_html(photos_info, copied_images_dir)

        today_date_str = datetime.today().strftime('%Y%m%d')
        html_filename = f"{today_date_str}_photos_summary.html"
        
        with open(html_filename, "w") as html_file:
            html_file.write(html_content)

        end_time = time.time()
        total_time = end_time - start_time

        print(f"HTML file '{html_filename}' generated successfully!")
        print(f"Total execution time: {total_time:.2f} seconds")
    else:
        print("No photos taken on today's date in any previous year were found.")
