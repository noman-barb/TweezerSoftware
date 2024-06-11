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
import asyncio
import websockets
from websockets import WebSocketServerProtocol
from typing import Set
import json
from multiprocessing.managers import DictProxy

def data_communicator(shared_dict, lock):

    connected_clients: Set[WebSocketServerProtocol] = set()

    broadcast_queue = []


    def get_value(d):
        return {
            key: get_value(sub_d)
            if isinstance(sub_d, DictProxy) else sub_d 
            for key, sub_d in d.items()
                }



    def round_array(array):
        return [round(x, 1) for x in array]

    def update_shared_dict(xyzi, data_received_time):
        with lock:
            shared_dict['points']['xyzi'] = xyzi
            shared_dict['points']['last_data_received'] = data_received_time

    def append_to_broadcast_queue(update_type, data_id, x_array, y_array, z_array, intensity_array, data_received_time, affine):
        broadcast_queue.append({
            "update_type": update_type,
            "id": data_id,
            "points": {
                "x_array": x_array,
                "y_array": y_array,
                "z_array": z_array,
                "intensity_array": intensity_array,
                "data_received_time": data_received_time,
            },
            "affine": affine
        })

    def process_points(data, update_type):
        start_time = time.time()
        all_points = data['points']
        data_id = data['id']

        x_array = round_array(all_points['x_array'])
        y_array = round_array(all_points['y_array'])
        z_array = round_array(all_points['z_array'])
        intensity_array = round_array(all_points['intensity_array'])

        xyzi = shared_dict['points']['xyzi']
        affine = shared_dict['affine']

        if update_type == "add_points":
            for x, y, z, i in zip(x_array, y_array, z_array, intensity_array):
                xyzi[(x, y, z)] = i
        elif update_type == "update_points":
            xyzi = {(x, y, z): i for x, y, z, i in zip(x_array, y_array, z_array, intensity_array)}
        elif update_type == "remove_points":
            for x, y, z, i in zip(x_array, y_array, z_array, intensity_array):
                if (x, y, z) in xyzi:
                    del xyzi[(x, y, z)]

        data_received_time = time.time()
        update_shared_dict(xyzi, data_received_time)
        append_to_broadcast_queue(update_type, data_id, x_array, y_array, z_array, intensity_array, data_received_time, affine)

        print(f"Time taken to process points: {time.time() - start_time} seconds")


    def get_points(data):

        xyzi = shared_dict['points']['xyzi']
        keys = xyzi.keys()
        x_array = [None] * len(keys)
        y_array = [None] * len(keys)
        z_array = [None] * len(keys)
        data_id = data['id']
        intensity_array = [None] * len(keys)

        for index, key in enumerate(keys):
            x_array[index] = key[0]
            y_array[index] = key[1]
            z_array[index] = key[2]
            intensity_array[index] = xyzi[key]


        affine = shared_dict['affine']

        append_to_broadcast_queue("get_points", data_id, x_array, y_array, z_array, intensity_array, -1, affine)




    def update_affine(data):
        
        affine_data = data['affine']
        data_id = data['id']
        SLM_X_0 =  int(affine_data['SLM_X_0'])
        SLM_Y_0 = int(affine_data['SLM_Y_0'])
        CAM_X_0 = int(affine_data['CAM_X_0'])
        CAM_Y_0 = int(affine_data['CAM_Y_0'])

        SLM_X_1 = int(affine_data['SLM_X_1'])
        SLM_Y_1 = int(affine_data['SLM_Y_1'])
        CAM_X_1 = int(affine_data['CAM_X_1'])
        CAM_Y_1 = int(affine_data['CAM_Y_1'])

        SLM_X_2 = int(affine_data['SLM_X_2'])
        SLM_Y_2 = int(affine_data['SLM_Y_2'])
        CAM_X_2 = int(affine_data['CAM_X_2'])
        CAM_Y_2 = int(affine_data['CAM_Y_2'])

        with lock:
            data_received_time = time.time()
            shared_dict['affine']['SLM_X_0'] = SLM_X_0
            shared_dict['affine']['SLM_Y_0'] = SLM_Y_0
            shared_dict['affine']['CAM_X_0'] = CAM_X_0
            shared_dict['affine']['CAM_Y_0'] = CAM_Y_0

            shared_dict['affine']['SLM_X_1'] = SLM_X_1
            shared_dict['affine']['SLM_Y_1'] = SLM_Y_1
            shared_dict['affine']['CAM_X_1'] = CAM_X_1
            shared_dict['affine']['CAM_Y_1'] = CAM_Y_1

            shared_dict['affine']['SLM_X_2'] = SLM_X_2
            shared_dict['affine']['SLM_Y_2'] = SLM_Y_2
            shared_dict['affine']['CAM_X_2'] = CAM_X_2
            shared_dict['affine']['CAM_Y_2'] = CAM_Y_2
            shared_dict['affine']['last_data_received'] = data_received_time


        # add to broadcast queue with the necceassary data that has to be sent to all clients
        broadcast_queue.append({
            "update_type": "update_affine",
            "id": data_id,
            "affine": {
                "SLM_X_0": SLM_X_0, "SLM_Y_0": SLM_Y_0, "CAM_X_0": CAM_X_0, "CAM_Y_0": CAM_Y_0,
                "SLM_X_1": SLM_X_1, "SLM_Y_1": SLM_Y_1, "CAM_X_1": CAM_X_1, "CAM_Y_1": CAM_Y_1,
                "SLM_X_2": SLM_X_2, "SLM_Y_2": SLM_Y_2, "CAM_X_2": CAM_X_2, "CAM_Y_2": CAM_Y_2,
                "data_received_time": data_received_time,
            }
        })

    async def handler(websocket: WebSocketServerProtocol, path: str):
        # Register the new client
        connected_clients.add(websocket)
        try:
            async for message in websocket:
                
                try:
                    data = json.loads(message)
                    if data['command'] == 'add_points' or data['command'] == 'update_points' or data['command'] == 'remove_points':
                        process_points(data,data['command'])
                    elif data['command'] == 'get_points':
                        get_points(data)
                    elif data['command'] == 'update_affine':
                        update_affine(data)
                
                    else:
                        print("Invalid command")
                    
                except Exception as e:
                    print(f"An error occurred: {e}")
                
        finally:
            # Unregister the client
            connected_clients.remove(websocket)


    async def send_personal_message(websocket: WebSocketServerProtocol, message: str):
        disconnected_clients = set()
        if not websocket.closed:
            await websocket.send(message)
        else:
            disconnected_clients.add(websocket)

        # Remove disconnected clients
        connected_clients.difference_update(disconnected_clients)
        
    async def broadcast(message: str):
        if connected_clients:
            await asyncio.wait([client.send(message) for client in connected_clients])


    async def broadcast(message: str):
            disconnected_clients = set()
            for client in connected_clients:
                if not client.closed:
                    await client.send(message)
                else:
                    disconnected_clients.add(client)
            # Remove disconnected clients
            connected_clients.difference_update(disconnected_clients)



    async def update_broadcaster():

        while True:

            with lock:
                last_updated_affine = shared_dict['affine']['last_updated']
                last_updated_points = shared_dict['points']['last_updated']
            
            for _index, broadcast_data in enumerate(broadcast_queue):
                if broadcast_data['update_type'] == 'update_affine':
                    if last_updated_affine > broadcast_data['affine']['data_received_time']:
                        await broadcast(json.dumps(get_value(broadcast_data)))
                        # remove the data from the broadcast queue
                        broadcast_queue.pop(_index)

                else:
                    if last_updated_points > broadcast_data['points']['data_received_time']:
                        await broadcast(json.dumps(get_value(broadcast_data)))
                        # remove the data from the broadcast queue
                        broadcast_queue.pop(_index)
                    
            # sleep for 0.01 seconds
            await asyncio.sleep(0.001)


    async def main():
        port = 4041
        server = await websockets.serve(handler, '0.0.0.0', port, ping_interval=None, ping_timeout=None)
        print(f"WebSocket server started on ws://0.0.0.0:{port}")
        asyncio.create_task(update_broadcaster())
        await server.wait_closed()

    def signal_handler(signum, frame):
        print("Received signal to terminate server process.")
        os._exit(0)

    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, signal_handler)

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Server stopped.")


