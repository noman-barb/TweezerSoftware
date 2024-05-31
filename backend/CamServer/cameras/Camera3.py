import sys
import threading
from typing import Optional
from queue import Queue
import cv2
from vmbpy import *
from . import AbstractCamera
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time
import os


IMAGE_EXTENSIONS = ['.tif', '.tiff', '.png', '.jpg', '.jpeg']
COMMENT = "Virtual Camera 1, folder watcher"
IS_REAL = False

class FolderHandler(FileSystemEventHandler):
    def __init__(self, camera):
        self.camera = camera
        self.last_change = -1

    def on_created(self, event):

        image_id  = 0
    
        if not event.is_directory and os.path.splitext(event.src_path)[1].lower() in IMAGE_EXTENSIONS:

            current_time_ms = int(round(time.time() * 1000))
            if current_time_ms - self.last_change > self.camera.wait_time:
                print(f"New image detected: {event.src_path}", flush=True)
                self.camera.last_path = event.src_path
                self.last_change = current_time_ms
                # wait for 100 ms
                # self.camera.current_frame = cv2.imread(event.src_path)
                # wait for the image to be completely written to disk

                count_fail = 1
                while True:
                    try:
                        self.camera.current_frame = cv2.imread(event.src_path)
                        if self.camera.current_frame is None:
                            print(f"Failed to read image {count_fail}", flush=True)
                            count_fail += 1
                        else:
                            print(f"Image read successfully", flush=True)
                            break
                            
                
                        if count_fail > 10:
                            print(f"Failed to read image finally {count_fail} times", flush=True)
                            break
                        time.sleep(0.01)
                    except:
                        print(f"Failed to read image {count_fail}", flush=True)
                        count_fail += 1
                        pass
                    time.sleep(0.01)
                self.camera.on_update(image_id, self.camera.current_frame)
                image_id += 1

 


class Camera(AbstractCamera.AbstractCamera):
    def __init__(self):
        # super().__init__()
        print("Camera3 instantiated")
        self.set_comment(COMMENT)
        self.last_path = None
        self.current_frame = None

        self.frame_rate = 10
        self.on_update = None
        self.wait_time = 1.0/self.frame_rate
        self.image_source_path = ""


    
    def get_comment(self):
        return self.comment

    def get_image_source_path(self):
        return self.image_source_path

        
    def set_frame_rate(self, frame_rate):
        self.frame_rate = frame_rate
        self.wait_time = 1.0/self.frame_rate

    
    def set_on_update_callback(self, on_update):
        self.on_update = on_update



    def set_comment(self, comment):
        self.comment = comment

    def set_image_source_path(self, image_source_path):
        print("Setting image source path to", image_source_path)
        self.image_source_path = image_source_path

    def print_preamble(self):
        print('///////////////////////////////////////////////////')
        print('/// Folder Watcher for Images ///')
        print('///////////////////////////////////////////////////\n')

    def startWatching(self):
        self.print_preamble()
    
        print("The path to watch is:", self.image_source_path, flush=True)
        self.event_handler = FolderHandler(self)
        self.observer = Observer()
        self.observer.schedule(self.event_handler, self.image_source_path, recursive=False)
        self.observer.start()
        

    def start(self):
        self.startWatching()


    def get_recent_frame(self):
        return self.current_frame

    def stop(self):
        self.observer.stop()
        self.observer.join()
        

    def destroy(self):
        self.stop()
        del self

    @staticmethod
    def get_camera_details():
        return {
            "name": "Camera3",
            "comment": COMMENT,
            "is_real": IS_REAL
        }

    @staticmethod
    def get_camera_instance():
        return Camera()

if __name__ == "__main__":
    pass
    # camera = Camera("C:/Users/Admin/Desktop/test_folder/")
    # camera.start()

    # try:
    #     while True:
    #         frame = camera.get_recent_frame()
    #         if frame is not None:
    #             # Display the frame or process it as needed
    #             cv2.imshow('Latest Image', frame)
    #             if cv2.waitKey(1) & 0xFF == ord('q'):
    #                 break
    # except KeyboardInterrupt:
    #     pass
    # finally:
    #     camera.stop()
    #     camera.destroy()
    #     cv2.destroyAllWindows()
