#import moviepy.editor as mp
import cv2
import base64

from audio_extract import extract_audio

from dotenv import load_dotenv  # Add this import

from openai import OpenAI
import os

from datetime import datetime
import time  # Add this import

# Load environment variables from .env file
load_dotenv()

# Initialize OpenAI client with the API key from environment variable
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

import imageio

def process_video(video_path):
    start_time = time.time()  # Start timing

    # Extract audio from video
    print(video_path)
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        print("Error: Could not open video.")
        return
    
    #frames = []
    #frame_count = 0
    ret, frame = cap.read()

    if ret:
        # Save the first frame as an image
        frame_path = f"./frames/frame_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.jpg"
        cv2.imwrite(frame_path, frame)
        print(f"Frame saved at {frame_path}")
        
        # Encode the image to base64
        with open(frame_path, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode('utf-8')
    else:
        print("Error: Could not read frame.")
        encoded_image = None
    
    cap.release()

    print(f"One frame extraction took {time.time() - start_time:.2f} seconds")

    """
    gif_start_time = time.time()  # Start timing for GIF creation
    
    while ret:
        if frame_count % 10 == 0:  # Read every tenth frame
            frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))  # Convert BGR to RGB
        frame_count += 1
        ret, frame = cap.read()
    
    cap.release()
    
    print(f"multiple Frame extraction took {time.time() - start_time:.2f} seconds")  # Log timing

    if frames:
        gif_start_time = time.time()  # Start timing for GIF creation
        # Create an animated GIF
        gif_path = f"./gifs/animation_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.gif"
        imageio.mimsave(gif_path, frames, format='GIF', duration=0.1)
        
        # Encode the GIF to base64
        with open(gif_path, "rb") as gif_file:
            encoded_gif = base64.b64encode(gif_file.read()).decode('utf-8')
        print(f"GIF creation and encoding took {time.time() - gif_start_time:.2f} seconds")  # Log timing
    else:
        print("Error: Could not read frames.")
        encoded_gif = None
    """

    audio_start_time = time.time()  # Start timing for audio extraction
    audio_path = f"./audio/temp_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.mp3"
    extract_audio(input_path=video_path, output_path=audio_path)
    print(f"Audio extraction took {time.time() - audio_start_time:.2f} seconds")  # Log timing
    
    transcription_start_time = time.time()  # Start timing for transcription
    # Transcribe audio using OpenAI Whisper
    with open(audio_path, "rb") as audio_file:
        response = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
        )
    print(f"Transcription took {time.time() - transcription_start_time:.2f} seconds")  # Log timing
    print(response)
    
    total_time = time.time() - start_time
    print(f"Total processing time: {total_time:.2f} seconds")  # Log total timing

    return response.text, encoded_image

# Example usage
if __name__ == "__main__":
    # Example usage
    video_path = "uploads/recording-2024-09-27T05-52-34-051Z.webm"
    transcription = process_video(video_path)
    print(transcription)



