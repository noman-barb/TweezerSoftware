import cv2
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time

class ImageHandler(FileSystemEventHandler):
    def on_created(self, event):
        # Check if the created file is an image
        if event.is_directory:
            return
        
        # Get the file extension
        _, file_extension = os.path.splitext(event.src_path)
        if file_extension.lower() in ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.tif']:
            print(f"New image detected: {event.src_path}")

            # extract the number between last undescore and last dot
            image_number = event.src_path.split('_')[-1].split('.')[0]
            # convert to int
            image_number = int(image_number)

            if image_number % 20 == 0:
                self.show_image(event.src_path)

    def show_image(self, image_path):
        # Read the image using OpenCV
        image = cv2.imread(image_path)
        # reduce to 0.5 size
        image = cv2.resize(image, (0, 0), fx=0.5, fy=0.5)
        if image is not None:
            cv2.imshow("New Image", image)
            # wait for 100 ms
            cv2.waitKey(100)
            # cv2.destroyAllWindows()
        else:
            print(f"Failed to load image: {image_path}")

def main(folder_to_watch):
    event_handler = ImageHandler()
    observer = Observer()
    observer.schedule(event_handler, folder_to_watch, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)  # Keep the script running
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    folder_to_watch = r"\\10.0.63.112\d\Noman_temp\melting_exps\002\images"  # Change to your folder path
    main(folder_to_watch)
