import asyncio
import websockets
import json
import time
import os
import csv
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from collections import deque
from typing import Callable, Any
from functools import partial

BASE_DIR = "f:/temp/"
IMAGE_DIR = f"{BASE_DIR}/images/"
TEMP_INFO_DIR = f"{BASE_DIR}/temp_info/"

FRAME_RATE = 20  # Hz
LOWER_TEMP = 24.0
HIGHER_TEMP = 29.2
MIN_TEMP = 18.0
STEP_AHEAD = 0.5
STEP_AHEAD_DELAY = 0.1  # seconds
CSV_FILE_PATH = f"{TEMP_INFO_DIR}/temp_events.csv"

# API URLs
BASE_URL = "10.0.63.153:4031"
WEBSOCKET_URL = f"ws://{BASE_URL}/ws"
WEBSOCKET_URL_4041 = f"ws://10.0.63.153:4041/ws"
HEATER_TEMP_URL = f"http://{BASE_URL}/heater/set_temperature"
CHILLER_FLOW_URL = f"http://{BASE_URL}/chiller/set_flow"
FRAME_GRABBER_URL = "http://10.0.63.153:4051/frame_grabber/set_frame_rate/"

global_data_4041 = {}

class Temperatures:
    def __init__(self):
        self.heater_set_point = -1.0
        self.heater_objective_temperature = -1.0
        self.chiller_set_point = -1.0
        self.chiller_liquid_temperature = -1.0
        self.chiller_flow = -1.0

    def set_heater_set_point(self, value):
        self.heater_set_point = value
        return self

    def set_heater_objective_temperature(self, value):
        self.heater_objective_temperature = value
        return self

    def set_chiller_set_point(self, value):
        self.chiller_set_point = value
        return self

    def set_chiller_liquid_temperature(self, value):
        self.chiller_liquid_temperature = value
        return self

    def set_chiller_flow(self, value):
        self.chiller_flow = value
        return self

    def get_heater_set_point(self):
        return self.heater_set_point

    def get_heater_objective_temperature(self):
        return self.heater_objective_temperature

    def get_chiller_set_point(self):
        return self.chiller_set_point

    def get_chiller_liquid_temperature(self):
        return self.chiller_liquid_temperature

    def get_chiller_flow(self):
        return self.chiller_flow

async def retry_request(request_func: Callable, max_retries: int = 5, delay: float = 1.0) -> Any:
    """Helper function to retry HTTP requests with exponential backoff"""
    for attempt in range(max_retries):
        try:
            response = await asyncio.to_thread(request_func)
            print(response.json())
            return response
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            print(f"Request failed: {e}. Retrying in {delay} seconds...")
            await asyncio.sleep(delay)
            delay *= 2

async def wait_for_temperature(temperatures: Temperatures, 
                             condition: Callable[[float], bool],
                             message: str,
                             check_interval: float = 1.0) -> None:
    """Helper function to wait for a temperature condition"""
    while True:
        temp = temperatures.get_heater_objective_temperature()
        if temp >= 0 and condition(temp):
            break
        print(f"{message}: {temp}")
        await asyncio.sleep(check_interval)

async def websocket_listener(temperatures):
    async with websockets.connect(WEBSOCKET_URL) as websocket:
        while True:
            await asyncio.sleep(0.01)
            try:
                data = await websocket.recv()
                message = json.loads(data)
                temperatures.set_heater_set_point(message.get("heater_set_point", -1.0))
                temperatures.set_heater_objective_temperature(message.get("heater_objective_temperature", -1.0))
                temperatures.set_chiller_set_point(message.get("chiller_set_point", -1.0))
                temperatures.set_chiller_liquid_temperature(message.get("chiller_liquid_temperature", -1.0))
                temperatures.set_chiller_flow(message.get("chiller_flow", -1.0))
            except websockets.ConnectionClosed:
                print("WebSocket connection closed.")
                break

async def websocket_listener_4041():
    global global_data_4041
    async with websockets.connect(WEBSOCKET_URL_4041) as websocket:
        while True:
            await asyncio.sleep(0.01)
            try:
                data = await websocket.recv()
                global_data_4041 = json.loads(data)
            except websockets.ConnectionClosed:
                print("WebSocket connection closed.")
                break

class NewImageHandler(FileSystemEventHandler):
    def __init__(self, temperatures, csv_writer):
        self.start_time = time.time()
        self.temperatures = temperatures
        self.csv_writer = csv_writer
        self.frame_times = deque(maxlen=10)
        self.event_count = 0

    def on_created(self, event):
        if event.is_directory:
            return
        
        self.event_count += 1
        elapsed_time_ms = int((time.time() - self.start_time) * 1000)
        file_name = os.path.basename(event.src_path)
        
        fps = -1.0
        try:
            self.frame_times.append(time.time())
            if len(self.frame_times) >= 2:
                time_diff = self.frame_times[-1] - self.frame_times[0]
                fps = (len(self.frame_times) - 1) / time_diff
            else:
                fps = 0.0
        except:
            print("Failed to calculate fps")
        
        fps = round(fps, 2)
        self.save_to_csv(file_name, elapsed_time_ms, fps)
        print(f"Global Data 4041: {global_data_4041}")

    def save_to_csv(self, file_name, elapsed_time_ms, fps):
        self.csv_writer.writerow({
            "file_name": file_name,
            "time_ms": elapsed_time_ms,
            "fps": fps,
            "heater_set_point": self.temperatures.get_heater_set_point(),
            "heater_objective_temperature": self.temperatures.get_heater_objective_temperature(),
            "chiller_set_point": self.temperatures.get_chiller_set_point(),
            "chiller_liquid_temperature": self.temperatures.get_chiller_liquid_temperature(),
            "chiller_flow": self.temperatures.get_chiller_flow(),
        })

        if self.event_count % int(FRAME_RATE) == 0:
            print("\n\n")
            print(f"File Name: {file_name}")
            print(f"Time: {elapsed_time_ms} ms")
            print(f"FPS: {fps}")
            print(f"Heater Set Point: {self.temperatures.get_heater_set_point()}")
            print(f"Heater Objective Temperature: {self.temperatures.get_heater_objective_temperature()}")
            print(f"Chiller Set Point: {self.temperatures.get_chiller_set_point()}")
            print(f"Chiller Liquid Temperature: {self.temperatures.get_chiller_liquid_temperature()}")
            print(f"Chiller Flow: {self.temperatures.get_chiller_flow()}")
            print("\n\n")

