#import moviepy.editor as mp
import cv2
import base64

from audio_extract import extract_audio

from dotenv import load_dotenv  # Add this import

from openai import OpenAI
import os

from datetime import datetime
# Load environment variables from .env file
load_dotenv()

# Initialize OpenAI client with the API key from environment variable
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def process_video(video_path):
    # Extract audio from video
    print(video_path)
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        print("Error: Could not open video.")
        return
    
    # Read the first frame
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

    audio_path = f"./audio/temp_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.mp3"
    extract_audio(input_path=video_path, output_path=audio_path)
    
    # Transcribe audio using OpenAI Whisper
    with open(audio_path, "rb") as audio_file:
        response = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
        )
    print(response)
    return response.text, encoded_image

# Example usage
if __name__ == "__main__":
    # Example usage
    video_path = "uploads/recording-2024-09-27T05-52-34-051Z.webm"
    transcription = process_video(video_path)
    print(transcription)



