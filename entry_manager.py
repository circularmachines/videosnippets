import json
import os
import time
import process_video
import base64

INCOMING_FILE = 'incoming.json'
OUTGOING_FILE = 'outgoing.json'
IMAGES_FOLDER = 'images'

def load_entries(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return json.load(f)
    return []

def save_entries(entries, file_path):
    with open(file_path, 'w') as f:
        json.dump(entries, f, indent=2)

def add_incoming_entry(video_path):
    entries = load_entries(INCOMING_FILE)
    entries.append({"video_path": video_path})
    save_entries(entries, INCOMING_FILE)

def update_incoming_entry(index, **kwargs):
    entries = load_entries(INCOMING_FILE)
    if 0 <= index < len(entries):
        entries[index].update(kwargs)
        save_entries(entries, INCOMING_FILE)

def add_outgoing_entry(entry):
    entries = load_entries(OUTGOING_FILE)
    entries.append(entry)
    save_entries(entries, OUTGOING_FILE)

def get_incoming_entries():
    return load_entries(INCOMING_FILE)

def get_outgoing_entries():
    entries = load_entries(OUTGOING_FILE)
    for entry in entries:
        if 'image_path' in entry and os.path.exists(entry['image_path']):
            with open(entry['image_path'], 'rb') as image_file:
                encoded_image = base64.b64encode(image_file.read()).decode('utf-8')
                entry['image'] = encoded_image
            del entry['image_path']
    return entries

def remove_incoming_entry(index):
    entries = load_entries(INCOMING_FILE)
    if 0 <= index < len(entries):
        del entries[index]
        save_entries(entries, INCOMING_FILE)

def process_videos():
    while True:
        incoming_entries = get_incoming_entries()
        for index, entry in enumerate(incoming_entries):
            video_path = entry['video_path']
            if 'transcription' not in entry:
                result = process_video.process_video(video_path)
                if result is not None:
                    transcription, image_path = result
                    
                    update_incoming_entry(index, 
                                          image_path=image_path, 
                                          transcription=transcription)
                    
                    if transcription:
                        add_outgoing_entry({
                            "transcription": transcription,
                            "image_path": image_path
                        })
                        remove_incoming_entry(index)
                    
                    print(f"Processing completed for {video_path}")
                else:
                    print(f"Processing failed for {video_path}")
                    remove_incoming_entry(index)
        
        time.sleep(1)  # Wait for 1 second before checking again

# Start the video processing thread
import threading
processing_thread = threading.Thread(target=process_videos, daemon=True)
processing_thread.start()