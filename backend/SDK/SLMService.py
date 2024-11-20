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

    cdll.LoadLibrary("ImageGen.dll")
    image_lib = CDLL("ImageGen.dll")

    # void Destruct_HologramGenerator()
    image_lib.Destruct_HologramGenerator.argtypes = []
    image_lib.Destruct_HologramGenerator.restype = c_void_p

    image_lib.Initialize_HologramGenerator.argtypes = [c_int, c_int, c_int, c_int, c_int]
    image_lib.Initialize_HologramGenerator.restype = c_int

    image_lib.CalculateAffinePolynomials.argtypes = [c_int] * 12
    image_lib.CalculateAffinePolynomials.restype = c_int

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

   
    # initalize hologram generator
    is_hologram_generator_initialized = image_lib.Initialize_HologramGenerator(1920, 1152, 8, 20, 0)

    print("Hologram generator initialized", is_hologram_generator_initialized)


    image_lib.CalculateAffinePolynomials(
                10, 10, 10, 10,
                -10, -10, -10, -10,
                10, -10, 10, -10)
    
    print("Affine polynomials calculated")


    for _ in range(100):

        hologram_image_1 = np.zeros([width * height * Bytes], np.uint8, 'C')
        WFC = np.zeros([width * height * Bytes], np.uint8, 'C')
   
        n = 10
        x_array = np.random.uniform(0, width, n).astype(np.float32)
        y_array = np.random.uniform(0, height, n).astype(np.float32)
        z_array = np.zeros(n, dtype=np.float32)
        intensity_array = np.ones(n, dtype=np.float32)
        
        ApplyAffine = 1

        
        # generate and store it in ImageHologram
        print("Generating hologram")
        
        start_time = time.time()
        


        image_lib.Generate_Hologram(
                hologram_image_1.ctypes.data_as(POINTER(c_ubyte)),
                WFC.ctypes.data_as(POINTER(c_float)),
                x_array.ctypes.data_as(POINTER(c_float)),
                y_array.ctypes.data_as(POINTER(c_float)),
                z_array.ctypes.data_as(POINTER(c_float)),
                intensity_array.ctypes.data_as(POINTER(c_float)),
                len(x_array), 1)
        # convert it to 2D array (image)
        hologram_image_1 = hologram_image_1.reshape([height, width, Bytes])

        print("Time taken to generate hologram:", time.time() - start_time)

        time.sleep(0.1)

        
        
    print("Done")

       




