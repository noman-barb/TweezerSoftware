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
    except websockets.exceptions.ConnectionClosedError:
        print(f"Client disconnected: {websocket.remote_address}")
    except Exception as e:
        print(f"Error with client {websocket.remote_address}: {e}")
    finally:
        # Remove client from the set of connected clients
        connected_clients.remove(websocket)

async def connect_to_source():
    while True:
        try:
            async with websockets.connect("ws://10.0.63.153:4011/ws") as source_ws:
                print(f"Connected to source: {source_ws.remote_address}")
                async for message in source_ws:
                    # Update global data and broadcast to all clients
                    size_of_message = len(message)
                    print(f"Received message size: {size_of_message}")
                    updated_data = process_message(message)
                    global_data.update(updated_data)
                    await broadcast_message(message)
        except (websockets.exceptions.ConnectionClosedError, ConnectionRefusedError) as e:
            print(f"Connection to source lost: {e}. Retrying in 5 seconds...")
            await asyncio.sleep(5)
        except Exception as e:
            print(f"Unexpected error: {e}. Retrying in 5 seconds...")
            await asyncio.sleep(5)

async def broadcast_message(message):
    # Send the message to all connected clients
    if connected_clients:
        print("Broadcasting")
        disconnected_clients = set()
        for client in connected_clients:
            try:
                await client.send(message)
            except websockets.exceptions.ConnectionClosedError:
                print(f"Client disconnected during broadcast: {client.remote_address}")
                disconnected_clients.add(client)
            except Exception as e:
                print(f"Error sending to client {client.remote_address}: {e}")
                disconnected_clients.add(client)
        connected_clients.difference_update(disconnected_clients)

async def main():
    # Start the source connection in the background
    asyncio.create_task(connect_to_source())

    # Start the relay server, binding to all interfaces (0.0.0.0)
    try:
        async with websockets.serve(relay_server, "0.0.0.0", 4012):
            print("Relay server started on ws://0.0.0.0:4012 (all interfaces)")
            await asyncio.Future()  # Run forever
    except Exception as e:
        print(f"Server error: {e}")

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
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Server shutdown requested.")
    except Exception as e:
        print(f"Unexpected error in main: {e}")