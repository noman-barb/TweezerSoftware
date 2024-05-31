import sys
import threading
from typing import Optional
from queue import Queue
import cv2
from vmbpy import *
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time
# from . import AbstractCamera


# All frames will either be recorded in this format, or transformed to it before being displayed
opencv_display_format = PixelFormat.Bgr8

QUEUE_SIZE = 10
BUFFER_SIZE = 10
CAM_ID = 0
COMMENT = "Allied Vision Camera 1, Lieca Microscope, side port"
IS_REAL = True

class Handler:
    def __init__(self):
        self.display_queue = Queue(QUEUE_SIZE)

    def get_image(self):
        return self.display_queue.get(True)

    def __call__(self, cam: Camera, stream: Stream, frame: Frame):
        if frame.get_status() == FrameStatus.Complete:
            #print('{} acquired {}'.format(cam, frame), flush=True)

            # Convert frame if it is not already the correct format
            if frame.get_pixel_format() == opencv_display_format:
                display = frame
            else:
                # This creates a copy of the frame. The original `frame` object can be requeued
                # safely while `display` is used
                display = frame.convert_pixel_format(opencv_display_format)

            self.display_queue.put(display.as_opencv_image(), True)

        cam.queue_frame(frame)

class Camera():
    def __init__(self):
        self.is_real = IS_REAL
        # super().__init__( is_real=self.is_real)
        print("Camera1 instantiated")
        self.set_comment(COMMENT)
        self.set_image_source_path("")
        self.stop_event = threading.Event()
        self.thread = None
        self.current_frame = None
        self.frame_rate = 10
        self.on_update = None
        self.wait_time = 1.0/self.frame_rate



    def set_comment(self, comment):
        self.comment = comment

    def set_image_source_path(self, image_source_path):
        self.image_source_path = image_source_path
    
    def set_frame_rate(self, frame_rate):
        self.frame_rate = frame_rate
        self.wait_time = 1.0/self.frame_rate

    
    def set_on_update_callback(self, on_update):
        self.on_update = on_update

    def print_preamble(self):
        print('///////////////////////////////////////////////////')
        print('/// VmbPy Asynchronous Grab Allied Vision Camera 1 ///')
        print('///////////////////////////////////////////////////\n')

    def get_camera(self, camera_id) -> Camera:
        with VmbSystem.get_instance() as vmb:
            cams = vmb.get_all_cameras()
            if not cams:
                abort('No Cameras accessible. Abort.')
            return cams[camera_id]

    def setup_camera(self, cam):
        # TODO set exposure time and gain
        pass

    def setup_pixel_format(self, cam):
        # Query available pixel formats. Prefer color formats over monochrome formats
        cam_formats = cam.get_pixel_formats()
        cam_color_formats = intersect_pixel_formats(cam_formats, COLOR_PIXEL_FORMATS)
        convertible_color_formats = tuple(f for f in cam_color_formats
                                          if opencv_display_format in f.get_convertible_formats())

        cam_mono_formats = intersect_pixel_formats(cam_formats, MONO_PIXEL_FORMATS)
        convertible_mono_formats = tuple(f for f in cam_mono_formats
                                          if opencv_display_format in f.get_convertible_formats())

        # if OpenCV compatible color format is supported directly, use that
        if opencv_display_format in cam_formats:
            cam.set_pixel_format(opencv_display_format)

        # else if existing color format can be converted to OpenCV format do that
        elif convertible_color_formats:
            cam.set_pixel_format(convertible_color_formats[0])

        # fall back to a mono format that can be converted
        elif convertible_mono_formats:
            cam.set_pixel_format(convertible_mono_formats[0])

        else:
            abort('Camera does not support an OpenCV compatible format. Abort.')

    def startStreaming(self):
        self.print_preamble()
        image_id = 0
        with VmbSystem.get_instance():
            with self.get_camera(CAM_ID) as cam:
                # setup general camera settings and the pixel format in which frames are recorded
                self.setup_camera(cam)
                self.setup_pixel_format(cam)
                handler = Handler()

                try:
                    # Start Streaming with a custom a buffer of 10 Frames (defaults to 5)
                    cam.start_streaming(handler=handler, buffer_count=BUFFER_SIZE)

                    while not self.stop_event.is_set():
                      
                        display = handler.get_image()
                        self.current_frame = display
                        self.on_update(image_id, display)
                        self.stop_event.wait(self.wait_time)
                        image_id += 1

                    print("Cancel request by user")
                    return
                        

                finally:

                    print("Stopping camera")
                    cam.stop_streaming()
                    print("Camera stopped")
                    # release all resources
                   

            

    def start(self):
        self.stop_event.clear()
        self.thread = threading.Thread(target=self.startStreaming)
        self.thread.start()

    def get_recent_frame(self) -> Optional:
    
        return self.current_frame

    def stop(self):
        self.stop_event.set()
        if self.thread:
            self.thread.join()



    def destroy(self):
        print("Camera1 destroyed")
        self.stop()
        print("Camera1 stopped")
        # destroy this class
        del self

    @staticmethod
    def get_camera_details():
        return {
            "name": "Camera1",
            "comment": COMMENT,
            "is_real": IS_REAL
        }

    @staticmethod
    def get_camera_instance():
        return Camera()

    

if __name__ == "__main__":
    

    def on_update_callback(image_id, frame):
        print(f"Frame {image_id} received")

    for i in range(4):
        print("Camera1 test")
        cam = Camera()
        cam.set_frame_rate(1)
        cam.set_on_update_callback(on_update_callback)
        cam.start()
        time.sleep(5)
        cam.stop()