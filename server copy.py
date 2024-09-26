import asyncio
import websockets
from aiohttp import web
import os
from flask import Flask, request, send_from_directory


app = Flask(__name__, static_folder='.')

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_file(path):
    return send_from_directory('.', path)

@app.route('/upload', methods=['POST'])
def upload_video():
    if 'video' not in request.files:
        return 'No video file', 400
    
    video = request.files['video']
    filename = video.filename  # Get the filename from the request

    if filename == '':
        return 'No selected file', 400
    
    if video:
        # Save the video with the provided filename
        video.save(os.path.join(UPLOAD_FOLDER, filename))
        return 'File uploaded successfully', 200

async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    async for msg in ws:
        if msg.type == web.WSMsgType.TEXT:
            # Broadcast the new filename to all connected clients
            for client in request.app['websockets']:
                await client.send_str(msg.data)
        elif msg.type == web.WSMsgType.ERROR:
            print('WebSocket connection closed with exception %s' % ws.exception())

    request.app['websockets'].remove(ws)
    return ws

async def on_startup(app):
    app['websockets'] = set()

if __name__ == '__main__':
    app = web.Application()
    app.on_startup.append(on_startup)
    app.router.add_get('/ws', websocket_handler)
    # ... existing routes ...

    web.run_app(app, host='localhost', port=8765)