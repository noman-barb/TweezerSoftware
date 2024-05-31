import concurrent.futures
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import Manager, Process
import grpc
import numpy as np
import image_service_pb2
import image_service_pb2_grpc
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import time
import os
import trackpy as tp
import pandas as pd
import argparse
import cv2
import asyncio

# turn off warnings
import warnings
warnings.filterwarnings("ignore")


# set blass, openmp threads, lapa threads to 1
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
# set numba threads to 1
os.environ["NUMBA_NUM_THREADS"] = "1"

current_image_id = 0

socket_data = {
    "x":[],
    "y":[],
    "mass":[]
}

websocket_instance = None   



def process_image(raw_image, track_params):
    """Processes a single image and returns the coordinates of the particles."""


    try:
        diameter = track_params['diameter']
        separation = track_params['separation']
        percentile = track_params['percentile']

        minmass = track_params['minmass']
        maxmass = track_params['maxmass']
        pixelthreshold = track_params['pixelthresh']

        preprocess = track_params['preprocess']
        lshort = track_params['lshort']
        llong = track_params['llong']

        min_ecc = track_params['min_ecc']
        max_ecc = track_params['max_ecc']
        refine = track_params['refine']

        if preprocess:
            raw_image = tp.bandpass(raw_image, lshort, llong)

        ret_df = tp.locate(raw_image, diameter=diameter, separation=separation, percentile=percentile, minmass=minmass, max_iterations=refine, engine='numba')

        if maxmass>0:
            ret_df = ret_df[(ret_df['mass'] < maxmass) ]
        if min_ecc>0:
            ret_df = ret_df[(ret_df['ecc'] > min_ecc) ]

        if max_ecc>0:
            ret_df = ret_df[(ret_df['ecc'] < max_ecc) ]
    

        if pixelthreshold>0:
            x_array_int = ret_df['x'].values
            y_array_int = ret_df['y'].values
            values = raw_image[y_array_int.astype(int), x_array_int.astype(int)]
            # index placeholder all with False
            #index = np.zeros(len(values), dtype=np.bool_)
            index = (values >= pixelthreshold)

            # keep the index where the pixel value is above the threshold
            ret_df = ret_df[index]



        return ret_df

    except Exception as e:
        print("Error in process_image", e)
        # return blank dataframe with columns x, y, mass, ecc
        return pd.DataFrame(columns=['x', 'y', 'mass', 'ecc'])


    


    
def process_grid(image, start_coord_x, start_coord_y, data_map):
    """Processes a single grid of the image and adjusts coordinates."""

    # Process the grid
    df_local = process_image(image, data_map)

    # Adjust coordinates to global image coordinates
    df_local['x'] += start_coord_x
    df_local['y'] += start_coord_y

    return df_local

def process_image_concurrent(image, executor=None, data_map=None):
    """Processes the image concurrently using multiple workers."""

    grid_x = data_map['grid_x']
    grid_y = data_map['grid_y']
    height, width = image.shape[:2]
    overlap = data_map['overlap']
    height, width = image.shape[:2]

   
    
    # Create tasks for each grid
    tasks = []

    for start_coord_y in range(0, height, grid_y):
        for start_coord_x in range(0, width, grid_x):
            _end_x = min(start_coord_x + data_map['grid_x'] + overlap, width)
            _end_y = min(start_coord_y + data_map['grid_y'] + overlap, height)

            
            tasks.append(executor.submit(process_grid, image[start_coord_y:_end_y, start_coord_x:_end_x], start_coord_x, start_coord_y, data_map))
            


    # Collect results from all tasks
    results = [task.result() for task in concurrent.futures.as_completed(tasks)]
    
    

    # Concatenate all dataframes into a single dataframe
    df_global = pd.concat(results)

    # save to socket_data
    global socket_data
    socket_data['x'] = df_global['x'].tolist()
    socket_data['y'] = df_global['y'].tolist()
    socket_data['mass'] = df_global['mass'].tolist()
    global last_data_time
    last_data_time = time.time()
    global current_image_id
    current_image_id += 1

    # show image and particles using opencv
    # image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    # for i in range(len(socket_data['x'])):
    #     cv2.circle(image, (int(socket_data['x'][i]), int(socket_data['y'][i])), 2, (0, 255, 0), -1)

    # cv2.imshow('image', image)

    # # wait for 100 s and then close the window
    # cv2.waitKey(100)

    # cv2.destroyAllWindows()

    return df_global


