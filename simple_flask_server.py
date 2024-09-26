import os
from flask import Flask, request, send_from_directory
from threading import Thread
import asyncio
from aiohttp import web
import websockets

# Flask app setup
flask_app = Flask(__name__, static_folder='.')

@flask_app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@flask_app.route('/<path:path>')
def serve_file(path):
    return send_from_directory('.', path)

def run_flask():
    print("Starting Flask server at http://127.0.0.1:5000")
    flask_app.run(debug=True, use_reloader=False)

# aiohttp WebSocket setup
async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    request.app['websockets'].add(ws)
    try:
        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                for client in request.app['websockets']:
                    await client.send_str(msg.data)
            elif msg.type == web.WSMsgType.ERROR:
                print('WebSocket connection closed with exception %s' % ws.exception())
    finally:
        request.app['websockets'].remove(ws)
    return ws

async def on_startup(app):
    app['websockets'] = set()

async def run_aiohttp():
    aio_app = web.Application()
    aio_app.on_startup.append(on_startup)
    aio_app.router.add_get('/ws', websocket_handler)
    runner = web.AppRunner(aio_app)
    await runner.setup()
    site = web.TCPSite(runner, 'localhost', 8765)
    await site.start()
    print("Starting aiohttp WebSocket server at ws://localhost:8765/ws")
    try:
        while True:
            await asyncio.sleep(3600)
    except asyncio.CancelledError:
        pass

def main():
    flask_thread = Thread(target=run_flask)
    flask_thread.start()

    loop = asyncio.get_event_loop()
    aiohttp_thread = Thread(target=loop.run_until_complete, args=(run_aiohttp(),))
    aiohttp_thread.start()

    flask_thread.join()
    aiohttp_thread.join()

if __name__ == "__main__":
    main()