if __name__ == '__main__':

    manager = multiprocessing.Manager()
    
    shared_dict = manager.dict({
        "affine": manager.dict({
            "last_updated": -1,
            "last_data_received": time.time(),
            "last_check_for_updates": time.time(),
            "SLM_X_0": 10, "SLM_Y_0": 10, "CAM_X_0": 10, "CAM_Y_0": 10,
            "SLM_X_1": -10, "SLM_Y_1": -10, "CAM_X_1": -10, "CAM_Y_1": -10,
            "SLM_X_2": -20, "SLM_Y_2": 20, "CAM_X_2": -20, "CAM_Y_2": 20
        }),
        "points": manager.dict({
            "last_updated": -1,
            "last_data_received": time.time(),
            "last_check_for_updates": time.time(),
            "xyzi": manager.dict({}),
        })
    })
    
    lock = manager.Lock()


    ##################################################################################################################################


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

    # print height, width, depth, Bytes
    print(f"Image width: {width}, Image height: {height}, Image depth: {depth}, Bytes per pixel: {Bytes}")

    print(f"Image width: {width}, Image height: {height}, Image depth: {depth}, Bytes per pixel: {Bytes}")

    # Load LUT file based the SLM LCD dimensions
    # lut_file = b"C:\\Program Files\\Meadowlark Optics\\Blink OverDrive Plus\\LUT Files\\1920x1152_linearVoltage.LUT"
    # calibrated
    lut_file = b"C:\Program Files\Meadowlark Optics\Blink OverDrive Plus\LUT Files\slm6336_at1064_PCIe.LUT"
    slm_lib.Load_LUT_file(board_number, lut_file)
    

    # Initialize image arrays
    hologram_image_1 = np.zeros([width * height * Bytes], np.uint8, 'C')
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
    is_hologram_generator_initialized = image_lib.Initialize_HologramGenerator(width, height, depth, 20, 0)
    

    if is_hologram_generator_initialized == 0:
        print("Hologram generator did not initialize successfully")
        cleanup(None, None)
        exit(1)

    print("Hologram generator initialized successfully")


    def work_on_affine():

        start_time = time.time()
    
        with lock:
            SLM_X_0 = int(shared_dict['affine']['SLM_X_0'])
            SLM_Y_0 = int(shared_dict['affine']['SLM_Y_0'])
            CAM_X_0 = int(shared_dict['affine']['CAM_X_0'])
            CAM_Y_0 = int(shared_dict['affine']['CAM_Y_0'])

            SLM_X_1 = int(shared_dict['affine']['SLM_X_1'])
            SLM_Y_1 = int(shared_dict['affine']['SLM_Y_1'])
            CAM_X_1 = int(shared_dict['affine']['CAM_X_1'])
            CAM_Y_1 = int(shared_dict['affine']['CAM_Y_1'])

            SLM_X_2 = int(shared_dict['affine']['SLM_X_2'])
            SLM_Y_2 = int(shared_dict['affine']['SLM_Y_2'])
            CAM_X_2 = int(shared_dict['affine']['CAM_X_2'])
            CAM_Y_2 = int(shared_dict['affine']['CAM_Y_2'])

            last_updated = shared_dict['affine']['last_updated']
            last_data_received = shared_dict['affine']['last_data_received']
        
            # set last check for updates to current time
            shared_dict['affine']['last_check_for_updates'] = time.time()


        if last_updated <= last_data_received:
            print(f"Affine updated in {time.time() - start_time:.3f} seconds")
            image_lib.CalculateAffinePolynomials(SLM_X_0, SLM_Y_0, CAM_X_0, CAM_Y_0, SLM_X_1, SLM_Y_1, CAM_X_1, CAM_Y_1, SLM_X_2, SLM_Y_2, CAM_X_2, CAM_Y_2)
            print(f"Affine calculated in {time.time() - start_time:.3f} seconds")
            with lock:
                shared_dict['affine']['last_updated'] = time.time()

        
    def work_on_points():

        start_time = time.time()

        with lock:
            # x_array = np.array(shared_dict['points']['x_array'])
            # y_array = np.array(shared_dict['points']['y_array'])
            # z_array = np.array(shared_dict['points']['z_array'])
            # intensity_array = np.array(shared_dict['points']['intensity_array'])

            # extract the values from the shared dictionary
            keys = shared_dict['points']['xyzi'].keys()
            x_array = [None] * len(keys)
            y_array = [None] * len(keys)
            z_array = [None] * len(keys)
            intensity_array = [None] * len(keys)

            for index, key in enumerate(keys):
                x_array[index] = key[0]
                y_array[index] = key[1]
                z_array[index] = key[2]
                intensity_array[index] = shared_dict['points']['xyzi'][key]

            x_array = np.array(x_array).astype(np.float32)
            y_array = np.array(y_array).astype(np.float32)
            z_array = np.array(z_array).astype(np.float32)
            intensity_array = np.array(intensity_array).astype(np.float32)

            # print x_array, y_array, z_array, intensity_array
            # print("x_array\n", x_array)
            # print("y_array\n", y_array)
            # print("z_array\n", z_array)
            # print("intensity_array\n", intensity_array)

            last_updated = shared_dict['points']['last_updated']
            last_data_received = shared_dict['points']['last_data_received']
        
            # set last check for updates to current time
            shared_dict['points']['last_check_for_updates'] = time.time()


       
        if last_updated <= last_data_received:
           
            
            print (f"Preprocessed points in {time.time() - start_time:.3f} seconds")
            image_lib.Generate_Hologram(hologram_image_1.ctypes.data_as(POINTER(c_ubyte)), WFC.ctypes.data_as(POINTER(c_float)), x_array.ctypes.data_as(POINTER(c_float)), y_array.ctypes.data_as(POINTER(c_float)), z_array.ctypes.data_as(POINTER(c_float)), intensity_array.ctypes.data_as(POINTER(c_float)), len(x_array), 1)
            # save image as png
            image_reshaped = hologram_image_1.reshape((height, width, Bytes))
            cv2.imwrite("hologram.png", image_reshaped)
            print(f"Image generated in {time.time() - start_time:.3f} seconds")
            write_image(hologram_image_1)
            print(f"Hologram written in {time.time() - start_time:.3f} seconds")
            with lock:
                shared_dict['points']['last_updated'] = time.time()



    def check_for_updates():
        work_on_affine()
        work_on_points()



 ########################## another process to receive updates from the frontend ##########################
   
    p = multiprocessing.Process(target=data_communicator, args=(shared_dict, lock))
    p.daemon = True
    p.start()
    ##################################################################################################################################


    while True:
        check_for_updates()
        time.sleep(0.001)

    # delete the SDK
    cleanup(None, None)
