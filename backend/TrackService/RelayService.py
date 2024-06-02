import asyncio
import websockets
import json

# Global state to store data received from the source
global_data = {}

# Set to store connected relay clients
connected_clients = set()

async def relay_server(websocket, path):
    # Add new client to the set of connected clients
    connected_clients.add(websocket)
    print(f"Client connected: {websocket.remote_address}")

    try:
        async for message in websocket:
            # Process and update global data (replace with your logic)
            updated_data = process_message(message)
            global_data.update(updated_data)
    except websockets.exceptions.ConnectionClosed:
        print(f"Client disconnected: {websocket.remote_address}")
    finally:
        # Remove client from the set of connected clients
        connected_clients.remove(websocket)

async def connect_to_source():
    async with websockets.connect("ws://10.0.63.153:4011/ws") as source_ws:
        print(f"Connected to source: {source_ws.remote_address}")
        async for message in source_ws:
            # Update global data and broadcast to all clients
            updated_data = process_message(message)
            global_data.update(updated_data)
            await broadcast_message(message)

async def broadcast_message(message):
    # Send the message to all connected clients
    if connected_clients:
        await asyncio.gather(*(client.send(message) for client in connected_clients))

async def main():
    # Start the source connection in the background
    asyncio.create_task(connect_to_source())

    # Start the relay server, binding to all interfaces (0.0.0.0)
    async with websockets.serve(relay_server, "0.0.0.0", 4012):
        print("Relay server 0 started on ws://0.0.0.0:4031 (all interfaces)")
        await asyncio.Future()  # Run forever

# Placeholder function to process messages from source
def process_message(message):
    """
    Processes the received message from the source and returns a dictionary
    to update the global state.

    Args:
        message (str): The message received from the source websocket.

    Returns:
        dict: A dictionary representing the updated data for the global state.
    """
    try:
        data = json.loads(message)
        # Process data and return the updated dictionary
        return data
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return {}

if __name__ == "__main__":
    asyncio.run(main())
