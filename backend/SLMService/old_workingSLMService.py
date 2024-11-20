from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from websockets.exceptions import ConnectionClosed
import signal
from pydantic import BaseModel
import os
import time
import numpy as np
import threading
from threading import Lock
from fastapi.middleware.cors import CORSMiddleware
from collections import deque
import cv2
from fastapi.responses import FileResponse
import multiprocessing
from ctypes import *
from time import sleep
import websockets
from websockets import WebSocketServerProtocol
from typing import Set
import json
from multiprocessing.managers import DictProxy
from collections import deque

def data_communicator(shared_dict, lock):

    import asyncio
    import websockets
    from websockets import WebSocketServerProtocol
    from typing import Set
    import json
    from multiprocessing.managers import DictProxy

    connected_clients: Set[WebSocketServerProtocol] = set()
    broadcast_queue = asyncio.Queue()
    rate_limit = 10  # Limit to 10 messages per second
    last_processed_time = time.time()

    def get_value(d):
        return {
            key: get_value(sub_d)
            if isinstance(sub_d, DictProxy) else sub_d 
            for key, sub_d in d.items()
        }

    def round_array(array):
        return [round(x, 1) for x in array]

    async def broadcast(message: str):
        print(time.time(), "broadcast")
        if not connected_clients:
            return
        disconnected_clients = set()
        for client in connected_clients.copy():
            try:
                await client.send(message)
            except websockets.exceptions.ConnectionClosed:
                disconnected_clients.add(client)
        connected_clients.difference_update(disconnected_clients)

    async def update_broadcaster():
        print(time.time(), "update_broadcaster")
        while True:
            print(time.time(), "Broadcasted message")
            broadcast_data = await broadcast_queue.get()
            try:
                message = json.dumps(get_value(broadcast_data))
                try:
                    # TODO exponential backoff later on???
                    await asyncio.wait_for(broadcast(message), timeout=0.1)
                except asyncio.TimeoutError:
                    print("Broadcast operation timed out")
                
                await asyncio.sleep(0.001)
            except Exception as e:
                print(f"Error in broadcaster: {e}")
            broadcast_queue.task_done()

    async def handler(websocket: WebSocketServerProtocol, path: str):
        print(time.time(), "handler")
        connected_clients.add(websocket)
        try:
            async for message in websocket:

                nonlocal last_processed_time
                current_time = time.time()
                if current_time - last_processed_time < 1 / rate_limit:
                    print("Rate limited")
                    continue
                last_processed_time = current_time

                await asyncio.sleep(0.001)
                data = json.loads(message)
                await process_data(data)
                
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            connected_clients.remove(websocket)

    async def process_data(data):
        print(time.time(), "process_data")
       

        try:
            command = data.get('command')
            if command in ['add_points', 'update_points', 'remove_points']:
                await process_points(data, command)
            elif command == 'get_points':
                await get_points(data)
            elif command == 'update_affine':
                await update_affine(data)
            else:
                print("Invalid command")
        except Exception as e:
            print(f"Error processing data: {e}")

    async def process_points(data, update_type):
        print(time.time(), "process_points")
        start_time = time.time()
        all_points = data['points']
        data_id = data['id']

        x_array = round_array(all_points['x_array'])
        y_array = round_array(all_points['y_array'])
        z_array = round_array(all_points['z_array'])
        intensity_array = round_array(all_points['intensity_array'])

        with lock:
            xyzi = shared_dict['points']['xyzi']
            if update_type == "add_points":
                for x, y, z, i in zip(x_array, y_array, z_array, intensity_array):
                    xyzi[(x, y, z)] = i
            elif update_type == "update_points":
                xyzi.clear()
                for x, y, z, i in zip(x_array, y_array, z_array, intensity_array):
                    xyzi[(x, y, z)] = i
            elif update_type == "remove_points":
                for x, y, z in zip(x_array, y_array, z_array):
                    xyzi.pop((x, y, z), None)
            shared_dict['points']['last_data_received'] = time.time()

        await append_to_broadcast_queue({
            "update_type": update_type,
            "id": data_id,
            "points": {
                "x_array": x_array,
                "y_array": y_array,
                "z_array": z_array,
                "intensity_array": intensity_array,
                "data_received_time": shared_dict['points']['last_data_received'],
            },
            "affine": get_value(shared_dict['affine'])
        })
        print(f"Time taken to process points: {time.time() - start_time} seconds")

    async def get_points(data):
        print(time.time(), "get_points")
        with lock:
            xyzi = shared_dict['points']['xyzi']
            x_array = []
            y_array = []
            z_array = []
            intensity_array = []
            for x, y, z in xyzi.keys():
                x_array.append(x)
                y_array.append(y)
                z_array.append(z)
                intensity_array.append(xyzi[(x, y, z)])
            data_id = data['id']
            affine = get_value(shared_dict['affine'])

        await append_to_broadcast_queue({
            "update_type": "get_points",
            "id": data_id,
            "points": {
                "x_array": x_array,
                "y_array": y_array,
                "z_array": z_array,
                "intensity_array": intensity_array,
                "data_received_time": -1,
            },
            "affine": affine
        })

    async def update_affine(data):
        affine_data = data['affine']
        data_id = data['id']
        with lock:
            for key in ['SLM_X_0', 'SLM_Y_0', 'CAM_X_0', 'CAM_Y_0',
                        'SLM_X_1', 'SLM_Y_1', 'CAM_X_1', 'CAM_Y_1',
                        'SLM_X_2', 'SLM_Y_2', 'CAM_X_2', 'CAM_Y_2']:
                shared_dict['affine'][key] = int(affine_data[key])
            shared_dict['affine']['last_data_received'] = time.time()
            shared_dict['points']['last_data_received'] = shared_dict['affine']['last_data_received']
            affine = get_value(shared_dict['affine'])

        await append_to_broadcast_queue({
            "update_type": "update_affine",
            "id": data_id,
            "affine": affine
        })

    async def append_to_broadcast_queue(broadcast_data):
        size_of_queue = broadcast_queue.qsize()
        print(time.time(), f"append_to_broadcast_queue of size {size_of_queue}")

        if size_of_queue > 5:
            print("Queue is full. Clearing the queue.")
            return
        await broadcast_queue.put(broadcast_data)

    async def main():
        port = 4041
        server = await websockets.serve(handler, '0.0.0.0', port, ping_interval=None, ping_timeout=None)
        print(f"WebSocket server started on ws://0.0.0.0:{port}")
        broadcaster_task = asyncio.create_task(update_broadcaster())
        await server.wait_closed()
        await broadcaster_task

    def signal_handler(signum, frame):
        print("Received signal to terminate server process.")
        for task in asyncio.all_tasks():
            task.cancel()
        asyncio.get_event_loop().stop()
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
    flip_immediate = c_uint(0)
    timeout_ms = c_uint(5000)
    fork = c_uint(0)
    RGB = c_uint(0)

    # Output pulse settings
    OutputPulseImageFlip = c_uint(0)
    OutputPulseImageRefresh = c_uint(0)

    is_hologram_generator_initialized = 0

    # Set up function prototypes
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

    image_lib.Destruct_HologramGenerator.argtypes = []
    image_lib.Destruct_HologramGenerator.restype = c_void_p

    slm_lib.Delete_SDK.argtypes = []
    slm_lib.Delete_SDK.restype = c_void_p

    image_lib.Initialize_HologramGenerator.argtypes = [c_int, c_int, c_int, c_int, c_int]
    image_lib.Initialize_HologramGenerator.restype = c_int

    image_lib.CalculateAffinePolynomials.argtypes = [c_int] * 12
    image_lib.CalculateAffinePolynomials.restype = c_int

    image_lib.Generate_Hologram.argtypes = [POINTER(c_ubyte), POINTER(c_float), POINTER(c_float), POINTER(c_float), POINTER(c_float), POINTER(c_float), c_int, c_int]
    image_lib.Generate_Hologram.restype = c_void_p

    # Initialize SDK
    slm_lib.Create_SDK(bit_depth, byref(num_boards_found), byref(constructed_okay), is_nematic_type, RAM_write_enable, use_GPU, max_transients, 0)

    # Signal handling for cleanup
    def cleanup(signum, frame):
        print("Exit command. Cleaning up resources...")
        if is_hologram_generator_initialized:
            image_lib.Destruct_HologramGenerator()
        slm_lib.Delete_SDK()
        os._exit(0)

    for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGABRT, signal.SIGSEGV, signal.SIGILL):
        signal.signal(sig, cleanup)

    if constructed_okay.value == 0:
        print("Blink SDK did not construct successfully")
        exit(1)

    if num_boards_found.value < 1:
        print("No SLM controller found")
        exit(1)

    print("Blink SDK was successfully constructed")
    print(f"Found {num_boards_found.value} SLM controller(s)")

    height = slm_lib.Get_image_height(board_number)
    width = slm_lib.Get_image_width(board_number)
    depth = slm_lib.Get_image_depth(board_number)
    Bytes = depth // 8

    print(f"Image width: {width}, Image height: {height}, Image depth: {depth}, Bytes per pixel: {Bytes}")

    # Load LUT file
    lut_file = b"C:\\Program Files\\Meadowlark Optics\\Blink OverDrive Plus\\LUT Files\\slm6336_at1064_PCIe.LUT"
    slm_lib.Load_LUT_file(board_number, lut_file)

    # Initialize image arrays
    hologram_image_1 = np.zeros([width * height * Bytes], np.uint8, 'C')
    WFC = np.zeros([width * height * Bytes], np.uint8, 'C')

    # Write a blank pattern to the SLM
    def write_image(image_array):
        retVal = slm_lib.Write_image(
            board_number, image_array.ctypes.data_as(POINTER(c_ubyte)), height * width * Bytes,
            wait_For_Trigger, flip_immediate, OutputPulseImageFlip, OutputPulseImageRefresh, timeout_ms)
        if retVal == -1:
            print("DMA Failed")
            slm_lib.Delete_SDK()
            exit(1)

    write_image(WFC)

    # Initialize hologram generator
    is_hologram_generator_initialized = image_lib.Initialize_HologramGenerator(width, height, depth, 10, 0)
    if is_hologram_generator_initialized == 0:
        print("Hologram generator did not initialize successfully")
        cleanup(None, None)
        exit(1)

    print("Hologram generator initialized successfully")

    # Start the data communicator process
    p = multiprocessing.Process(target=data_communicator, args=(shared_dict, lock))
    p.daemon = True
    p.start()

    # Main loop to process updates
    def process_affine():
        with lock:
            last_updated = shared_dict['affine']['last_updated']
            last_data_received = shared_dict['affine']['last_data_received']
        if last_updated < last_data_received:
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
            image_lib.CalculateAffinePolynomials(
                SLM_X_0, SLM_Y_0, CAM_X_0, CAM_Y_0,
                SLM_X_1, SLM_Y_1, CAM_X_1, CAM_Y_1,
                SLM_X_2, SLM_Y_2, CAM_X_2, CAM_Y_2)
            with lock:
                shared_dict['affine']['last_updated'] = time.time()
            print(f"Affine updated in {time.time() - start_time:.3f} seconds")

    def process_points():
        with lock:
            last_updated = shared_dict['points']['last_updated']
            last_data_received = shared_dict['points']['last_data_received']
        if last_updated < last_data_received:
            start_time = time.time()
            with lock:
                keys = list(shared_dict['points']['xyzi'].keys())
                x_array = np.array([k[0] for k in keys], dtype=np.float32)
                y_array = np.array([k[1] for k in keys], dtype=np.float32)
                z_array = np.array([k[2] for k in keys], dtype=np.float32)
                intensity_array = np.array([shared_dict['points']['xyzi'][k] for k in keys], dtype=np.float32)
            image_lib.Generate_Hologram(
                hologram_image_1.ctypes.data_as(POINTER(c_ubyte)),
                WFC.ctypes.data_as(POINTER(c_float)),
                x_array.ctypes.data_as(POINTER(c_float)),
                y_array.ctypes.data_as(POINTER(c_float)),
                z_array.ctypes.data_as(POINTER(c_float)),
                intensity_array.ctypes.data_as(POINTER(c_float)),
                len(x_array), 1)
            write_image(hologram_image_1)
            with lock:
                shared_dict['points']['last_updated'] = time.time()
            print(f"Points processed and hologram updated in {time.time() - start_time:.3f} seconds")

    try:
        while True:
            process_affine()
            process_points()
            # time.sleep(0.01)
    except KeyboardInterrupt:
        cleanup(None, None)