import asyncio
import websockets
import json
import threading
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import numpy as np
from matplotlib.widgets import Button
import websocket  # websocket-client library

# Global DataFrame to store 'x' and 'y' values
data_df = pd.DataFrame(columns=["x", "y"])

# Lock for thread-safe DataFrame updates
data_lock = threading.Lock()

# Global variables for plots
scat1 = None
scat2 = None
ax1 = None

MAX_DIST = 60
# Variables for selected points
selected_points = []
selected_points_ws = None

async def connect_to_source():
    async with websockets.connect("ws://10.0.63.153:4012/ws") as source_ws:
        print(f"Connected to source: {source_ws.remote_address}")
        async for message in source_ws:
            # Process the message and update the DataFrame
            updated_data = process_message(message)
            update_dataframe(updated_data)

def process_message(message):
    try:
        data = json.loads(message)
        x_values = data.get('x', [])
        y_values = data.get('y', [])
        points = [{"x": x, "y": y} for x, y in zip(x_values, y_values)]
        return points
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return []

def update_dataframe(data):
    with data_lock:
        global data_df
        new_rows = pd.DataFrame(data)
        data_df = new_rows.reset_index(drop=True)

def animate(i):
    with data_lock:
        if not data_df.empty:
            x_data = data_df['x']
            y_data = data_df['y']
            scat1.set_offsets(np.c_[x_data, y_data])
            ax1.set_xlim(0, 1456)
            ax1.set_ylim(0, 1090)

            if selected_points:
                selected_x = [p[0] for p in selected_points]
                selected_y = [p[1] for p in selected_points]
                scat2.set_offsets(np.c_[selected_x, selected_y])



def on_select(event):
    global selected_points
    with data_lock:
        if not data_df.empty:
            fraction = 0.1
            num_points = max(1, int(len(data_df) * fraction))
            filtered_df = data_df[
                (data_df['x'] > 100) & (data_df['x'] < data_df['x'].max() - 100) &
                (data_df['y'] > 100) & (data_df['y'] < data_df['y'].max() - 100)
            ]
            selected_points = []
            attempts = 0
            max_attempts = num_points * 100  # Prevent infinite loop
            while len(selected_points) < num_points and attempts < max_attempts:
                candidate = filtered_df.sample(n=1).iloc[0]
                x_cand, y_cand = candidate['x'], candidate['y']
                is_valid = True
                for x_sel, y_sel in selected_points:
                    distance = ((x_cand - x_sel) ** 2 + (y_cand - y_sel) ** 2) ** 0.5
                    if distance < MAX_DIST:
                        is_valid = False
                        break
                if is_valid:
                    selected_points.append([x_cand, y_cand])
                attempts += 1
            print(f"Selected {len(selected_points)} points.")

  

def on_send(event):
    global selected_points
    with data_lock:
        if selected_points:
            selected_df = pd.DataFrame(selected_points, columns=['x', 'y'])
            selected_df['z'] = 0.0
            selected_df['intensity'] = 1.0

            message = {
                'command': 'update_points',
                'points': {
                    'x_array': selected_df['x'].round(1).tolist(),
                    'y_array': selected_df['y'].round(1).tolist(),
                    'z_array': selected_df['z'].round(1).tolist(),
                    'intensity_array': selected_df['intensity'].round(1).tolist()
                },
                'id': 3242
            }
            try:
                selected_points_ws.send(json.dumps(message))
                print(f"Sent {len(selected_points)} points.")
            except Exception as e:
                print(f"Error sending selected points: {e}")

def main_loop():
    global ax1, scat1, scat2, selected_points
    fig, ax1 = plt.subplots(figsize=(6, 6))
    scat1 = ax1.scatter([], [], color='blue')
    scat2 = ax1.scatter([], [], color='red')
    ax1.set_title("Real-Time Tracked Particles")
    ax1.set_xlabel("x", fontsize=14)
    ax1.set_ylabel("y", fontsize=14)
    plt.subplots_adjust(bottom=0.2)

    ax_button_select = plt.axes([0.3, 0.00, 0.2, 0.075])
    btn_select = Button(ax_button_select, 'Select Points')

 

    ax_button_send = plt.axes([0.5, 0.00, 0.2, 0.075])
    btn_send = Button(ax_button_send, 'Send Points')



    btn_select.on_clicked(on_select)
   
    btn_send.on_clicked(on_send)

    plt.tight_layout()
    ani = FuncAnimation(fig, animate, interval=100)
    plt.show()



async def auto_select_and_send():
    while True:

        try:
            on_select(None)
            on_send(None)
            print("Auto select and send")
            await asyncio.sleep(0.1)

        except Exception as e:
            print(f"Error in auto select and send: {e}")
            await asyncio.sleep(0.5)

if __name__ == "__main__":
    # threading.Thread(target=lambda: asyncio.run(connect_to_source()), daemon=True).start()
    selected_points_ws = websocket.create_connection("ws://10.0.63.153:4041")
    
    # run connect to source and auto select and send in parallel
    threading.Thread(target=lambda: asyncio.run(connect_to_source()), daemon=True).start()
    threading.Thread(target=lambda: asyncio.run(auto_select_and_send()), daemon=True).start()
    main_loop()