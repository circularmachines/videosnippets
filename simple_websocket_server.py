import asyncio
import websockets
import os

async def send_filenames(websocket, path):
    UPLOAD_FOLDER = './uploads'
    seen_files = set(os.listdir(UPLOAD_FOLDER))
    print(f"Initial files: {seen_files}")  # Debugging print

    try:
        while True:
            current_files = set(os.listdir(UPLOAD_FOLDER))
            new_files = current_files - seen_files
            if new_files:
                for filename in new_files:
                    print(f"File created: {filename}")  # Debugging print
                    await websocket.send(filename)
            seen_files = current_files
            await asyncio.sleep(1)
    except Exception as e:
        print(f"Error watching directory: {e}")  # Debugging print

async def main():
    async with websockets.serve(send_filenames, "localhost", 8765):
        print("WebSocket server started at ws://localhost:8765")
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    asyncio.run(main())