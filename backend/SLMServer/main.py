from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
import io
import os

app = FastAPI()

# Setup CORS to allow all
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

@app.websocket("/ws")
async def image_sender(websocket: WebSocket):
    await websocket.accept()  # Accept the WebSocket connection
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
                    img.save(output, format="jpeg")
                    images.append(output.getvalue())
        else:
            print(f"File not found: {img_file}")

    try:
        while True:
            x = 0
            for img_data in images:
                x += 1
                if x % 10 == 0:
                    print(f"Sending image {x}")
                await websocket.send_bytes(img_data)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await websocket.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3010)
