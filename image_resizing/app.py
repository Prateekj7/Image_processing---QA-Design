import os
import cv2
import time
from multiprocessing import Pool

# Function to resize an image
def resize_image(input_path, output_path, width=600, height=480, log_file=None):
    img = cv2.imread(input_path)
    img_width = img.shape[1]
    img_height = img.shape[0]
    image_size = f"{img_width} X {img_height}"

    if(img_width>600 or img_height>480):
        img = cv2.resize(img, (width, height)) #Resizing image function by OpenCV
        cv2.imwrite(output_path, img)

if __name__ == '__main__':
    # Enter your input and output directories where images are there. You can also create output directory
    # depending upon your OS
    input_dir = "input_images/"
    output_dir = "output_images/"
    batch_size = 10  # Number of images in each batch (Batch processing for smaller RAM)
    # log_file_path = os.path.join(output_dir, "image_sizes.log")  # Path to the log file where I am outputting the log file

    # Remove all files if present in output directory
    files = os.listdir(output_dir)
    for f in files:
        file_path = os.path.join(output_dir,f)
        os.remove(file_path)

    image_files = os.listdir(input_dir)
    # List of image file paths, we are joining the file name to the directory name
    image_paths = [os.path.join(input_dir, file) for file in image_files]

    # For parallel processing. Multiprocessing library is used.
    pool = Pool(processes=2)  # We are using 2 because problem states 2 vcpu

    # Create batches and process the images
    init_time = time.time_ns()
    for i in range(0, len(image_paths), batch_size):
        batch = image_paths[i:i + batch_size]
        
        # Use the pool of processes to resize images in parallel
        for image_path in batch:
            output_path = os.path.join(output_dir, os.path.basename(image_path))
            pool.apply_async(resize_image, (image_path, output_path))
            # resize_image(image_path, output_path)
        
        print(f"Processed batch is stored in output directory")
    
    out_time = time.time_ns()
    print(out_time-init_time)

    # Close the pool and wait for all processes to finish
    pool.close() #Not take any further tasks
    pool.join() #wait for the pending tasks to complete

    print("All images processed successfully.")
