# main.py
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
import io
import os
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import Manager, Process
from CamServer import CamServer
import uvicorn
import time
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import Manager, Process
import argparse


# PORT_CAMSERVER_1 = 4001
# PORT_CAMSERVER_2 = 4002

if __name__ == "__main__":

    # get the port number from the command line
    parser = argparse.ArgumentParser(description='Start the CamServer')
    parser.add_argument('--port', type=int, help='Port number to start the CamServer', required=True)
    args = parser.parse_args()
    port = args.port


    CamServer.start(port)

    # app = FastAPI()

    # # Setup CORS to allow all
    # app.add_middleware(
    #     CORSMiddleware,
    #     allow_origins=["*"],
    #     allow_methods=["*"],
    #     allow_headers=["*"],
    # )

    # # Create a shared dictionary for camera control
    # manager = Manager()
  
    # print("Starting both the camservers")

    # executor = ProcessPoolExecutor(2)
    # executor.submit(CamServer.start, PORT_CAMSERVER_1)
    # executor.submit(CamServer.start, PORT_CAMSERVER_2)

  


    #############################################

   

    # is_cam_server_1_active = False
    # is_cam_server_2_active = False
    
    # @app.get("/heartbeat")
    # def get_heartbeat():
    #     return {"success": True, "msg": "Server is running", "data": []}

    # @app.post("/warmup/camserver/1")
    # async def warmup_camserver1():
    #     port = 4001
    #     global is_cam_server_1_active
    #     if not is_cam_server_1_active:
    #         executor.submit(CamServer.start, port)
    #         is_cam_server_1_active = True
    #         return {"success": True, "msg": "CamServer 1 warmed up", "data": [{"port": port}]}

    #     return {"success": True, "msg": "CamServer 1 already active", "data": [{"port": port}]}

    # @app.post("/warmup/camserver/2")
    # async def warmup_camserver2():
    #     port = 4002
    #     global is_cam_server_2_active
    #     if not is_cam_server_2_active:
    #         executor.submit(CamServer.start, port)
    #         is_cam_server_2_active = True
    #         return {"success": True, "msg": "CamServer 2 warmed up", "data": [{"port": port}]}

    #     return {"success": True, "msg": "CamServer 2 already active", "data": [{"port": port}]}


    # @app.get("/warmup/camserver/1/status")
    # async def get_camserver1_status():
    #     port = 4001
    #     return {"success": True, "msg": "CamServer 1 status", "data": [{"port": port, "active": is_cam_server_1_active}]}

    # @app.get("/warmup/camserver/2/status")
    # async def get_camserver2_status():
    #     port = 4002
    #     return {"success": True, "msg": "CamServer 2 status", "data": [{"port": port, "active": is_cam_server_2_active}]}


    


    # uvicorn.run(app, host="0.0.0.0", port=4000)