if __name__ == '__main__':
    # Start the gRPC server in a separate thread

    app = FastAPI()

    # get n_procs from the command line
    parser = argparse.ArgumentParser()
    parser.add_argument("--n_procs", type=int, default=4)
    args = parser.parse_args()
    n_procs = args.n_procs


    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    executor = ProcessPoolExecutor(n_procs)

    data_map = {}
    data_map['diameter'] = 21
    data_map['separation'] = 18
    data_map['percentile'] = 14
    data_map['minmass'] = 100
    data_map['maxmass'] = 999999
    data_map['pixelthresh'] = -1
    data_map['preprocess'] = True
    data_map['lshort'] = 1
    data_map['llong'] = 21
    data_map['min_ecc'] = -1
    data_map['max_ecc'] = -1
    data_map['refine'] = 1
    data_map['grid_x'] = 300
    data_map['grid_y'] = 250
    data_map['overlap'] = 21*2



  
    class ImageServiceServicer(image_service_pb2_grpc.ImageServiceServicer):
        def LocateTask(self, request, context):

            print("Processing image ...")
           
            width = request.width
            height = request.height
            start_time = time.time()
            image = np.frombuffer(request.image, dtype=np.uint8).reshape((height, width))

            # Process the image
            df = process_image_concurrent(image, executor=executor, data_map=data_map)

            

            return image_service_pb2.ImageResponse()


    def serve():
        options = [
            ('grpc.max_receive_message_length', 50 * 1024 * 1024),  # 50 MB
            ('grpc.max_send_message_length', 50 * 1024 * 1024),     # 50 MB
            ('grpc.initial_connection_window_size', 32 * 1024 * 1024)  # 32 MB
        ]
        
        server = grpc.server(concurrent.futures.ThreadPoolExecutor(max_workers=1), options=options)
        image_service_pb2_grpc.add_ImageServiceServicer_to_server(ImageServiceServicer(), server)
        server.add_insecure_port('[::]:50051')
        server.start()
        server.wait_for_termination()


    


    @app.get("/heartbeat")
    async def get_heartbeat():
        return {"success": True, "msg": "Server is running", "data": []}


    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        global websocket_instance
        global current_image_id


        await websocket.accept()
        websocket_instance = websocket

        last_image_sent_id = -1

        while True:

    

            try:
                await asyncio.sleep(0.001)

                if last_image_sent_id == current_image_id:
                  
                    continue

                

                last_image_sent_id = current_image_id

                # send data (socket data)
                await websocket.send_json(socket_data)

            except Exception as e:
                print("Error in websocket", e)
                
                break

    @app.post("/set_track_params")
    async def set_parameters(data: dict):
        global data_map
        data_map['diameter'] = int(data['diameter'])
        data_map['separation'] = int(data['separation'])
        data_map['percentile'] = float(data['percentile'])
        data_map['minmass'] = int(data['minmass'])
        data_map['maxmass'] = int(data['maxmass'])
        data_map['pixelthresh'] = int(data['pixelthresh'])
        data_map['preprocess'] = int(data['preprocess'])
        data_map['lshort'] = int(data['lshort'])
        data_map['llong'] = int(data['llong'])
        data_map['min_ecc'] = float(data['min_ecc'])
        data_map['max_ecc'] = float(data['max_ecc'])
        data_map['refine'] = int(data['refine'])
        data_map['grid_x'] = int(data['grid_x'])
        data_map['grid_y'] = int(data['grid_y'])
        data_map['overlap'] = int(data['overlap'])
        
        return {"success": True, "msg": "Parameters set successfully", "data": []}


    import threading
    grpc_thread = threading.Thread(target=serve)
    grpc_thread.start()

    # Start the FastAPI server
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=4011, workers=1)