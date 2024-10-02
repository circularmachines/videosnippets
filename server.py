from flask import Flask, request, send_from_directory, jsonify, Response
import os
import entry_manager
import logging
import json
import time
import asyncio
import threading

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
        return jsonify({'error': 'No video file'}), 400
    
    video = request.files['video']
    filename = video.filename

    if filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if video:
        video_path = os.path.join(UPLOAD_FOLDER, filename)
        video.save(video_path)
        
        # Add a new entry to incoming.json
        entry_manager.add_incoming_entry(video_path)
        
        return jsonify({
            'message': 'File uploaded successfully, processing will start soon',
            'filename': filename
        }), 202

@app.route('/stream')
def stream():
    def event_stream():
        last_entry_count = 0
        while True:
            entries = entry_manager.get_outgoing_entries()
            if len(entries) > last_entry_count:
                last_entry_count = len(entries)
                yield f"data: {json.dumps(entries)}\n\n"
            time.sleep(1)  # Check for new entries every second

    return Response(event_stream(), content_type='text/event-stream')

def run_async_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(entry_manager.main())

if __name__ == '__main__':
    # Start the entry_manager processes in a separate thread
    entry_manager_thread = threading.Thread(target=run_async_loop, daemon=True)
    entry_manager_thread.start()

    # Run the Flask app
    app.run(debug=True, threaded=True)
