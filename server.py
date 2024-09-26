from flask import Flask, request, send_from_directory
import os

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

if __name__ == '__main__':
    app.run(debug=True)