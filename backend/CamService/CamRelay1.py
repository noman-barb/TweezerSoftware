import asyncio
import websockets

# Set to store connected relay clients
connected_clients = set()

async def relay_server(websocket, path):
    # Add new client to the set of connected clients
    connected_clients.add(websocket)
    print(f"Client connected: {websocket.remote_address}")

    try:
        async for message in websocket:
            # Relay the exact binary message to all clients
            await broadcast_message(message)
    except websockets.exceptions.ConnectionClosed:
        print(f"Client disconnected: {websocket.remote_address}")
    finally:
        # Remove client from the set of connected clients
        connected_clients.remove(websocket)

async def connect_to_source():
    async with websockets.connect("ws://10.0.63.153:4001/ws") as source_ws:
        print(f"Connected to source: {source_ws.remote_address}")
        async for message in source_ws:
            # Relay the exact binary message to all clients
            await broadcast_message(message)

async def broadcast_message(message):
    # Send the message to all connected clients
    if connected_clients:
        await asyncio.gather(*(client.send(message) for client in connected_clients))

async def main():
    # Start the source connection in the background
    asyncio.create_task(connect_to_source())

    # Start the relay server, binding to all interfaces (0.0.0.0)
    async with websockets.serve(relay_server, "0.0.0.0", 4003):
        print("Relay server started on ws://0.0.0.0:4003 (all interfaces)")
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    asyncio.run(main())
