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

BASE_DIR = "D:/Noman_temp/melting_exps/005/"
IMAGE_DIR = f"{BASE_DIR}/images/"
TEMP_INFO_DIR = f"{BASE_DIR}/temp_info/"

FRAME_RATE = 20 #Hz

LOWER_TEMP = 23.0
HIGHER_TEMP = 30.2


MIN_TEMP = 18.0
STEP_AHEAD = 0.5
STEP_AHEAD_DELAY = 0.1  # seconds
CSV_FILE_PATH = f"{TEMP_INFO_DIR}/temp_events.csv"

# API URLs
BASE_URL = "10.0.63.153:4031"
WEBSOCKET_URL = f"ws://{BASE_URL}/ws"
HEATER_TEMP_URL = f"http://{BASE_URL}/heater/set_temperature"
CHILLER_FLOW_URL = f"http://{BASE_URL}/chiller/set_flow"
WEBSOCKET_URL = f"ws://{BASE_URL}/ws"


FRAME_GRABBER_URL = "http://10.0.63.153:4051/frame_grabber/set_frame_rate/"


class Temperatures:
    def __init__(self):
        self.heater_set_point = -1.0
        self.heater_objective_temperature = -1.0
        self.chiller_set_point = -1.0
        self.chiller_liquid_temperature = -1.0
        self.chiller_flow = -1.0

    # Setters
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

    # Getters
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


# WebSocket listener to update the temperature object
async def websocket_listener(temperatures):
    async with websockets.connect(WEBSOCKET_URL) as websocket:
        while True:
            await asyncio.sleep(0.01)
            try:
                data = await websocket.recv()  # Receive message
                message = json.loads(data)  # Parse JSON message

                # Update the temperatures object based on the received message
                temperatures.set_heater_set_point(message.get("heater_set_point", -1.0))
                temperatures.set_heater_objective_temperature(message.get("heater_objective_temperature", -1.0))
                temperatures.set_chiller_set_point(message.get("chiller_set_point", -1.0))
                temperatures.set_chiller_liquid_temperature(message.get("chiller_liquid_temperature", -1.0))
                temperatures.set_chiller_flow(message.get("chiller_flow", -1.0))

                #print("Updated Temperatures:", temperatures.__dict__)

            except websockets.ConnectionClosed:
                print("WebSocket connection closed.")
                break


