import sys
import threading
from typing import Optional
from queue import Queue
import cv2
from vmbpy import *
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time
from abc import ABC, abstractmethod



class AbstractCamera():

    def __init__(self, is_real=True, image_source_path = "", exposure_time = 0.0, gain = 0.0):
        self.is_real = is_real
        self.image_source_path = image_source_path

        self.exposure_time = exposure_time
        self.gain = gain
        self.comment = "Not set"


    def set_exposure_time(self, exposure_time):
        self.exposure_time = exposure_time


    def set_gain(self, gain):
        self.gain = gain


    def get_exposure_time(self):
        raise NotImplementedError("Subclass must implement this method")


    def get_gain(self):
        raise NotImplementedError("Subclass must implement this method")


 
    def is_real(self):
       raise NotImplementedError("Subclass must implement this method")

    def is_simulated(self):
        raise NotImplementedError("Subclass must implement this method")
    
    def set_image_source_path(self, image_source_path):
        raise NotImplementedError("Subclass must implement this method")
    @abstractmethod
    def set_comment(self, comment):
        raise NotImplementedError("Subclass must implement this method")
    @abstractmethod
    def get_comment(self):
        raise NotImplementedError("Subclass must implement this method")
        
    @abstractmethod
    def get_image_source_path(self):
        raise NotImplementedError("Subclass must implement this method")

    @abstractmethod
    def start_streaming(self):
        raise NotImplementedError("Subclass must implement this method")


    @abstractmethod
    def destroy(self):
        raise NotImplementedError("Subclass must implement this method")


    @abstractmethod
    def start(self):
        raise NotImplementedError("Subclass must implement this method")
    @abstractmethod
    def stop(self):
        raise NotImplementedError("Subclass must implement this method")
    @abstractmethod
    def get_recent_frame(self):
        raise NotImplementedError("Subclass must implement this method")


    @staticmethod
    def get_camera_details():
        raise NotImplementedError("Subclass must implement this method")


    @staticmethod
    def get_camera_instance():
        raise NotImplementedError("Subclass must implement this method")

    @abstractmethod
    def set_on_update_callback(self, callback):
        raise NotImplementedError("Subclass must implement this method")
        
    @abstractmethod
    def set_frame_rate(self, frame_rate):
        raise NotImplementedError("Subclass must implement this method")
