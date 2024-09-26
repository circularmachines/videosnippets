from flask import Flask, request, send_from_directory, jsonify
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time

app = Flask(__name__, static_folder='.')

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def alter_string(filename):
    return filename[::-1]  # Reverse the filename

class FileHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory:
            filename = os.path.basename(event.src_path)
            print(f"New file detected: {filename}")
            altered_filename = alter_string(filename)
            print(f"Altered filename: {altered_filename}")

file_handler = FileHandler()
observer = Observer()
observer.schedule(file_handler, path=UPLOAD_FOLDER, recursive=False)
observer.start()

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
        # Save the video with the provided filename
        video.save(os.path.join(UPLOAD_FOLDER, filename))
        
        # Process the filename
        altered_filename = alter_string(filename)
        
        return jsonify({
            'message': 'File uploaded successfully',
            'alteredFilename': altered_filename
        }), 200

if __name__ == '__main__':
    try:
        app.run(debug=True)
    finally:
        observer.stop()
        observer.join()