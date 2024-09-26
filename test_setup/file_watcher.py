import os
import time
import asyncio
import websockets
import threading

# Flag to indicate if the program should stop
stop_event = threading.Event()

async def send_filename(websocket, filename):
    print(f"Preparing to send filename: {filename}")  # Debugging print
    try:
        await websocket.send(filename)
        print(f"Successfully sent filename: {filename}")  # Debugging print
    except Exception as e:
        print(f"Error sending filename: {e}")  # Debugging print

async def watch_directory(path, websocket):
    print(f"Watching directory: {path}")  # Debugging print
    seen_files = set(os.listdir(path))
    print(f"Initial files: {seen_files}")  # Debugging print
    try:
        while not stop_event.is_set():
            current_files = set(os.listdir(path))
            new_files = current_files - seen_files
            deleted_files = seen_files - current_files
            if new_files:
                for filename in new_files:
                    print(f"File created: {filename}")  # Debugging print
                    await send_filename(websocket, filename)
            if deleted_files:
                for filename in deleted_files:
                    print(f"File deleted: {filename}")  # Debugging print
            seen_files = current_files
            await asyncio.sleep(1)
    except Exception as e:
        print(f"Error watching directory: {e}")  # Debugging print

async def main():
    uri = "ws://localhost:8765/ws"
    print(f"Connecting to WebSocket server at {uri}")  # Debugging print
    try:
        async with websockets.connect(uri) as websocket:
            print("WebSocket connection established")  # Debugging print
            await watch_directory("./uploads", websocket)
    except Exception as e:
        print(f"Error connecting to WebSocket server: {e}")  # Debugging print

def file_watcher():
    #print("Starting file watcher...")  # Debugging print
    asyncio.run(main())

def main():
    try:
        watch_thread = threading.Thread(target=file_watcher)
        watch_thread.start()
        while watch_thread.is_alive():
            watch_thread.join(timeout=1)
    except KeyboardInterrupt:
        print("KeyboardInterrupt caught, stopping thread...")
        stop_event.set()
        watch_thread.join()

if __name__ == "__main__":
    main()