import json
import os
import time
import process_video
import base64
import asyncio
import sys

import requests
from openai import OpenAI
from dotenv import load_dotenv

from datetime import datetime
os.makedirs("messages", exist_ok=True)
working_dir = os.getcwd()

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

INCOMING_FILE = 'incoming.json'
OUTGOING_FILE = 'outgoing.json'
IMAGES_FOLDER = 'images'

system_prompt = open("system_prompt.md", "r").read()

def load_entries(file_path):
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                if content.strip():  # Check if the file is not empty
                    return json.loads(content)
                else:
                    print(f"Warning: {file_path} is empty. Returning an empty list.")
                    return []
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON in {file_path}: {e}")
            print("Returning an empty list and backing up the corrupted file.")
            # Backup the corrupted file
            backup_path = f"{file_path}.bak"
            os.rename(file_path, backup_path)
            return []
    else:
        with open(file_path, 'w') as f:
            json.dump([], f, indent=2)
        return []

def save_entries(entries, file_path):
    with open(file_path, 'w') as f:
        json.dump(entries, f, indent=2)

def add_incoming_entry(video_path):
    entries = load_entries(INCOMING_FILE)
    new_index = max([entry.get('index', -1) for entry in entries], default=-1) + 1
    entries.append({
        "index": new_index,
        "video_path": video_path,
        "processed": False,
        "llm_processed": False
    })
    save_entries(entries, INCOMING_FILE)

def update_incoming_entry(index, **kwargs):
    entries = load_entries(INCOMING_FILE)
    for entry in entries:
        if entry['index'] == index:
            entry.update(kwargs)
            save_entries(entries, INCOMING_FILE)
            break

def remove_incoming_entry(index):
    entries = load_entries(INCOMING_FILE)
    entries = [entry for entry in entries if entry['index'] != index]
    save_entries(entries, INCOMING_FILE)

def get_incoming_entries():
    return load_entries(INCOMING_FILE)

# Function to encode the image
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def get_outgoing_entries():
    entries = load_entries(OUTGOING_FILE)
    for entry in entries:
    
        description = entry.get('description', 'N/A')
        comments = entry.get('comments', 'N/A')
        location = entry.get('location', 'N/A')
        if 'image_paths' in entry:  # Change 'image_path' to 'image_paths'
            
            entry['images'] = [encode_image(path) for path in entry['image_paths'] if os.path.exists(path)]
            del entry['image_paths']

            if entry['processed']:
                entry['transcription'] = f"<p><b>Description:</b> {description}<br><b>Comments:</b> {comments}<br><b>Location:</b> {location}</p>"
            else:
                entry['transcription'] = "<p><b>PROCESSING...</b></p>"

            
    return entries

def update_outgoing_entries():
    outgoing_entries = load_entries(OUTGOING_FILE)
    outgoing_entries = [e for e in outgoing_entries if e.get('processed',False)]
    indexes=[]
    for e in outgoing_entries:
            indexes.extend(e['indexes_in_merged_video'])
    
    incoming_entries = get_incoming_entries()
    processing_images = []
    for e in incoming_entries:
        if e['index'] not in indexes and e.get('image_path',False):
            processing_images.extend(e['image_path'])
    

    outgoing_entries.append({"image_paths": processing_images,
                            "processed": False})
    save_entries(outgoing_entries, OUTGOING_FILE)

def add_outgoing_entry(entry):
    entries = load_entries(OUTGOING_FILE)
    entries.append(entry)
    save_entries(entries, OUTGOING_FILE)
    update_outgoing_entries()

def get_image_path(index, incoming_entries):
    
    image_entry = next(entry for entry in incoming_entries if entry['index'] == index)
    return image_entry['image_path']

