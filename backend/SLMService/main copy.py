import asyncio
import websockets
import os
from PIL import Image
import io

async def image_sender(websocket, path):
    img_directory = "F:/data_ssd_01/nucleation_kinetics_under_pinning/Set_Vibrational_01/Experiment_1_pinned_free_63x"
    num_images = 1000  # Total number of images
    images = []

    # Preload images and compress them to JPEG
    for i in range(1, num_images + 1):
        img_file = f"img_1_{i}.bmp"
        print(f"Loading image: {img_file}")
        file_path = os.path.join(img_directory, img_file)
        if os.path.exists(file_path):
            with Image.open(file_path) as img:
                with io.BytesIO() as output:
                    img.save(output, format="bmp")
                    images.append(output.getvalue())
        else:
            print(f"File not found: {img_file}")

    # Stream compressed images
    
    while True:
        x = 0
        for img_data in images:
            
            x += 1

            if x % 10 == 0:
                print(f"Sending image {x}")
            # await websocket.send(img_data)
            # before sending, compress the image to JPEG
            # compress the image to JPEG
            with Image.open(io.BytesIO(img_data)) as img:
                with io.BytesIO() as output:
                    img.save(output, format="jpeg")
                    await websocket.send(output.getvalue())

async def main():
    async with websockets.serve(image_sender, "0.0.0.0", 3010):
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())