import sys
import threading
from typing import Optional
from queue import Queue
import cv2
from vmbpy import *
from . import AbstractCamera
import glob
import time
import os


IMAGE_EXTENSIONS = ['.tif', '.tiff', '.png', '.jpg', '.jpeg', ".bmp"]
COMMENT = "Virtual Camera 2, Stream images from folder"
IS_REAL = False


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

        self.stop_event = threading.Event()
        self.thread = None
    
    
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
        print('/// Folder Streamer for Images ///')
        print('///////////////////////////////////////////////////\n')

    def start_streaming(self):
        self.print_preamble()

        # get all the images in the folder
        print("The path is:", self.image_source_path, flush=True)
        images = [f for f in os.listdir(self.image_source_path) if f.endswith(tuple(IMAGE_EXTENSIONS))]
        print("Images found:", len(images))

        # extract the content between last _ and first . and extract the number
        images = sorted(images, key=lambda x: int(x.split('_')[-1].split('.')[0]))

        

      
        image_id = 0

        self.stop_event.clear()

        
        
        while self.stop_event.is_set() == False:
            
            # serve the images in the folder
            image = cv2.imread(os.path.join(self.image_source_path, images[image_id]))
            self.current_frame = image
            

            _start_time = time.time()
            if self.on_update:
                self.on_update(image_id, image)
                image_id += 1

            if image_id >= len(images):
                image_id = 0

            delta_time = time.time() - _start_time
            self.stop_event.wait(max(0.001, self.wait_time - delta_time))
            

        print("6")
        

    def start(self):
        self.stop_event.clear()
        self.thread = threading.Thread(target=self.start_streaming)
        self.thread.start()


    def get_recent_frame(self):
        return self.current_frame

    def stop(self):
        self.stop_event.set()
        # if self.thread:
        #     self.thread.join()

        while self.thread.is_alive():
            self.thread.join(1.0)
            print("Waiting for thread to stop")

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