async def process_videos(debug=False):
    while True:
        incoming_entries = get_incoming_entries()
        last_transcription = ""
        for entry in incoming_entries:

            #if entry.get('transcription') is not None:
                
            #    last_transcription = entry['transcription']

            if not entry.get('processed', False):
                video_path = entry['video_path']
                result = process_video.process_video(video_path,last_transcription)
                print("result:", result)
                if result is not None:
                    transcription, image_path, no_speech_prob, new_audio_length = result

                    valid = no_speech_prob < 0.7 and new_audio_length > 0.5
                    
                    

                    update_incoming_entry(entry['index'], 
                                            image_path=image_path, 
                                            transcription=transcription,
                                            no_speech_prob=no_speech_prob,
                                            new_audio_length=new_audio_length,
                                            processed=True,
                                            valid=valid)
                                        
                
                        
                    update_outgoing_entries()
                    print(f"Processing completed for {video_path}")
                else:
                    print(f"Processing failed for {video_path}")
                    update_incoming_entry(entry['index'], processed=True)
        
        await asyncio.sleep(1)  # Wait for 1 second before checking again

async def process_LLM(debug=False):
    while True:
        llm_call = False
        #incoming_entries = [entry for entry in get_incoming_entries() if entry.get('valid',False)]
        incoming_entries = get_incoming_entries()
        new_entries = 0
        for entry in incoming_entries:
            if not entry.get('llm_processed', False) and entry.get('transcription'):
                llm_call = True
                
                


        if llm_call:
            # Prepare the payload for OpenAI API

            
            
            messages = [{"role": "system", "content": [{"type": "text", "text": system_prompt}]}]
            obsidian = f"## System\n{system_prompt}\n\n"
            #i=1
            for entry in incoming_entries:
                if not entry.get('locked_in',False) and entry.get('image_path',False) and new_entries < 2:
                    
                    if not entry.get('llm_processed',False):
                        new_entries += 1
                        update_incoming_entry(entry['index'], llm_processed=True)

                    #print(f"Transcription #{entry['index']}: {entry['transcription']}")
                    #i+=1
                    path_list = entry['image_path']
                    image_path = path_list[len(path_list)//2]
                    
                    base64_image = encode_image(image_path)
                   
                    messages.append({
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": f"Transcription #{entry['index']}: {entry['transcription']}"
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}",
                                    "detail": "low"
                                }
                            }
                        ]
                    })
                    image_path = image_path.replace('\\', '/').split("/",1)[-1]
                    obsidian+=f"## Transcription #{entry['index']}\n{entry['transcription']}\n\n![[{image_path}]]\n\n"

            
            #save messages along with images to a .md file for vizualising using obsidian
            with open(f"messages/messages_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.md", "w", encoding="utf-8") as f:
                f.write(obsidian)
            
            if debug:
                x=input("Press Enter to continue...")
            
            #send messages to openai and get response   
            try:
                response = requests.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}"
                    },
                    json={
                        "model": "gpt-4o-mini",
                        "messages": messages,
                        "max_tokens": 2000,
                        "response_format": { "type": "json_object" }
                    }
                )
                print("RESPONSE:")
                print(response.json()['choices'][0]['message']['content'])

                # Parse the JSON response
                response_data = json.loads(response.json()['choices'][0]['message']['content'])

                #new_data=[]

                for snippet in response_data['merged_video_snippets']:
                    #print("snippet:", snippet['video_snippet_id'])

                    
                   
                    #new_data.append({
                    if len(response_data['merged_video_snippets']) > 1:
                        if snippet['video_snippet_id'] == 1:
                            snippet['image_paths'] = []
                            for ix in snippet['indexes_in_merged_video']:
                                snippet['image_paths'].extend(get_image_path(ix, incoming_entries))
                            
                            snippet['processed'] = True
                            
                            add_outgoing_entry(snippet)
                            
                            for ix in snippet['indexes_in_merged_video']:
                                update_incoming_entry(ix, locked_in=True)
                        

                # Add the response to the outgoing entries
                #print("outgoing_data:")
                #print(outgoing_data)
               # save_entries(outgoing_data, OUTGOING_FILE)

            except Exception as e:
                print(f"Error in LLM processing: {str(e)}")
        if debug:
            x=input("Press Enter to continue...")
        else:
            await asyncio.sleep(1)  # Wait for 1 second before checking again




async def main(debug=False):
    await asyncio.gather(
        process_videos(debug),
        process_LLM(debug)
    )


if __name__ == "__main__":

    # get debug from args  
    # python entry_manager.py debug

    if len(sys.argv) > 1:   
        debug = sys.argv[1] == "debug"
    else:
        debug = False

    asyncio.run(main(debug))



