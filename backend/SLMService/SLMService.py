from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from websockets.exceptions import ConnectionClosed
import signal
from pydantic import BaseModel
import os
import time
import numpy as np
import threading
import asyncio
from threading import Lock
from fastapi.middleware.cors import CORSMiddleware
from collections import deque
import cv2
from fastapi.responses import FileResponse
import multiprocessing
from ctypes import *
from time import sleep


# def update_affine(shared_dict, lock, key, value):
#     with lock:
#         shared_dict['affine'][key] = value
#         shared_dict['affine']['last_updated'] = time.time()

# def update_points(shared_dict, lock, x_array, y_array, intensity_array):
#     with lock:
#         shared_dict['points']['x_array'] = x_array
#         shared_dict['points']['y_array'] = y_array
#         shared_dict['points']['intensity_array'] = intensity_array
#         shared_dict['points']['last_updated'] = time.time()

# def update_test(shared_dict, lock, value):
#     with lock:
#         shared_dict['test']['value'] = value
#         shared_dict['test']['last_updated'] = time.time()

# def worker(shared_dict, lock):
#     while True:
#         with lock:
#             affine_last_updated = shared_dict['affine']['last_updated']
#             points_last_updated = shared_dict['points']['last_updated']
#             test_last_updated = shared_dict['test']['last_updated']
        
#         current_time = time.time()
        
#         if affine_last_updated != current_time:
#             print("Affine updated:", affine_last_updated)
        
#         if points_last_updated != current_time:
#             print("Points updated:", points_last_updated)
        
#         if test_last_updated != current_time:
#             print("Test updated:", test_last_updated)
        
#         time.sleep(1)  # Sleep to prevent busy waiting

# if __name__ == "__main__":
#     manager = multiprocessing.Manager()
#     shared_dict = manager.dict({
#         "affine": manager.dict({
#             "last_updated": time.time(),
#             "SLM_X_0": 200, "SLM_Y_0": 200, "CAM_X_0": 200, "CAM_Y_0": 200,
#             "SLM_X_1": 300, "SLM_Y_1": 300, "CAM_X_1": 300, "CAM_Y_1": 300,
#             "SLM_X_2": 100, "SLM_Y_2": 100, "CAM_X_2": 100, "CAM_Y_2": 100
#         }),
#         "points": manager.dict({
#             "last_updated": time.time(),
#             "x_array": [], "y_array": [], "intensity_array": []
#         }),
#         "fresnel_lens": manager.dict({
#             "last_updated": time.time(),
#             "center_x": 255,
#             "center_y": 255,
#             "radius": 20,
#             "power": 1,
#             "cylinderical": False, 
#             "horizontal": False,

#         }),
#         "test": manager.dict({
#             "last_updated": time.time(),
#             "value": ""
#         })
#     })
    
#     lock = manager.Lock()


#     p = multiprocessing.Process(target=worker, args=(shared_dict, lock))
#     p.daemon = True
#     p.start()


#     # Simulate updates in the main process
#     time.sleep(5)
#     update_affine(shared_dict, lock, "SLM_X_0", 10)
#     time.sleep(5)
#     update_points(shared_dict, lock, [1, 2, 3], [4, 5, 6], [7, 8, 9])
#     time.sleep(5)
#     update_test(shared_dict, lock, "test_value")

#     pool.close()
#     pool.join()



