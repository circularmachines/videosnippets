#import moviepy.editor as mp
import cv2
import base64
from pydub import AudioSegment, silence  # Add these imports

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
import ffmpeg  # Add this import

IMAGES_FOLDER = 'images'

def process_video(video_path):
    start_time = time.time()  # Start timing

    # Extract audio from video
    print(video_path)
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        print("Error: Could not open video.")
        return None, None  # Return None for both transcription and frame_path

    ret, frame = cap.read()

    if ret:
        # Save the first frame as an image
        os.makedirs(IMAGES_FOLDER, exist_ok=True)
        frame_path = os.path.join(IMAGES_FOLDER, f"frame_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.jpg")
        cv2.imwrite(frame_path, frame)
        print(f"Frame saved at {frame_path}")
    else:
        print("Error: Could not read frame.")
        frame_path = None
    
    cap.release()

    print(f"One frame extraction took {time.time() - start_time:.2f} seconds")

    audio_start_time = time.time()  # Start timing for audio extraction
    audio_path = f"./audio/temp_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.mp3"
    extract_audio(input_path=video_path, output_path=audio_path)
    print(f"Audio extraction took {time.time() - audio_start_time:.2f} seconds")  # Log timing

    trim_start_time = time.time()

    # Load the extracted audio
    audio = AudioSegment.from_file(audio_path)

    # Detect non-silent chunks
    non_silent_chunks = silence.detect_nonsilent(audio, min_silence_len=100, silence_thresh=-40)

    if non_silent_chunks:
        # Get the start and end of the first and last non-silent chunks
        start_trim = max(0, non_silent_chunks[0][0])
        end_trim = min(len(audio), non_silent_chunks[-1][1])

        original_audio_length = len(audio) / 1000
        new_audio_length = (end_trim - start_trim) / 1000
        print(f"trimmed audio from {original_audio_length} to {new_audio_length}")

        if new_audio_length < 0.2:
            print("Audio is too short, skipping")
            return "", frame_path  # Return empty string for transcription and frame_path
        # Trim the audio
        trimmed_audio = audio[start_trim:end_trim]

        # Save the trimmed audio
        trimmed_audio_path = f"./audio/trimmed_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.mp3"
        trimmed_audio.export(trimmed_audio_path, format="mp3")
        audio_path = trimmed_audio_path  # Update the audio path to the trimmed audio

        """# Trim the video using ffmpeg
        video_trim_start_time = time.time()  # Start timing for video trimming
        trimmed_video_path = f"./videos/trimmed_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.webm"
        (
            ffmpeg
            .input(video_path, ss=start_trim / 1000, to=end_trim / 1000)
            .output(trimmed_video_path)
            .run()
        )
        print(f"Video trimming took {time.time() - video_trim_start_time:.2f} seconds")  # Log timing
        video_path = trimmed_video_path  # Update the video path to the trimmed video"""

    else:
        print("Error: No non-silent chunks found in the audio.")

    print(f"Audio trimming took {time.time() - trim_start_time:.2f} seconds")  # Log timing

    

    # Transcribe audio using OpenAI Whisper
    transcription_start_time = time.time()  # Start timing for transcription
    with open(audio_path, "rb") as audio_file:
        response = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="verbose_json"
        )
    print(f"Transcription took {time.time() - transcription_start_time:.2f} seconds")  # Log timing
    #print("RESPONSE!", response)
    
    total_time = time.time() - start_time
    print(f"Total processing time: {total_time:.2f} seconds")  # Log total timing

    response_text = ""

    for s in response.segments:
        if s['no_speech_prob'] < 0.7:
            response_text += s['text']

    print("RESPONSE TEXT", response_text)

    return response_text, frame_path

# Example usage
if __name__ == "__main__":
    # Example usage
    video_path = "uploads/recording-2024-09-27T05-52-34-051Z.webm"
    transcription = process_video(video_path)
    print(transcription)



