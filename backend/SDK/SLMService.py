import os
import time
import numpy as np
import threading
from threading import Lock
import multiprocessing
from ctypes import *
from time import sleep
import signal
import cv2
if __name__ == '__main__':


   
    cdll.LoadLibrary("C:\\Program Files\\Meadowlark Optics\\Blink OverDrive Plus\\SDK\\ImageGen.dll")
    image_lib = CDLL("C:\\Program Files\\Meadowlark Optics\\Blink OverDrive Plus\\SDK\\ImageGen.dll")

  


  
   

    # void Destruct_HologramGenerator()
    image_lib.Destruct_HologramGenerator.argtypes = []
    image_lib.Destruct_HologramGenerator.restype = c_void_p



    # int Initialize_HologramGenerator(int width, int height, int depth, int iterations, int RGB);
    image_lib.Initialize_HologramGenerator.argtypes = [c_int, c_int, c_int, c_int, c_int]
    image_lib.Initialize_HologramGenerator.restype = c_int

    # int CalculateAffinePolynomials(int SLM_X_0, int SLM_Y_0, int CAM_X_0, int CAM_Y_0, int SLM_X_1, int SLM_Y_1, int CAM_X_1, int CAM_Y_1, int SLM_X_2, int SLM_Y_2, int CAM_X_2, int CAM_Y_2);
    image_lib.CalculateAffinePolynomials.argtypes = [ c_int] * 12   # 12 integers
    image_lib.CalculateAffinePolynomials.restype = c_int

    # int Generate_Hologram(unsigned char *Array, unsigned char* WFC, float *x_spots, float *y_spots, float *z_spots, float *I_spots, int N_spots, int ApplyAffine);
    image_lib.Generate_Hologram.argtypes = [POINTER(c_ubyte), POINTER(c_float), POINTER(c_float), POINTER(c_float), POINTER(c_float), POINTER(c_float), c_int, c_int]
    image_lib.Generate_Hologram.restype = c_void_p




    # some signal handling for error/user interrupt and following cleanup
    def cleanup(signum, frame):
        print("Exit command. Cleaning up resources...")

        if is_hologram_generator_initialized >0 :
            image_lib.Destruct_HologramGenerator()

       

    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)
    signal.signal(signal.SIGABRT, cleanup)
    signal.signal(signal.SIGSEGV, cleanup)
    signal.signal(signal.SIGILL, cleanup)

   


    height = 1152
    width = 1920
    depth = 8
    Bytes = depth // 8
    center_x = width // 2
    center_y = height // 2

 
    
    # Initialize image arrays
    hologram_image_1 = np.zeros([width * height * Bytes], np.uint8, 'C')
    WFC = np.zeros([width * height * Bytes], np.uint8, 'C') # blank wavefront correction image

 
   
    # initalize hologram generator
    is_hologram_generator_initialized = image_lib.Initialize_HologramGenerator(width, height, depth, 10, 0)
   
    n = 100
    x_spots = np.random.uniform(-400, 400, n).astype(np.float32)
    y_spots = np.random.uniform(-400, 400, n).astype(np.float32)
    z_spots = np.zeros(n, dtype=np.float32)
    I_spots = np.ones(n, dtype=np.float32)
    N_spots = n
    ApplyAffine = 0

    
    # generate and store it in ImageHologram
    print("Generating hologram")
    
    start_time = time.time()
    image_lib.Generate_Hologram(hologram_image_1.ctypes.data_as(POINTER(c_ubyte)), WFC.ctypes.data_as(POINTER(c_float)), x_spots.ctypes.data_as(POINTER(c_float)), y_spots.ctypes.data_as(POINTER(c_float)), z_spots.ctypes.data_as(POINTER(c_float)), I_spots.ctypes.data_as(POINTER(c_float)), N_spots, ApplyAffine)
    print("Time taken to generate hologram:", time.time() - start_time)

    # convert it to 2D array (image)
    hologram_image_1 = hologram_image_1.reshape([height, width, Bytes])
    # save the hologram image
    cv2.imwrite("hologram.png", hologram_image_1)
    
    
    
    print("Hologram generated")
    

    # delete the SDK
    cleanup(None, None)




