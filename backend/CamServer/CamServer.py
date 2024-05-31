from .cameras import Camera1 as Cam1
from .cameras import Camera2 as Cam2
from .cameras import Camera3 as Cam3
from .cameras import Camera4 as Cam4

import time
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
import io
import os
import cv2
import asyncio
import grpc
import image_service_pb2
import image_service_pb2_grpc

TURN_OFF_CAMERA_ON_NOT_RECEIVING_HEARTBEAT_TIME = 5


class CamServer:




    def __init__(self):
        self.cameras = {
            "Cam1_real" : Cam1,
            "Cam2_real" : Cam2,
            "Cam3_virt": Cam3,
            "Cam4_virt": Cam4
        }

        self.frame_rate = 10
        self.is_camera_active = False
        self.camera_id = None
        self.camera_instance = None
        self.websocket = None
        self.image_source_path = None
        self.exposure = 10.0
        self.gain = 1.0
        self.request_locate = False

        self.image = None
        self.image_id = -1

        self.last_image_time = time.time()

        self.last_hearbeat_time = time.time()
        self.image_height = -1
        self.image_width = -1
        self.image_bytes = None



        self.channel = None
        self.stub = None

        self.init_tracking()

        self.save_folder = None

        self.root_folder = "F:/temp_cam_data/images/"




       


    def init_tracking(self):

        if self.channel is None:
            

            try:
                options = [
                ('grpc.max_receive_message_length', 50 * 1024 * 1024),  # 50 MB
                ('grpc.max_send_message_length', 50 * 1024 * 1024),     # 50 MB
                ('grpc.initial_connection_window_size', 32 * 1024 * 1024)  # 32 MB
                ]
            
                self.channel = grpc.insecure_channel('127.0.0.1:50051', options=options)
                self.stub = image_service_pb2_grpc.ImageServiceStub(self.channel)

            except Exception as e:
                print("Error tracking", e)
            




    def get_camera(self, camera_id):
        return self.cameras[camera_id]

    def get_camera_ids(self):
        return list(self.cameras.keys())

    def get_camera_details(self, camera_id):
        return self.cameras[camera_id].Camera.get_camera_details()

    def instantiate_camera(self, camera_id):
        return self.cameras[camera_id].Camera.get_camera_instance()

    def initialize(self, port = 4001):

        print("Starting camera server at port", port)

        self.app = FastAPI()

        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Allows all origins
            allow_methods=["*"],  # Allows all methods
            allow_headers=["*"],  # Allows all headers
            )


        async def send_frame(self, frame_bytes):
            if self.websocket is not None:
                try:
                    await self.websocket.send_bytes(frame_bytes)
                    print("Sent frame to websocket")
                except Exception as e:
                    print(f"An error occurred while sending frame: {e}")


        def on_update_callback(image_id, image):


            try:




                # print("Image updated", image_id)
                # cv2.imshow(self.camera_id, image)
                # # # set title as image_id
                # cv2.setWindowTitle(self.camera_id, str(image_id) + " " + self.camera_id)
                # print(image.shape)
                # # wait for 1 ms
                # cv2.waitKey(1)

                # self.image = cv2.imencode('.jpg', image)[1].tobytes()
                # don't encode the image, send the raw image
                # self.image = image.tobytes()
                # encode using PIL and send
                _start_time = time.time()
                
                self.image_id = image_id

                if len(image.shape)==3:
                    # convert image to grayscale
                    self.image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                elif len(image.shape)==2:
                    self.image = image

                

                if self.request_locate:
                    
                    self.image_height, self.image_width = self.image.shape
                    self.image_bytes = self.image.tobytes()
                    # print type of elements in image
                    
                    try:
                        self.init_tracking()
                        self.stub.LocateTask(image_service_pb2.ImageRequest(image=self.image_bytes, width=self.image_width, height=self.image_height))

                    except Exception as e:
                        # destroy the stub and channel
                        self.stub = None
                        self.channel = None
                        print("Error tracking", e)


                if self.save_folder is not None:
                    # save the image
                    cv2.imwrite(os.path.join(self.save_folder, str(image_id) + ".bmp"), self.image)
                    


                self.last_image_time = time.time()

             


        
            except Exception as e:
                print(e)

              

          
        ##### GET requests #####
        @self.app.get("/heartbeat")
        def get_heartbeat():
            self.last_hearbeat_time = time.time()
            return {"success": True, "msg": "Server is running", "data": []}

        @self.app.get("/get_camera_details")
        def get_camera_ids():
            return {"success": True, "msg": "Camera IDs", "data": self.get_camera_ids()}

        @self.app.get("/get_camera_details/{camera_id}")
        def get_camera_details(camera_id: str):
            if camera_id not in self.get_camera_ids():
                return {"success": False, "msg": "Camera ID not found", "data": []}
            return {"success": True, "msg": "Camera details", "data": self.get_camera_details(camera_id)}

        @self.app.get("/get_all_camera_details")
        def get_all_camera_details():
            data = []
            for camera_id in self.get_camera_ids():
                data.append({
                    "camera_id": camera_id,
                    "details": self.get_camera_details(camera_id)
                })
                
                
            return {"success": True, "msg": "All camera details", "data": data}


        @self.app.get("/get/cam_id")
        def get_cam_id():
            return {"success": True, "msg": "Camera ID", "data": self.cam_id}


        @self.app.get("/get/frame_rate")
        def get_frame_rate():
            return {"success": True, "msg": "Frame rate", "data": self.frame_rate}

        @self.app.get("/get/image_source_path")
        def get_image_source_path():
            return {"success": True, "msg": "Image source path", "data": self.image_source_path}

        @self.app.get("/get/exposure")
        def get_exposure():
            return {"success": True, "msg": "Exposure", "data": self.exposure}

        @self.app.get("/get/gain")
        def get_gain():
            return {"success": True, "msg": "Gain", "data": self.gain}

        @self.app.get("/get/is_stream_active")
        def get_is_camera_active():
            if self.is_camera_active:
                return {"success": True, "msg": "Camera is active", "data": [{"camera_id": self.camera_id}]}
            else:
                return {"success": True, "msg": "Camera is not active", "data": []}



        ##### POST requests #####

        # @self.app.get("/start_camera/{camera_id}")
        # def start_camera(camera_id: str):
        #     if self.is_camera_active:
        #         return {"success": False, "msg": "Camera already active", "data": [{"camera_id": self.camera_id}]}
        #     self.camera_id = camera_id
        #     self.is_camera_active = True
        #     self.camera_instance = self.instantiate_camera(camera_id)
        #     self.camera_instance.set_frame_rate(self.frame_rate)
        #     self.camera_instance.set_on_update_callback(on_update_callback)
        #     self.camera_instance.start()
        #     return {"success": True, "msg": "Camera started", "data": []}

        # post request to start camera
        # the post request contains, fps, exposure, gain, image_source_path, is_compressed in the body as json
        @self.app.post("/start_camera/")
        def start_camera(data: dict):
            if self.is_camera_active:
                #return {"success": False, "msg": "Camera already active", "data": [{"camera_id": self.camera_id}]}
                stop_camera_func()

                print("Camera stopped")

            camera_id = data["camera_id"]

            if camera_id not in self.get_camera_ids():
                return {"success": False, "msg": "Camera ID not found", "data": []}

            try:
                self.camera_id = camera_id
                self.is_camera_active = True
                self.camera_instance = self.instantiate_camera(camera_id)
                self.camera_instance.set_image_source_path(data["folder_path"])
                self.camera_instance.set_frame_rate(float(data["fps"]))
                self.camera_instance.set_on_update_callback(on_update_callback)
                self.request_locate = data["request_locate"]
                self.camera_instance.start()


            except Exception as e:

                # print the error
                print(e)

                try:
                    if self.camera_instance:
                        self.camera_instance.stop()
                except:
                    pass

                self.is_camera_active = False
                self.camera_id = None


                return {"success": False, "msg": "Error starting camera", "data": []}
          
            
            return {"success": True, "msg": "Camera started", "data": []}


        def stop_camera_func():

            print("Stopping camera")
            if not self.is_camera_active:
                return {"success": True, "msg": "Camera not active", "data": []}

            self.camera_instance.stop()
            self.is_camera_active = False
            temp = self.camera_id
            self.camera_id = None

            try:
                del self.camera_instance
            except:
                pass

            try:
                if self.websocket is not None:
                    self.websocket.close()

            except:
                #stop the camera
                self.camera_instance.stop()
                self.is_camera_active = False
                self.camera_id = None

                try:
                    del self.camera_instance
                except:
                    pass

                pass




        cv2.destroyAllWindows()

        @self.app.post("/stop_camera/")
        def stop_camera():
            print("Stopping camera")
            if not self.is_camera_active:
                return {"success": True, "msg": "Camera not active", "data": []}

            self.camera_instance.stop()
            self.is_camera_active = False
            temp = self.camera_id
            self.camera_id = None

            try:
                del self.camera_instance
            except:
                pass

            try:
                if self.websocket is not None:
                    self.websocket.close()

            except:
                #stop the camera
                self.camera_instance.stop()
                self.is_camera_active = False
                self.camera_id = None

                try:
                    del self.camera_instance
                except:
                    pass

                pass

           

            return {"success": True, "msg": "Camera stopped", "data": [{"camera_id": temp}]}


        @self.app.post("/start_saving/")
        def start_saving(data: dict):

            relative_path = data["relative_folder_path"]
            self.save_folder = os.path.join(self.root_folder, relative_path)
            # create folder if it doesn't exist
            if not os.path.exists(self.save_folder):
                os.makedirs(self.save_folder)
            
            return {"success": True, "msg": "Saving started", "data": []}


        @self.post("/stop_saving/")
        def stop_saving():
            self.save_folder = None
            return {"success": True, "msg": "Saving stopped", "data": []}


        # websocket endpoint
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await websocket.accept()
            self.websocket = websocket

            last_image_sent_id = -1

            while True:

                try:
                    await asyncio.sleep(0.001)

                    if self.image is None:
                        continue

                    if self.image_id == last_image_sent_id:
                        continue

                    last_image_sent_id = self.image_id                
                    await websocket.send_bytes(cv2.imencode('.jpg', self.image)[1].tobytes() )

                except Exception as e:

                    # close the websocket
                    try:
                        self.websocket.close()
                    except:
                        pass
                    
                    #stop_camera_func()
                    break
                

               


     

        import uvicorn
        uvicorn.run(self.app, host="0.0.0.0", port=port)


def start(port):


    cam_server = CamServer()
    cam_server.initialize(port)


# if __name__ == "__main__":
#     start(4001)

