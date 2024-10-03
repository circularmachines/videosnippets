import json
import os

# Define the path to incoming.json
INCOMING_FILE = 'incoming.json'
FOLDER='uploads'

entries=[]

for i,file in enumerate(os.listdir(FOLDER)):
    entries.append({'index':i,'video_path': "uploads\\"+file,'processed':False})

with open(INCOMING_FILE, 'w') as file:
    json.dump(entries, file, indent=2)