async def save_temperatures_with_filenames(temperatures):
    with open(CSV_FILE_PATH, mode='a', newline='') as f:
        fieldnames = ["file_name", "time_ms", "fps", "heater_set_point", "heater_objective_temperature",
                     "chiller_set_point", "chiller_liquid_temperature", "chiller_flow"]
        csv_writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        if f.tell() == 0:
            csv_writer.writeheader()

        event_handler = NewImageHandler(temperatures, csv_writer)
        observer = Observer()
        observer.schedule(event_handler, path=IMAGE_DIR, recursive=False)
        observer.start()

        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()

async def lower_temp(temperatures):
    await retry_request(
        lambda: requests.post(HEATER_TEMP_URL, json={"temperature": MIN_TEMP})
    )
    
    await retry_request(
        lambda: requests.post(CHILLER_FLOW_URL, json={"flow": True})
    )
    
    await wait_for_temperature(
        temperatures,
        lambda temp: temp <= LOWER_TEMP,
        f"Current temperature: {temperatures.get_heater_objective_temperature()} / Target: {LOWER_TEMP}"
    )
    
    await retry_request(
        lambda: requests.post(CHILLER_FLOW_URL, json={"flow": False})
    )
    
    await retry_request(
        lambda: requests.post(HEATER_TEMP_URL, json={"temperature": LOWER_TEMP})
    )

async def equilibrate_to_slowly(temperatures, set_point):
    await retry_request(
        lambda: requests.post(CHILLER_FLOW_URL, json={"flow": False})
    )
    
    await retry_request(
        lambda: requests.post(HEATER_TEMP_URL, json={"temperature": set_point})
    )

    while True:
        obj_temp = temperatures.get_heater_objective_temperature()
        if obj_temp >= 0 and abs(obj_temp - set_point) <= 0.2:
            break
            
        set_obj_temp = obj_temp + 0.5 if obj_temp < set_point else obj_temp - 0.5
        print(f"Equilibrating temperature: {obj_temp} / Target: {set_point}")
        
        await retry_request(
            lambda: requests.post(HEATER_TEMP_URL, json={"temperature": set_obj_temp})
        )
        await asyncio.sleep(5)
    
    await retry_request(
        lambda: requests.post(HEATER_TEMP_URL, json={"temperature": set_point})
    )
    
    await wait_for_temperature(
        temperatures,
        lambda temp: abs(temp - set_point) <= 0.2,
        f"Final equilibration: {temperatures.get_heater_objective_temperature()} / Target: {set_point}",
        STEP_AHEAD_DELAY
    )

async def set_frame_rate(frame_rate):
    await retry_request(
        lambda: requests.post(FRAME_GRABBER_URL, json={"frame_rate": frame_rate})
    )

async def higher_temp(temperatures):
    await retry_request(
        lambda: requests.post(CHILLER_FLOW_URL, json={"flow": False})
    )

    current_temp = temperatures.get_heater_objective_temperature()
    while current_temp < HIGHER_TEMP:
        current_temp += STEP_AHEAD
        await retry_request(
            lambda: requests.post(HEATER_TEMP_URL, json={"temperature": current_temp})
        )
        await asyncio.sleep(STEP_AHEAD_DELAY)

async def wait(time_seconds, message="Waiting"):
    for i in range(time_seconds):
        print(f"{message}: {i}/{time_seconds}")
        await asyncio.sleep(1)

async def experimental_protocol(temperatures):
    await set_frame_rate(0)
    input("Start?")

    await equilibrate_to_slowly(temperatures, LOWER_TEMP)

    await set_frame_rate(15)
    await wait(60*1, "Lower temperature")

    await set_frame_rate(2)
    await wait(60*1, "Lower temperature")

    await set_frame_rate(10)
    await higher_temp(temperatures)
    await wait(60*1, "Higher temperature")


    await lower_temp(temperatures)
    await wait(60*1, "Lower temperature")

    await set_frame_rate(2)
    await wait(60*1, "Lower temperature")
    await set_frame_rate(0)

    return True

async def main():
    temperatures = Temperatures()
    await asyncio.gather(
        websocket_listener(temperatures),
        websocket_listener_4041(),
        save_temperatures_with_filenames(temperatures),
        experimental_protocol(temperatures),
    )

if __name__ == "__main__":
    asyncio.run(main())