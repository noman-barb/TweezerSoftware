from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from websockets.exceptions import ConnectionClosed
from fastapi.templating import Jinja2Templates
import signal
import serial
import serial.tools.list_ports
from pydantic import BaseModel
import os
import time
import numpy as np
import threading
import asyncio
from threading import Lock
from fastapi.middleware.cors import CORSMiddleware
# import dequeue for storing the data
from collections import deque


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except RuntimeError as e:
                print(f"RuntimeError: {e}")
                self.disconnect(connection)
            except WebSocketDisconnect:
                self.disconnect(connection)
            except ConnectionClosed:
                self.disconnect(connection)




app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)



manager = ConnectionManager()

temp_min = 18.0
temp_max = 37.0
ID = "C274"
BAUD_RATE = 9600
timeout = 5
set_point = 20.0
objective_temperature = 20.0
is_dont_send_read_cmd = False

# deques for storing the data
max_len = 1000
objective_temperature_deque = deque(maxlen=1000)
set_point_deque = deque(maxlen=1000)
time_deque = deque(maxlen=1000)





        

serial_lock = Lock()

def parse_return_data(data, identifier, data_type_func = str):

    try:

        data = data.split(":")

        # now split data[0] by _
        data_id = data[0].split("_")

        # now check if the identifier is in the data_id
        if not identifier in data_id:
            return None

        # now split data[1] by _ and get the first element
        return data_type_func( data[1].split("_END")[0])

    except Exception as e:
        print(f"Error parsing data: {e}")
        return None

    # example data is DATA_ID:C274_
    # i need to get C274
    # split the data by :
    
def identify_cmd():
    return "CMD_IDENTIFY_END"

def get_temp_cmd(identifier):
    return f"CMD_GETTEMP{identifier}_END"

def set_temp_cmd(temp):
    return f"CMD_SETTEMP_{temp}_END"

def send_cmd(ser, cmd):
    with serial_lock:
        ser.flushInput()
        ser.flushOutput()
        ser.write(cmd.encode())
        read_str = ser.readline().decode().strip()
        ser.flushInput()
        ser.flushOutput()
        return read_str

def read_data(ser):
    return ser.readline().decode().strip()

def get_temp(ser, identifier):
    cmd = get_temp_cmd(identifier)
    ret_data = send_cmd(ser, cmd)
    return parse_return_data(ret_data, identifier, float)


# Function to find the correct serial port
def find_serial_port(ID):
    ports = list(serial.tools.list_ports.comports())
    # reverse the list
    ports.reverse()
    for port in ports:
        print(f"Trying to open port {port.device}")
        try:
            # SET DTR AND RTS TO false
            ser = serial.Serial(port.device, BAUD_RATE, timeout=timeout)
            ser.dtr = False
            ser.rts = False
            ser.flushInput()  # Flush input buffer
            ser.flushOutput()  # Flush output buffer
            ser.readline()
            print(f"Opened port {port.device}")
            # send ascii command to the device
            ser.write(b"CMD_IDENTIFY_END")
            print("Sent IDENTIFY command")
            response = ser.readline().decode().strip()
            print(f"Received response: {response}")
            ser.close()
            identifier = parse_return_data(response, "ID", str)
            print(f"Identifier: {identifier}")
            if identifier == ID:
                print(f"Found device on port {port.device}")
                return port.device
        except (OSError, serial.SerialException) as e:
            print(f"Failed to open port {port.device}: {e}")
    return None



SERIAL_PORT = find_serial_port(ID)
if SERIAL_PORT is None:
    raise Exception(f"Could not find serial port for {ID}")

print(f"Using serial port {SERIAL_PORT}")

# Open the serial connection
ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=timeout)
# set dtr and rts to false
ser.dtr = False
ser.rts = False
# read any data that may be in the buffer
ser.readline()




def cleanup(signum, frame):
    print("Cleaning up resources...")
    if ser.is_open:
        ser.close()
    os._exit(0)


class TempRequest(BaseModel):
    temperature: float

@app.post("/set_temperature")
async def set_temperature(temp_request: TempRequest):
    global objective_temperature, set_point
   
    # round the temperature to 1 decimal place
    requested_temperature = np.around(temp_request.temperature, 1)
    print(f"Setting temperature to {requested_temperature}")
    
    # check for min max
    if requested_temperature < temp_min or requested_temperature > temp_max:
        raise HTTPException(status_code=400, detail="Temperature out of range")

    # set the temperature
    cmd = set_temp_cmd(requested_temperature)
    print(f"Sending command: {cmd}")
    ret_data = send_cmd(ser, cmd)
    return {"success": True, "msg": f"Temperature set to {requested_temperature}"}


def thread_fucn_update_temp():
    global objective_temperature, set_point, is_dont_send_read_cmd
    while True:
        time.sleep(0.25)
        if is_dont_send_read_cmd:
            continue
        _ot = get_temp(ser, 'OT')
        if _ot is not None:
            objective_temperature = _ot
            
        _st = get_temp(ser, 'ST')
        if _st is not None:
            set_point = _st

        #print(f"Objective temperature is {_ot}, set point is {_st}")
        
# thread worker to update the temperature data every 5 seconds by reading the data from objective_temperaturem and set_point
def thread_worker_update_to_dequee():
    global objective_temperature, set_point, objective_temperature_deque, set_point_deque, time_deque
    while True:
        time.sleep(5)
        # get the current time
        current_time = time.time()
        # push the data to the deques
        objective_temperature_deque.append(objective_temperature)
        set_point_deque.append(set_point)
        time_deque.append(current_time)




@app.get("/heartbeat")
async def heartbeat():
    return {"success": True, "msg": "Heartbeat", "data":{}}

@app.get("/get_temperature")
async def get_temperature():
    return {"success": True, "msg": f"Temperature is {objective_temperature}", "data": {"objective_temperature": objective_temperature, "set_point": set_point}}


        
# web sockets part
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            receive_task = asyncio.create_task(websocket.receive_json())
            broadcast_task = asyncio.create_task(
                manager.broadcast({"set_point": set_point, "objective_temperature": objective_temperature,
                
                "previous_objective_temperature": list(objective_temperature_deque),
                "previous_set_point": list(set_point_deque),
                "previous_time": list(time_deque)
                
                })
                
            )

            done, pending = await asyncio.wait({receive_task, broadcast_task}, return_when=asyncio.FIRST_COMPLETED)

            if receive_task in done:
                data = receive_task.result()
            else:
                receive_task.cancel()

            await asyncio.sleep(0.25)  # sleep for 0.25 seconds
    except (WebSocketDisconnect, ConnectionClosed):
        manager.disconnect(websocket)
    finally:
        await websocket.close()




if __name__ == '__main__':
    import uvicorn
    t1 = threading.Thread(target=thread_fucn_update_temp)
    t1.daemon = True
    t1.start()
    t2 = threading.Thread(target=thread_worker_update_to_dequee)
    t2.daemon = True
    t2.start()
    uvicorn.run(app, host='0.0.0.0', port=4031)