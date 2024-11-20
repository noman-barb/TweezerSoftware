from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, HTTPException
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
from collections import deque
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import cv2
from fastapi.responses import FileResponse
from typing import List

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        try:
            with serial_lock:
                self.active_connections.remove(websocket)
        except Exception as e:
            print(f"Error disconnecting: {e}")

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

# Heater settings
heater_temp_min = 18.0
heater_temp_max = 37.0
heater_id = "C274"
heater_baud_rate = 9600
heater_timeout = 5
heater_set_point = 20.0
heater_objective_temperature = 20.0
is_dont_send_read_cmd = False

# Chiller settings
chiller_id = "CH826"
chiller_baud_rate = 9600
chiller_timeout = 5
chiller_set_point = 20.0
chiller_liquid_temperature = 20.0
chiller_flow = False


connection_error = False
connection_error_msg = ""


serial_lock = Lock()
start_time = time.time()

def parse_return_data(data, identifier, data_type_func=str):
    try:
        data = data.split(":")
        data_id = data[0].split("_")
        if identifier not in data_id:
            return None
        return data_type_func(data[1].split("_END")[0])
    except Exception as e:
        print(f"Error parsing data: {e}")
        return None

def identify_cmd():
    return "CMD_IDENTIFY_END"

def get_temp_cmd(identifier):
    return f"CMD_GETTEMP{identifier}_END"

def set_temp_cmd(temp):
    return f"CMD_SETTEMP_{temp}_END"

def set_flow_cmd(flow):
    return f"CMD_SETFLOW_{1 if flow else 0}_END"

def get_flow_cmd():
    return "CMD_GETFLOWIF_END"

def send_cmd(ser, cmd):

    with serial_lock:
        ser.flushInput()
        ser.flushOutput()
        ser.write(cmd.encode())
        read_str = ser.readline().decode().strip()
        ser.flushInput()
        ser.flushOutput()
        return read_str

def get_temp(ser, identifier):
    cmd = get_temp_cmd(identifier)
    ret_data = send_cmd(ser, cmd)
    print(f"Received temperature data: {ret_data}")
    return parse_return_data(ret_data, identifier, float)

def get_flow(ser):
    cmd = get_flow_cmd()
    ret_data = send_cmd(ser, cmd)
    print(f"Received flow data: {ret_data}")
    return parse_return_data(ret_data, "FL", lambda x: x == "1")

def find_serial_port(ID):
    ports = list(serial.tools.list_ports.comports())
    ports.reverse()
    for port in ports:
        print(f"Trying to open port {port.device}")
        try:
            ser = serial.Serial(port.device, heater_baud_rate, timeout=heater_timeout)
            ser.dtr = False
            ser.rts = False
            ser.flushInput()
            ser.flushOutput()
            ser.readline()
            print(f"Opened port {port.device}")
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

heater_serial_port = find_serial_port(heater_id)
chiller_serial_port = find_serial_port(chiller_id)

if heater_serial_port is None or chiller_serial_port is None:
    raise Exception(f"Could not find serial port for {heater_id} or {chiller_id}")

print(f"Detected serial port {heater_serial_port} for heater")
print(f"Detected serial port {chiller_serial_port} for chiller")

ser_heater = serial.Serial(heater_serial_port, heater_baud_rate, timeout=heater_timeout)
ser_heater.dtr = False
ser_heater.rts = False
ser_heater.readline()

ser_chiller = serial.Serial(chiller_serial_port, chiller_baud_rate, timeout=chiller_timeout)
ser_chiller.dtr = False
ser_chiller.rts = False
ser_chiller.readline()

def cleanup(signum, frame):
    print("Cleaning up resources...")
    if ser_heater.is_open:
        ser_heater.close()
    if ser_chiller.is_open:
        ser_chiller.close()
    os._exit(0)

class TempRequest(BaseModel):
    temperature: float

class FlowRequest(BaseModel):
    flow: bool

@app.post("/heater/set_temperature")
async def set_heater_temperature(temp_request: TempRequest):
    global heater_objective_temperature, heater_set_point
    requested_temperature = np.around(temp_request.temperature, 1)
    print(f"Setting heater temperature to {requested_temperature}")
    if requested_temperature < heater_temp_min or requested_temperature > heater_temp_max:
        raise HTTPException(status_code=400, detail="Temperature out of range")
    cmd = set_temp_cmd(requested_temperature)
    print(f"Sending command: {cmd}")
    ret_data = send_cmd(ser_heater, cmd)
    return {"success": True, "msg": f"Heater temperature set to {requested_temperature}"}

