import grpc
import hologram_pb2
import hologram_pb2_grpc
import cv2
import time
import numpy as np


def run():
    channel = grpc.insecure_channel('10.0.63.195:50051')
    stub = hologram_pb2_grpc.HologramGeneratorServiceStub(channel)

    height = 1152
    width = 1920
    depth = 8
    iterations = 50
    is_rgb = False
    is_apply_affine = True


    for i in range(2000):

        start_time = time.time()

        n = 100
        x_array = np.random.uniform(0, width, n).astype(np.float32)
        y_array = np.random.uniform(0, height, n).astype(np.float32)
        z_array = np.zeros(n, dtype=np.float32)
        intensity_array = np.ones(n, dtype=np.float32)

        # x_array = np.array([-10, 10], dtype=np.float32)
        # y_array = np.array([0, 0], dtype=np.float32)

        x_array_bytes = x_array.tobytes()
        y_array_bytes = y_array.tobytes()
        z_array_bytes = z_array.tobytes()
        intensity_array_bytes = intensity_array.tobytes()

        print("Generate: ", time.time() - start_time )




        start_time = time.time()

        request = hologram_pb2.HologramRequest(
            height=height,
            width=width,
            depth=depth,
            iterations=iterations,
            is_rgb=is_rgb,
            is_apply_affine=is_apply_affine,
            x_array=x_array_bytes,
            y_array=y_array_bytes,
            z_array=z_array_bytes,
            intensity_array=intensity_array_bytes,
            SLM_X_0=10, SLM_Y_0=10, CAM_X_0=10, CAM_Y_0=10,
            SLM_X_1=-10, SLM_Y_1=-10, CAM_X_1=-10, CAM_Y_1=-10,
            SLM_X_2=10, SLM_Y_2=-10, CAM_X_2=10, CAM_Y_2=-10
        )

        response = stub.GenerateHologram(request)

        hologram_image_bytes = response.hologram_image
        height = response.height
        width = response.width
        hologram_image_np = np.frombuffer(hologram_image_bytes, dtype=np.uint8)
        hologram_image_np = hologram_image_np.reshape((height, width))
        # hologram_image_np = hologram_image_np.get()

        print("Response: ", time.time() - start_time )
        # cv2.imwrite('hologram_image.png', hologram_image_np)

        time.sleep(0.1)

if __name__ == '__main__':
    run()