# Event handler for detecting new files in the image directory
class NewImageHandler(FileSystemEventHandler):
    def __init__(self, temperatures, csv_writer):
        self.start_time = time.time()  # To track experimental time in ms
        self.temperatures = temperatures
        self.csv_writer = csv_writer  # Pass the CSV writer to append data
        self.frame_times = deque(maxlen=10)  # Store timestamps of the last 10 frames
        self.event_count = 0
        

    def on_created(self, event):
    
       
        if event.is_directory:
            return
        
        self.event_count += 1

        elapsed_time_ms = int((time.time() - self.start_time) * 1000)
        file_name = os.path.basename(event.src_path)
        
        
        
        fps = -1.0
        
        try:
            # Calculate FPS
            self.frame_times.append(time.time())
            if len(self.frame_times) >= 2:
                time_diff = self.frame_times[-1] - self.frame_times[0]
                fps = (len(self.frame_times) - 1) / time_diff
            else:
                fps = 0.0
        except:
            print("Failed to calculate fps")
            pass

        # round fps to 2 decimal places
        fps = round(fps, 2)

       

        # Log the temperatures and time to CSV
        elapsed_time_ms = int((time.time() - self.start_time) * 1000)  # Get time in ms
        file_name = os.path.basename(event.src_path)
        
        # Append the temperature and FPS data to CSV
        self.save_to_csv(file_name, elapsed_time_ms, fps)
      

    def save_to_csv(self, file_name, elapsed_time_ms, fps):
            self.csv_writer.writerow({
                "file_name": file_name,
                "time_ms": elapsed_time_ms,
                "fps": fps,  # Add FPS to the CSV row
                "heater_set_point": self.temperatures.get_heater_set_point(),
                "heater_objective_temperature": self.temperatures.get_heater_objective_temperature(),
                "chiller_set_point": self.temperatures.get_chiller_set_point(),
                "chiller_liquid_temperature": self.temperatures.get_chiller_liquid_temperature(),
                "chiller_flow": self.temperatures.get_chiller_flow(),
            })

            if self.event_count % int(FRAME_RATE) !=0:
                return

            # print the data to the console in a nice format for better readability and delete previous console output
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
                      "chiller_set_point", "chiller_liquid_temperature", "chiller_flow"]  # Add "fps"
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
    # 1. set heater temperature to MIN_TEMP

    while True:
        await asyncio.sleep(1)

        try:
            print("Setting heater temperature to MIN_TEMP")
            response = requests.post(HEATER_TEMP_URL, json={"temperature": MIN_TEMP})
            print(response.json())

            break

        except Exception as e:
            print(e)
            pass
        

    # 2. set chiller flow to True
    while True:
        await asyncio.sleep(1)
        try:
            print("Setting chiller flow to True")
            response = requests.post(CHILLER_FLOW_URL, json={"flow": True})
            print(response.json())
            break

        
        except Exception as e:
            print(e)
            pass
        

    # 3. keep monitoring the heater_objective_temperature till it reaches LOWER_TEMP
    obj_temp = temperatures.get_heater_objective_temperature() 
    
    while obj_temp<0  or obj_temp > LOWER_TEMP:
        obj_temp = temperatures.get_heater_objective_temperature() 
        print(f"Current heater objective temperature: {temperatures.get_heater_objective_temperature()} / Target: {LOWER_TEMP}")
        await asyncio.sleep(1)

    # 4. set chiller flow to False

    while True:
        await asyncio.sleep(1)
        try:
            print("Setting chiller flow to False")
            response = requests.post(CHILLER_FLOW_URL, json={"flow": False})
            print(response.json())

            break
        
        except Exception as e:
            print(e)
            pass
            

    while True:
        await asyncio.sleep(1)

        try:
            # 5. set heater temperature to LOWER_TEMP
            print("Setting heater temperature to LOWER_TEMP")
            response = requests.post(HEATER_TEMP_URL, json={"temperature": LOWER_TEMP})
            print(response.json())
            break

        except Exception as e:
            print(e)
            pass
            
    
    
async def equilibrate_to_slowly(temperatures, set_point):
 
 
    while True:
        await asyncio.sleep(1)
        try:
            print("Setting chiller flow to False")
            response = requests.post(CHILLER_FLOW_URL, json={"flow": False})
            print(response.json())
            break

        except Exception as e:
            print(e)
            pass
 

    while True:
        await asyncio.sleep(1)
        try:
            print(f"Setting heater temperature to {set_point} ")
            response = requests.post(HEATER_TEMP_URL, json={"temperature": set_point})
            print(response.json())
            break

        except Exception as e:
            print(e)
            pass
    
    obj_temp = temperatures.get_heater_objective_temperature() 

    while obj_temp < 0 or abs(obj_temp - set_point) > 0.2:
        await asyncio.sleep(1)
        obj_temp = temperatures.get_heater_objective_temperature() 
        
        set_obj_temp = 0
        
        if obj_temp > set_point:
            set_obj_temp = obj_temp - 0.5
        else:
            set_obj_temp = obj_temp + 0.5
        
        print(f"Equilibrating Current heater objective temperature: {temperatures.get_heater_objective_temperature()} / Target: {set_point}")
        
        
        while True:
            await asyncio.sleep(1)

            try:
                response = requests.post(HEATER_TEMP_URL, json={"temperature": set_obj_temp})
                print(response.json())
                break

            except Exception as e:
                print(e)
                pass
                
        
        await asyncio.sleep(5)
        
        
    while True:
        await asyncio.sleep(1)

        try:
            print(f"Setting heater temperature to {set_point} / Target: {set_point}")
            response = requests.post(HEATER_TEMP_URL, json={"temperature": set_point})
            print(response.json())
            break

        except Exception as e:
            print(e)
            pass
    
    print("waiting for final equilibration")
    
    obj_temp = temperatures.get_heater_objective_temperature() 

    while obj_temp < 0 or abs(obj_temp - set_point) > 0.2:
        await asyncio.sleep(STEP_AHEAD_DELAY)
    
    
        obj_temp = temperatures.get_heater_objective_temperature()
        print(f"Equilibrating Current heater objective temperature: {temperatures.get_heater_objective_temperature()} / Target: {set_point}")
        

   
    




