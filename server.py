from flask import Flask, request, send_from_directory, jsonify
import os
import threading
import process_video
import json

app = Flask(__name__, static_folder='.')

UPLOAD_FOLDER = 'uploads'
RESULTS_FOLDER = 'results'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
if not os.path.exists(RESULTS_FOLDER):
    os.makedirs(RESULTS_FOLDER)

"""def alter_string(filename):
    return filename[::-1]  # Reverse the filename

class FileHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory:
            filename = os.path.basename(event.src_path)
            print(f"New file detected: {filename}")
            #altered_filename = alter_string(filename)
            #print(f"Altered filename: {altered_filename}")

file_handler = FileHandler()
observer = Observer()
observer.schedule(file_handler, path=UPLOAD_FOLDER, recursive=False)
observer.start()
"""
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
        # Save the video with the provided filename
        video.save(video_path)
        
        # Start processing the video in a separate thread
        thread = threading.Thread(target=process_video_async, args=(video_path,))
        thread.start()
        
        return jsonify({
            'message': 'File uploaded successfully, processing started',
            'filename': filename
        }), 202  # 202 Accepted status code

def process_video_async(video_path):
    filename = os.path.basename(video_path)
    result_path = os.path.join(RESULTS_FOLDER, f"{filename}.json")
    
    # Save initial status
    with open(result_path, 'w') as f:
        json.dump({'status': 'processing'}, f)
    
    transcription, encoded_image = process_video.process_video(video_path)
    
    # Save results
    with open(result_path, 'w') as f:
        json.dump({
            'status': 'completed',
            'transcription': transcription,
            'image': encoded_image
        }, f)
    
    print(f"Processing completed for {video_path}")

@app.route('/check_status/<filename>', methods=['GET'])
def check_status(filename):
    result_path = os.path.join(RESULTS_FOLDER, f"{filename}.json")
    if os.path.exists(result_path):
        with open(result_path, 'r') as f:
            return jsonify(json.load(f))
    else:
        return jsonify({'status': 'not_found'}), 404

if __name__ == '__main__':
    try:
        app.run(debug=True)
    finally:
        None
        #  observer.stop()
        #  observer.join()