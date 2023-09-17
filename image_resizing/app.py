import os
import cv2
from multiprocessing import Pool

# Function to resize an image
def resize_image(input_path, output_path, width=600, height=480, log_file=None):
    img_width = img.shape[1]
    img_height = img.shape[0]
    image_size = f"{img_width} X {img_height}"
    log_entry = f"{os.path.basename(input_path)}: {image_size}\n"
    if log_file:
        with open(log_file, "a") as f:
            f.write(log_entry)

    img = cv2.imread(input_path)
    if(img_width>600 or img_height>480):
        img = cv2.resize(img, (width, height)) #Resizing image function by OpenCV
    cv2.imwrite(output_path, img)

# Enter your input and output directories where images are there. You can also create output directory
# depending upon your OS
input_dir = "input_images/"
output_dir = "output_images/"
batch_size = 100  # Number of images in each batch (Batch processing for smaller RAM)
log_file_path = os.path.join(output_dir, "image_sizes.log")  # Path to the log file where I am outputting the log file

image_files = os.listdir(input_dir)
# List of image file paths, we are joining the file name to the directory name
image_paths = [os.path.join(input_dir, file) for file in image_files]

# For parallel processing. Multiprocessing library is used.
pool = Pool(processes=2)  # We are using 2 because problem states 2 vcpu

# Create batches and process the images
for i in range(0, len(image_paths), batch_size):
    batch = image_paths[i:i + batch_size]
    
    # Use the pool of processes to resize images in parallel
    for image_path in batch:
        output_path = os.path.join(output_dir, os.path.basename(image_path))
        pool.apply_async(resize_image, (image_path, output_path, log_file_path))
    
    print(f"Processed batch is stored in output directory")

# Close the pool and wait for all processes to finish
pool.close()
pool.join()

print("All images processed successfully.")