async def set_frame_rate(frame_rate):

    while True:
        await asyncio.sleep(1)
        try:
            response = requests.post(FRAME_GRABBER_URL, json={"frame_rate": frame_rate})
            print(response.json())
            break

        except Exception as e:
            print(e)
            pass


async def higher_temp(temperatures):
    # 1. set chiller flow to False

    while True:
        await asyncio.sleep(1)
        try:
            print("Setting chiller flow to False")
            response = requests.post(CHILLER_FLOW_URL, json={"flow": False})
            print(response.json())
            break

        except Exception as e:
            print(e)
            pass


    # 2. increment heater temperature by STEP_AHEAD until it reaches HIGHER_TEMP
    current_temp = temperatures.get_heater_objective_temperature()
    while current_temp < HIGHER_TEMP:
        await asyncio.sleep(1)
        current_temp = temperatures.get_heater_objective_temperature()
        current_temp += STEP_AHEAD


        while True:
            await asyncio.sleep(1)
            try:
                print(f"Setting heater temperature to {current_temp} / Target: {HIGHER_TEMP}")
                response = requests.post(HEATER_TEMP_URL, json={"temperature": current_temp})
                print(response.json())
                break

            except Exception as e:
                print(e)
                pass
      
        await asyncio.sleep(STEP_AHEAD_DELAY)



async def wait(time_seconds, message="Waiting"):
    for i in range(time_seconds):
        print(f"{message}: {i}/{time_seconds}")
        await asyncio.sleep(1)

async def experimental_protocol(temperatures):

 
    # Implement your experimental protocol here

    # 1. Lower the temperature to LOWER_TEMP
    # 2. start recording images at FRAME_RATE for 10 minutes
    # 3. Increase the temperature to HIGHER_TEMP
    # 4. Be there for 10 minutes
    # 5. Lower the temperature to LOWER_TEMP
    # 6. Be there for 10 minutes
    # 7. stop recording images
    # 8. Done


    await set_frame_rate(0)
    input("Start?")

    # Lower the temperature to LOWER_TEMP
    await equilibrate_to_slowly(temperatures, LOWER_TEMP)
    # Start recording images at FRAME_RATE
    await set_frame_rate(FRAME_RATE)
    # Wait for 10 minutes
    await wait(600, "Lower temperature")
    await higher_temp(temperatures)
    # Wait for 10 minutes
    await wait(600, "Higher temperature")
    # Lower the temperature to LOWER_TEMP
    await lower_temp(temperatures)
    # Wait for 10 minutes
    await wait(600, "Lower temperature")
    # Stop recording images
    await set_frame_rate(0)


    return True


# Main function to run the WebSocket listener and other tasks concurrently
async def main():
    
    temperatures = Temperatures()

    # Run WebSocket listener, image monitoring, and experimental protocol concurrently using asyncio.gather
    await asyncio.gather(
        websocket_listener(temperatures),
        save_temperatures_with_filenames(temperatures),
        experimental_protocol(temperatures),
    )


if __name__ == "__main__":
   
    
    asyncio.run(main())