if __name__ == '__main__':


    # Load the DLLs
    cdll.LoadLibrary("C:\\Program Files\\Meadowlark Optics\\Blink OverDrive Plus\\SDK\\Blink_C_wrapper.dll")
    slm_lib = CDLL("C:\\Program Files\\Meadowlark Optics\\Blink OverDrive Plus\\SDK\\Blink_C_wrapper.dll")

    cdll.LoadLibrary("C:\\Program Files\\Meadowlark Optics\\Blink OverDrive Plus\\SDK\\ImageGen.dll")
    image_lib = CDLL("C:\\Program Files\\Meadowlark Optics\\Blink OverDrive Plus\\SDK\\ImageGen.dll")

    # Basic parameters for calling Create_SDK
    bit_depth = c_uint(12)
    num_boards_found = c_uint(0)
    constructed_okay = c_uint(-1)
    is_nematic_type = c_bool(True)
    RAM_write_enable = c_bool(True)
    use_GPU = c_bool(True)
    max_transients = c_uint(20)
    board_number = c_uint(1)
    wait_For_Trigger = c_uint(0)
    flip_immediate = c_uint(0)  # only supported on the 1024
    timeout_ms = c_uint(5000)
    center_x = c_float(256)
    center_y = c_float(256)
    VortexCharge = c_uint(3)
    fork = c_uint(0)
    RGB = c_uint(0)


    # Output pulse settings
    OutputPulseImageFlip = c_uint(0)
    OutputPulseImageRefresh = c_uint(0)  # only supported on 1920x1152, FW rev 1.8


    # some global variables for SLM stages
    is_hologram_generator_initialized = 0


    # set up function prototypes

    # void Create_SDK (unsigned int SLM_bit_depth, unsigned int* n_boards_found, int *constructed_ok, 
    # int is_nematic_type, int RAM_write_enable, int use_GPU_if_available, i
    # nt max_transient_frames, char* static_regional_lut_file);
    slm_lib.Create_SDK.argtypes = [c_uint, POINTER(c_uint), POINTER(c_uint), c_bool, c_bool, c_bool, c_uint, c_uint]
    slm_lib.Create_SDK.restype = c_void_p

    # int Load_LUT_file (int board, char* LUT_file);
    slm_lib.Load_LUT_file.argtypes = [c_uint, c_char_p]
    slm_lib.Load_LUT_file.restype = c_int

    # int Get_image_height (int board);
    slm_lib.Get_image_height.argtypes = [c_uint]
    slm_lib.Get_image_height.restype = c_uint

    # int Get_image_width (int board);
    slm_lib.Get_image_width.argtypes = [c_uint]
    slm_lib.Get_image_width.restype = c_uint

    # no idea
    # guess from supplied code: int Get_image_depth (int board);
    slm_lib.Get_image_depth.argtypes = [c_uint]
    slm_lib.Get_image_depth.restype = c_uint

    # int Write_image (int board, unsigned char* image, unsigned int image_size, int
    # wait_for_trigger, int output_pulse_image_flip, int output_pulse_image_refresh,
    # unsigned int trigger_timeout_ms);
    slm_lib.Write_image.argtypes = [c_uint, POINTER(c_ubyte), c_uint, c_uint, c_uint, c_uint, c_uint, c_uint]
    slm_lib.Write_image.restype = c_int

    # int ImageWriteComplete (int board, unsigned int trigger_timeout_ms);
    slm_lib.ImageWriteComplete.argtypes = [c_uint, c_uint]
    slm_lib.ImageWriteComplete.restype = c_int

    # void Destruct_HologramGenerator()
    image_lib.Destruct_HologramGenerator.argtypes = []
    image_lib.Destruct_HologramGenerator.restype = c_void_p

    # void Delete_SDK();
    slm_lib.Delete_SDK.argtypes = []
    slm_lib.Delete_SDK.restype = c_void_p

    # int Initialize_HologramGenerator(int width, int height, int depth, int iterations, int RGB);
    image_lib.Initialize_HologramGenerator.argtypes = [c_int, c_int, c_int, c_int, c_int]
    image_lib.Initialize_HologramGenerator.restype = c_int

    # int CalculateAffinePolynomials(int SLM_X_0, int SLM_Y_0, int CAM_X_0, int CAM_Y_0, int SLM_X_1, int SLM_Y_1, int CAM_X_1, int CAM_Y_1, int SLM_X_2, int SLM_Y_2, int CAM_X_2, int CAM_Y_2);
    image_lib.CalculateAffinePolynomials.argtypes = [ c_int] * 12   # 12 integers
    image_lib.CalculateAffinePolynomials.restype = c_int

    # int Generate_Hologram(unsigned char *Array, unsigned char* WFC, float *x_spots, float *y_spots, float *z_spots, float *I_spots, int N_spots, int ApplyAffine);
    image_lib.Generate_Hologram.argtypes = [POINTER(c_ubyte), POINTER(c_float), POINTER(c_float), POINTER(c_float), POINTER(c_float), POINTER(c_float), c_int, c_int]
    image_lib.Generate_Hologram.restype = c_void_p


    # void Generate_LG(unsigned char* Array, int width, int height, int VortexCharge, int centerX, int center, bool fork);
    image_lib.Generate_LG.argtypes = [POINTER(c_ubyte), POINTER(c_ubyte), c_uint, c_uint, c_uint, c_uint, c_uint, c_uint, c_uint]
    image_lib.Generate_LG.restype = c_void_p


    # Call the Create_SDK constructor
    slm_lib.Create_SDK(bit_depth, byref(num_boards_found), byref(constructed_okay), is_nematic_type, RAM_write_enable, use_GPU, max_transients, 0)



    # some signal handling for error/user interrupt and following cleanup
    def cleanup(signum, frame):
        print("Exit command. Cleaning up resources...")

        if is_hologram_generator_initialized >0 :
            image_lib.Destruct_HologramGenerator()

        slm_lib.Delete_SDK()
        os._exit(0)

    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)
    signal.signal(signal.SIGABRT, cleanup)
    signal.signal(signal.SIGSEGV, cleanup)
    signal.signal(signal.SIGILL, cleanup)

    if constructed_okay.value == 0:
        print("Blink SDK did not construct successfully")
        exit(1)

    if num_boards_found.value <1:
        print("No SLM controller found")
        exit(1)



    print("Blink SDK was successfully constructed")
    print(f"Found {num_boards_found.value} SLM controller(s)")

    height = slm_lib.Get_image_height(board_number)
    width = slm_lib.Get_image_width(board_number)
    depth = slm_lib.Get_image_depth(board_number)
    Bytes = depth // 8
    center_x = width // 2
    center_y = height // 2

    print(f"Image width: {width}, Image height: {height}, Image depth: {depth}, Bytes per pixel: {Bytes}")

    # Load LUT file based the SLM LCD dimensions
    # lut_file = b"C:\\Program Files\\Meadowlark Optics\\Blink OverDrive Plus\\LUT Files\\1920x1152_linearVoltage.LUT"
    # calibrated
    lut_file = b"C:\Program Files\Meadowlark Optics\Blink OverDrive Plus\LUT Files\slm6336_at1064_PCIe.LUT"
    slm_lib.Load_LUT_file(board_number, lut_file)
    

    # Initialize image arrays
    hologram_image_1 = np.zeros([width * height * Bytes], np.uint8, 'C')
    hologram_image_2 = np.zeros([width * height * Bytes], np.uint8, 'C')
    WFC = np.zeros([width * height * Bytes], np.uint8, 'C') # blank wavefront correction image

 
    # Write a blank pattern to the SLM to start
    def write_image(image_array):
        retVal = slm_lib.Write_image(board_number, image_array.ctypes.data_as(POINTER(c_ubyte)), height * width * Bytes, wait_For_Trigger, flip_immediate, OutputPulseImageFlip, OutputPulseImageRefresh, timeout_ms)
        if retVal == -1:
            print("DMA Failed")
            slm_lib.Delete_SDK()
            exit(1)

    write_image(WFC)

    # initalize hologram generator
    is_hologram_generator_initialized = image_lib.Initialize_HologramGenerator(width, height, depth, 1000, 0)
    print("Hologram generator initialized:", is_hologram_generator_initialized)

    # generate hologram image for postion x= (-5, 0, 0) and (5, 0, 0) with intensity 1
    x_spots = np.array([-10, 10], dtype=np.float32)
    y_spots = np.array([0, 0], dtype=np.float32)
    z_spots = np.array([0, 0], dtype=np.float32)
    I_spots = np.array([1, 1], dtype=np.float32)
    N_spots = 2
    ApplyAffine = 0
    
    # generate and store it in ImageHologram
    print("Generating hologram")
    image_lib.Generate_Hologram(hologram_image_1.ctypes.data_as(POINTER(c_ubyte)), WFC.ctypes.data_as(POINTER(c_float)), x_spots.ctypes.data_as(POINTER(c_float)), y_spots.ctypes.data_as(POINTER(c_float)), z_spots.ctypes.data_as(POINTER(c_float)), I_spots.ctypes.data_as(POINTER(c_float)), N_spots, ApplyAffine)
    print("Hologram generated")
    # reshape the image to 2D
    hologram_1_reshaped_to_image = hologram_image_1.reshape((height, width, Bytes))
    # save the image
    cv2.imwrite("hologram1.png", hologram_1_reshaped_to_image)
    # swap x and y
    x_spots, y_spots = y_spots, x_spots
    # generate and store it in ImageHologram
    image_lib.Generate_Hologram(hologram_image_2.ctypes.data_as(POINTER(c_ubyte)), WFC.ctypes.data_as(POINTER(c_float)), x_spots.ctypes.data_as(POINTER(c_float)), y_spots.ctypes.data_as(POINTER(c_float)), z_spots.ctypes.data_as(POINTER(c_float)), I_spots.ctypes.data_as(POINTER(c_float)), N_spots, ApplyAffine)
    # hologram_reshaped_to_image = ImageHologram.reshape((height, width, Bytes))
    # save the image
    hologram_2_reshaped_to_image = hologram_image_2.reshape((height, width, Bytes))
    cv2.imwrite("hologram2.png", hologram_2_reshaped_to_image)
    
    
    
    # reshape the image to 2D
    # hologram_reshaped_to_image = ImageHologram.reshape((height, width, Bytes))
    # save the image
    # cv2.imwrite("hologram1.png", hologram_reshaped_to_image)

   
    ##################### works ###################################################################
    # VortexCharge = 1
    # image_lib.Generate_LG(ImageHologram.ctypes.data_as(POINTER(c_ubyte)), WFC.ctypes.data_as(POINTER(c_ubyte)), width, height, depth, VortexCharge, center_x, center_y, fork, RGB)
    # hologram_reshaped_to_image = ImageHologram.reshape((height, width, Bytes))
    # cv2.imwrite("hologram.png", hologram_reshaped_to_image)
    #################################################################################################




    while True:

        write_image(hologram_image_1)
        time.sleep(0.5)
        write_image(hologram_image_2)
        time.sleep(0.5)

        print("Hologram looped")

        
        
       

    # delete the SDK
    cleanup(None, None)




