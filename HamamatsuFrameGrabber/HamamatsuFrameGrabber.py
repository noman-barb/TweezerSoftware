from fastapi import FastAPI, HTTPException
import serial
import serial.tools.list_ports
from pydantic import BaseModel
import time
from threading import Lock

app = FastAPI()

# Frame Grabber settings
frame_grabber_id = "FR_J37FH"
frame_grabber_baud_rate = 9600
frame_grabber_timeout = 5
frame_grabber_frame_rate = 10

connection_error = False
connection_error_msg = ""

serial_lock = Lock()

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

def get_frame_rate_cmd():
    return "CMD_GETFR_END"

def set_frame_rate_cmd(frame_rate):
    return f"CMD_SETFR_{frame_rate}_END"

def send_cmd(ser, cmd):
    with serial_lock:
        ser.flushInput()
        ser.flushOutput()
        ser.write(cmd.encode())
        read_str = ser.readline().decode().strip()
        ser.flushInput()
        ser.flushOutput()
        return read_str

def get_frame_rate(ser):
    cmd = get_frame_rate_cmd()
    ret_data = send_cmd(ser, cmd)
    print(f"Received frame rate data: {ret_data}")
    return parse_return_data(ret_data, "FR", int)

def find_serial_port(ID):
    ports = list(serial.tools.list_ports.comports())
    ports.reverse()
    for port in ports:
        print(f"Trying to open port {port.device}")
        try:
            ser = serial.Serial(port.device, frame_grabber_baud_rate, timeout=frame_grabber_timeout)
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

frame_grabber_serial_port = find_serial_port(frame_grabber_id)

if frame_grabber_serial_port is None:
    raise Exception(f"Could not find serial port for {frame_grabber_id}")

print(f"Detected serial port {frame_grabber_serial_port} for frame grabber")

ser_frame_grabber = serial.Serial(frame_grabber_serial_port, frame_grabber_baud_rate, timeout=frame_grabber_timeout)
ser_frame_grabber.dtr = False
ser_frame_grabber.rts = False
ser_frame_grabber.readline()

class FrameRateRequest(BaseModel):
    frame_rate: int

@app.post("/frame_grabber/set_frame_rate")
async def set_frame_rate(frame_rate_request: FrameRateRequest):
    global frame_grabber_frame_rate
    requested_frame_rate = frame_rate_request.frame_rate
    print(f"Setting frame rate to {requested_frame_rate}")
    cmd = set_frame_rate_cmd(requested_frame_rate)
    print(f"Sending command: {cmd}")

    loop_counter = 10

    for i in range(loop_counter):

        try:
            ret_data = send_cmd(ser_frame_grabber, cmd)
        
            break
        except Exception as e:
            print(f"Error sending command: {e}")
            pass
        time.sleep(0.5)


    return {"success": True, "msg": f"Frame rate set to {requested_frame_rate}"}

@app.get("/frame_grabber/get_frame_rate")
async def get_frame_rate():
    global frame_grabber_frame_rate, connection_error, connection_error_msg
    
    try:
        _fr = get_frame_rate(ser_frame_grabber)
        if _fr is not None:
            frame_grabber_frame_rate = _fr
    except Exception as e:
        connection_error = True
        connection_error_msg = "Error communicating with frame grabber"
        print(connection_error_msg)

    if connection_error:
        return {"success": False, "msg": connection_error_msg}
    
    return {"success": True, "msg": f"Frame rate is {frame_grabber_frame_rate}", "data": {"frame_rate": frame_grabber_frame_rate}}

@app.get("/heartbeat")
async def heartbeat():
    if connection_error:
        return {"success": False, "msg": connection_error_msg}

    return {"success": True, "msg": "Heartbeat", "data": {}}

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=4051)