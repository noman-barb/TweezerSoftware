import grpc
import numpy as np
import image_service_pb2
import image_service_pb2_grpc
import time
import sys
import io
import cv2
from PIL import Image
options = [
    ('grpc.max_receive_message_length', 50 * 1024 * 1024),  # 50 MB
    ('grpc.max_send_message_length', 50 * 1024 * 1024),     # 50 MB
    ('grpc.initial_connection_window_size', 32 * 1024 * 1024)  # 32 MB
]

def run():
    
    channel = grpc.insecure_channel('127.0.0.1:50051', options=options)
    stub = image_service_pb2_grpc.ImageServiceStub(channel)

    average_transmission_speed = 0
    average_time_taken = 0
    counter = 0

    # image_height = 2000
    # image_width = 2000
        
    # image_data = np.random.randint(0, 256, (image_height, image_width), dtype=np.uint8)
    # image_bytes = image_data.tobytes()
    # # Calculate the size of the data in megabits
    # data_size_megabits = sys.getsizeof(image_bytes) / 1e6

  

    root_dir = "F:/data_ssd_01/nucleation_kinetics_under_pinning/Set_Vibrational_01/Experiment_1_pinned_free_63x/"
    

            
    for i in range(1, 1000):
        
        
        start_time = time.time()
        
        image_path = f"{root_dir}/img_1_{i}.bmp"

        image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        image_height, image_width = image.shape
        image_bytes = image.tobytes()
        data_size_megabits = sys.getsizeof(image_bytes) / 1e6
        response = stub.LocateTask(image_service_pb2.ImageRequest(image=image_bytes, width=image_width, height=image_height))
        end_time = time.time()

        # Calculate the transmission speed in Mbps
        transmission_speed_mbps = data_size_megabits / (end_time - start_time)
        average_transmission_speed = (average_transmission_speed*counter + transmission_speed_mbps)/(counter+1)
        time_taken = end_time - start_time
        average_time_taken = (average_time_taken*counter + time_taken)/(counter+1)
        
        print(f"Average Transmission speed: {int(average_transmission_speed)} Mbps")
        print(f"Average Time taken: {average_time_taken} seconds")
        counter += 1

if __name__ == '__main__':
    run()