@app.get("/heater/get_temperature")
async def get_heater_temperature():
    return {"success": True, "msg": f"Heater temperature is {heater_objective_temperature}", "data": {"objective_temperature": heater_objective_temperature, "set_point": heater_set_point}}

@app.post("/chiller/set_temperature")
async def set_chiller_temperature(temp_request: TempRequest):
    global chiller_liquid_temperature, chiller_set_point
    requested_temperature = np.around(temp_request.temperature, 1)
    print(f"Setting chiller temperature to {requested_temperature}")
    cmd = set_temp_cmd(requested_temperature)
    print(f"Sending command: {cmd}")
    ret_data = send_cmd(ser_chiller, cmd)
    return {"success": True, "msg": f"Chiller temperature set to {requested_temperature}"}

@app.post("/chiller/set_flow")
async def set_chiller_flow(flow_request: FlowRequest):
    global chiller_flow
    print(f"Setting chiller flow to {flow_request.flow}")
    cmd = set_flow_cmd(flow_request.flow)
    print(f"Sending command: {cmd}")
    ret_data = send_cmd(ser_chiller, cmd)
    return {"success": True, "msg": f"Chiller flow set to {flow_request.flow}"}

@app.get("/chiller/get_temperature")
async def get_chiller_temperature():
    return {"success": True, "msg": f"Chiller temperature is {chiller_liquid_temperature}", "data": {"objective_temperature": chiller_liquid_temperature, "set_point": chiller_set_point}}

@app.get("/chiller/get_flow")
async def get_chiller_flow():
    return {"success": True, "msg": f"Chiller flow is {'on' if chiller_flow else 'off'}", "data": {"flow": chiller_flow}}

def thread_func_update_temp():
    global heater_objective_temperature, heater_set_point, chiller_liquid_temperature, chiller_set_point, chiller_flow, is_dont_send_read_cmd, connection_error, connection_error_msg
    while True:
        time.sleep(0.25)

        err_msg = ""

        try:
            if is_dont_send_read_cmd:
                continue
            _hot = get_temp(ser_heater, 'OT')
            if _hot is not None:
                heater_objective_temperature = _hot
            _hst = get_temp(ser_heater, 'ST')
            if _hst is not None:
                heater_set_point = _hst

        except Exception as e:
            connection_error = True
            err_msg += "Error communicating with heater"
            
        try:
            _cot = get_temp(ser_chiller, 'CT')
            if _cot is not None:
                chiller_liquid_temperature = _cot
            _cst = get_temp(ser_chiller, 'ST')
            if _cst is not None:
                chiller_set_point = _cst
                print(f"Chiller set point: {chiller_set_point}")
            _flow = get_flow(ser_chiller)
            if _flow is not None:
                chiller_flow = _flow

        except Exception as e:
            connection_error = True
            if len(err_msg) > 0:
                err_msg += " and "
            err_msg += "Error communicating with chiller"

        if connection_error:
            connection_error_msg = err_msg
            print(err_msg)
           

@app.get("/heartbeat")
async def heartbeat():
    if connection_error:
        return {"success": False, "msg": connection_error_msg}


    return {"success": True, "msg": "Heartbeat", "data": {}}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            receive_task = asyncio.create_task(websocket.receive_json())
            broadcast_task = asyncio.create_task(
                manager.broadcast({
                    "heater_set_point": heater_set_point,
                    "heater_objective_temperature": heater_objective_temperature,
                    "chiller_set_point": chiller_set_point,
                    "chiller_liquid_temperature": chiller_liquid_temperature,
                    "chiller_flow": chiller_flow,
                    "connection_error": connection_error,
                    "connection_error_msg": connection_error_msg
                })
            )
            done, pending = await asyncio.wait({receive_task, broadcast_task}, return_when=asyncio.FIRST_COMPLETED)
            if receive_task in done:
                data = receive_task.result()
            else:
                receive_task.cancel()
            await asyncio.sleep(0.5)
    except (WebSocketDisconnect, ConnectionClosed):
        manager.disconnect(websocket)
    finally:
        await websocket.close()

if __name__ == '__main__':
    import uvicorn
    t1 = threading.Thread(target=thread_func_update_temp)
    t1.daemon = True
    t1.start()
    # t2 = threading.Thread(target=thread_worker_update_to_dequee)
    # t2.daemon = True
    # t2.start()
    uvicorn.run(app, host='0.0.0.0', port=4031)
