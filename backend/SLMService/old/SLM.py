# Example usage of Blink_C_wrapper.dll
# Meadowlark Optics Spatial Light Modulators
# September 12 2019
# fixed by noman
import os
import numpy
from ctypes import *
from time import sleep

# Load the DLLs
#
#
#
cdll.LoadLibrary("C:\\Program Files\\Meadowlark Optics\\Blink OverDrive Plus\\SDK\\Blink_C_wrapper.dll")
slm_lib = CDLL("C:\\Program Files\\Meadowlark Optics\\Blink OverDrive Plus\\SDK\\Blink_C_wrapper.dll")


#
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


# Function prototypes (optional but recommended for clarity)
slm_lib.Create_SDK.argtypes = [c_uint, POINTER(c_uint), POINTER(c_uint), c_bool, c_bool, c_bool, c_uint, c_uint]
slm_lib.Create_SDK.restype = c_void_p

slm_lib.Load_LUT_file.argtypes = [c_uint, c_char_p]
slm_lib.Load_LUT_file.restype = c_int

slm_lib.Get_image_height.argtypes = [c_uint]
slm_lib.Get_image_height.restype = c_uint

slm_lib.Get_image_width.argtypes = [c_uint]
slm_lib.Get_image_width.restype = c_uint

slm_lib.Get_image_depth.argtypes = [c_uint]
slm_lib.Get_image_depth.restype = c_uint

slm_lib.Write_image.argtypes = [c_uint, POINTER(c_ubyte), c_uint, c_uint, c_uint, c_uint, c_uint, c_uint]
slm_lib.Write_image.restype = c_int

slm_lib.ImageWriteComplete.argtypes = [c_uint, c_uint]
slm_lib.ImageWriteComplete.restype = c_int

slm_lib.Delete_SDK.argtypes = []
slm_lib.Delete_SDK.restype = c_void_p

image_lib.Generate_LG.argtypes = [POINTER(c_ubyte), POINTER(c_ubyte), c_uint, c_uint, c_uint, c_uint, c_float, c_float, c_uint, c_uint]
image_lib.Generate_LG.restype = c_int

# Call the Create_SDK constructor
slm_lib.Create_SDK(bit_depth, byref(num_boards_found), byref(constructed_okay), is_nematic_type, RAM_write_enable, use_GPU, max_transients, 0)

if constructed_okay.value == 0:
    print("Blink SDK did not construct successfully")
    exit(1)

if num_boards_found.value >= 1:
    print("Blink SDK was successfully constructed")
    print(f"Found {num_boards_found.value} SLM controller(s)")

    height = slm_lib.Get_image_height(board_number)
    width = slm_lib.Get_image_width(board_number)
    depth = slm_lib.Get_image_depth(board_number)
    Bytes = depth // 8
    center_x = width // 2
    center_y = height // 2

    print(f"Image width: {width}, Image height: {height}, Image depth: {depth}, Bytes per pixel: {Bytes}")

    # Load LUT file based on image dimensions
    lut_file = None
    if width == 512:
        if depth == 8:
            lut_file = b"C:\\Program Files\\Meadowlark Optics\\Blink OverDrive Plus\\LUT Files\\512x512_linearVoltage.LUT"
        elif depth == 16:
            lut_file = b"C:\\Program Files\\Meadowlark Optics\\Blink OverDrive Plus\\LUT Files\\512x512_16bit_linearVoltage.LUT"
    elif width == 1920:
        lut_file = b"C:\\Program Files\\Meadowlark Optics\\Blink OverDrive Plus\\LUT Files\\1920x1152_linearVoltage.LUT"
    elif width == 1024:
        lut_file = b"C:\\Program Files\\Meadowlark Optics\\Blink OverDrive Plus\\LUT Files\\1024x1024_linearVoltage.LUT"

    if lut_file:
        slm_lib.Load_LUT_file(board_number, lut_file)
    else:
        print("No valid LUT file found for the current dimensions")
        slm_lib.Delete_SDK()
        exit(1)

    # Initialize image arrays
    ImageOne = numpy.zeros([width * height * Bytes], numpy.uint8, 'C')
    ImageTwo = numpy.zeros([width * height * Bytes], numpy.uint8, 'C')
    WFC = numpy.zeros([width * height * Bytes], numpy.uint8, 'C')


    # Write a blank pattern to the SLM to start
    retVal = slm_lib.Write_image(board_number, ImageOne.ctypes.data_as(POINTER(c_ubyte)), height * width * Bytes, wait_For_Trigger, flip_immediate, OutputPulseImageFlip, OutputPulseImageRefresh, timeout_ms)
    if retVal == -1:
        print("DMA Failed")
        slm_lib.Delete_SDK()
        exit(1)

    # Generate phase gradients
    VortexCharge = 30
    image_lib.Generate_LG(ImageOne.ctypes.data_as(POINTER(c_ubyte)), WFC.ctypes.data_as(POINTER(c_ubyte)), width, height, depth, VortexCharge, center_x, center_y, fork, RGB)
    VortexCharge = 3
    image_lib.Generate_LG(ImageTwo.ctypes.data_as(POINTER(c_ubyte)), WFC.ctypes.data_as(POINTER(c_ubyte)), width, height, depth, VortexCharge, center_x, center_y, fork, RGB)

    # Loop between phase gradient images
    for i in range(10):
        retVal = slm_lib.Write_image(board_number, ImageOne.ctypes.data_as(POINTER(c_ubyte)), height * width * Bytes, wait_For_Trigger, flip_immediate, OutputPulseImageFlip, OutputPulseImageRefresh, timeout_ms)
        if retVal == -1:
            print("DMA Failed")
            break
        retVal = slm_lib.ImageWriteComplete(board_number, timeout_ms)
        if retVal == -1:
            print("ImageWriteComplete failed, trigger never received?")
            break

        sleep(0.3)  # This is in seconds. IF USING EXTERNAL TRIGGERS, SET THIS TO 0

        retVal = slm_lib.Write_image(board_number, ImageTwo.ctypes.data_as(POINTER(c_ubyte)), height * width * Bytes, wait_For_Trigger, flip_immediate, OutputPulseImageFlip, OutputPulseImageRefresh, timeout_ms)
        if retVal == -1:
            print("DMA Failed")
            break
        retVal = slm_lib.ImageWriteComplete(board_number, timeout_ms)
        if retVal == -1:
            print("ImageWriteComplete failed, trigger never received?")
            break

        sleep(0.3)  # This is in seconds. IF USING EXTERNAL TRIGGERS, SET THIS TO 0

    # Clean up
    slm_lib.Delete_SDK()
else:
    print("No SLM controllers found")
