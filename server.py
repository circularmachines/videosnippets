from flask import Flask, request, send_from_directory, jsonify
import os
import threading
import process_video
import entry_manager
import logging

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
        
        # Add a new entry without status
        entry_manager.add_entry('', '')
        
        # Start processing the video in a separate thread
        thread = threading.Thread(target=process_video_async, args=(video_path,))
        thread.start()
        
        return jsonify({
            'message': 'File uploaded successfully, processing started',
            'filename': filename
        }), 202

def process_video_async(video_path):
    transcription, encoded_image = process_video.process_video(video_path)
    
    # Update the last entry with the results
    entries = entry_manager.get_all_entries()
    entries[-1]['transcription'] = transcription
    entries[-1]['image'] = encoded_image
    entry_manager.save_entries(entries)
    
    print(f"Processing completed for {video_path}")

@app.route('/get_entries', methods=['GET'])
def get_entries():
    entries = entry_manager.get_all_entries()
    logging.debug(f"Sending entries: {entries}")
    return jsonify(entries)

if __name__ == '__main__':
    app.run(debug=True)