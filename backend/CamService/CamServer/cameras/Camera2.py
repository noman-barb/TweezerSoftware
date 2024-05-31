
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




QUEUE_SIZE = 10
BUFFER_SIZE = 10
CAM_ID = 0
COMMENT = "Webcam"
IS_REAL = True

class Handler:
    def __init__(self):
        self.display_queue = Queue(QUEUE_SIZE)

    def get_image(self):
        return self.display_queue.get(True)

    def __call__(self, frame):
        if frame is not None:
            self.display_queue.put(frame, True)

class Camera(AbstractCamera.AbstractCamera):
    def __init__(self):
        self.is_real = IS_REAL
        self.cap = cv2.VideoCapture(CAM_ID)
        if not self.cap.isOpened():
            raise ValueError("Webcam could not be opened")
        print("Webcam instantiated")
        self.set_comment(COMMENT)
        self.stop_event = threading.Event()
        self.thread = None
        self.current_frame = None
        self.frame_rate = 10
        self.on_update = None
        self.wait_time = 1.0/self.frame_rate


    
    def set_frame_rate(self, frame_rate):
        self.frame_rate = frame_rate
        self.wait_time = 1.0/self.frame_rate

    
    def set_on_update_callback(self, on_update):
        self.on_update = on_update

    def set_comment(self, comment):
        self.comment = comment

    def get_comment(self):
        return self.comment

    def get_image_source_path(self):
        return self.image_source_path

    def set_image_source_path(self, image_source_path):
        self.image_source_path = image_source_path

        

    def print_preamble(self):
        print('///////////////////////////////////////////////////')
        print('/// OpenCV Webcam Asynchronous Grab ///')
        print('///////////////////////////////////////////////////\n')

    def start_streaming(self):
        self.print_preamble()
        handler = Handler()

        _start_time = time.time()
        _delta_time = 0

        # unset set flag
        self.stop_event.clear()

        try:
            image_id = 0
            
            while not self.stop_event.is_set():
           
                ret, frame = self.cap.read()
              
                if ret:
                    handler(frame)
                    display = handler.get_image()
                    self.current_frame = display
                    _start_time = time.time()
                    if self.on_update:
                        
                        self.on_update(image_id, display)
                        image_id += 1

                    _delta_time = time.time() - _start_time
                    
                else:
                    print("Failed to grab frame")

               

                self.stop_event.wait( max(0.01, self.wait_time - _delta_time) )
                

        except Exception as e:
            print(e)
        finally:
            print(5)
            self.cap.release()
            cv2.destroyAllWindows()

    def start(self):
        self.stop_event.clear()
        self.thread = threading.Thread(target=self.start_streaming)
        self.thread.start()

    def get_recent_frame(self) -> Optional:
        return self.current_frame


    def stop(self):
        self.stop_event.set()
        if self.thread:
            self.thread.join()

    def destroy(self):
        self.stop()
        del self


    @staticmethod
    def get_camera_details():
        return {
            "name": "Webcam",
            "comment": COMMENT,
            "is_real": IS_REAL
        }

    @staticmethod
    def get_camera_instance():
        return Camera()

# Usage example
if __name__ == "__main__":
    pass
    # cam = Camera()
    # cam.start()
    # try:
    #     while True:
    #         frame = cam.get_recent_frame()
    #         if frame is not None:
    #             cv2.imshow("Webcam", frame)
    #             if cv2.waitKey(1) & 0xFF == ord('q'):
    #                 break
    # finally:
    #     cam.stop()
    #     cam.destroy()
    #     cv2.destroyAllWindows()
