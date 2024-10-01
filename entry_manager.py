import json
import os

RESULTS_FILE = 'results.json'

def load_entries():
    if os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE, 'r') as f:
            return json.load(f)
    return []

def save_entries(entries):
    with open(RESULTS_FILE, 'w') as f:
        json.dump(entries, f, indent=2)

def add_entry(transcription, image):
    entries = load_entries()
    if transcription != "":
        print("ADDING ENTRY", transcription)
        entries.append({
            "transcription": transcription,
            "image": image
        })
        save_entries(entries)

def get_all_entries():
    return load_entries()

def print_entries_without_images():
    entries = load_entries()
    for entry in entries:
        has_image = 'image' in entry
        entry_without_image = {key: value for key, value in entry.items() if key != 'image'}
        print(entry_without_image, has_image)

if __name__ == "__main__":
    print_entries_without_images()