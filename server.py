from flask import Flask, request, send_from_directory, jsonify, Response
import os
import entry_manager
import logging
import json
import time
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

@app.route('/upload-image', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return jsonify({'error': 'No image file'}), 400
    
    image = request.files['image']
    filename = image.filename

    if filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if image:
        # Generate a unique filename using a timestamp
        timestamp = int(time.time())
        file_extension = os.path.splitext(filename)[1]
        new_filename = f"{timestamp}{file_extension}"
        image_path = os.path.join(UPLOAD_FOLDER, new_filename)
        
        try:
            image.save(image_path)
            app.logger.info(f"Image saved successfully: {image_path}")
            
            # Add a new entry to incoming.json
            entry_manager.add_incoming_entry(image_path)
            entry_manager.update_outgoing_entries()
            
            return jsonify({
                'message': 'Image uploaded successfully',
                'filename': new_filename
            }), 202
        except Exception as e:
            app.logger.error(f"Error saving image: {str(e)}")
            return jsonify({'error': 'Failed to save image'}), 500
    
    return jsonify({'error': 'Invalid image'}), 400

@app.route('/stream')
def stream():
    def event_stream():
        last_entry_count = 0
        while True:
            entries = entry_manager.get_outgoing_entries()
            if len(entries) > 0:
                if len(str(entries)) != last_entry_count:
                    last_entry_count = len(str(entries))
                    yield f"data: {json.dumps(entries)}\n\n"
            time.sleep(0.7324)  # Check for new entries every second

    return Response(event_stream(), content_type='text/event-stream')

def run_llm_process():
    while True:
        entry_manager.process_LLM()
        time.sleep(0.5)  # Wait for 0.5 seconds before checking again

if __name__ == '__main__':
    # Start the entry_manager processes in a separate thread
    entry_manager_thread = threading.Thread(target=run_llm_process, daemon=True)
    entry_manager_thread.start()

    # Run the Flask app
    app.run(debug=True, threaded=True)
