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

MESSAGES_FOLDER = 'messages'
IMAGES_FOLDER = 'messages/images'
AUDIO_FOLDER = 'audio'

os.makedirs(MESSAGES_FOLDER, exist_ok=True)
os.makedirs(IMAGES_FOLDER, exist_ok=True)
os.makedirs(AUDIO_FOLDER, exist_ok=True)

def process_video(video_path, last_transcription):
    start_time = time.time()  # Start timing
    print("NEW VIDEO")
    print(video_path)

    # Extract frames from video
    print(video_path)
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        print("Error: Could not open video.")
        return None, [], 1.0, 0.0  # Return empty list for frame_paths

    frame_paths = []
    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_count % 20 == 0:  # Save every 20th frame
            frame_path = os.path.join(IMAGES_FOLDER, f"frame_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_{frame_count}.jpg")
            cv2.imwrite(frame_path, frame)
            frame_paths.append(frame_path)
            print(f"Frame saved at {frame_path}")

        frame_count += 1

    cap.release()

    print(f"Frame extraction took {time.time() - start_time:.2f} seconds")
    print(f"Total frames processed: {frame_count}")
    print(f"Frames saved: {len(frame_paths)}")

    audio_start_time = time.time()  # Start timing for audio extraction
    audio_path = f"./audio/{os.path.basename(video_path)}.mp3"
    if os.path.exists(audio_path):
        print("Audio already exists, skipping extraction")
        return None, frame_paths, 1.0, 0.0
    extract_audio(input_path=video_path, output_path=audio_path)
    print(f"Audio extraction took {time.time() - audio_start_time:.2f} seconds")  # Log timing

    trim_start_time = time.time()

    # Load the extracted audio
    audio = AudioSegment.from_file(audio_path)

    # Detect non-silent chunks
    non_silent_chunks = silence.detect_nonsilent(audio, min_silence_len=100, silence_thresh=-40)
    new_audio_length = 0

    if non_silent_chunks:
        # Get the start and end of the first and last non-silent chunks
        start_trim = max(0, non_silent_chunks[0][0])
        end_trim = min(len(audio), non_silent_chunks[-1][1])

        original_audio_length = len(audio) / 1000
        new_audio_length = (end_trim - start_trim) / 1000
        print(f"trimmed audio from {original_audio_length} to {new_audio_length}")

        if new_audio_length < 0.2:
            print("Audio is too short, skipping")
            return "", frame_paths, 1.0, 0.0  # Return empty string for transcription and frame_paths and 1.0 for no_speech_prob and 0.0 for new_audio_length 
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
            language="sv",
            response_format="verbose_json"
        )
    print(f"Transcription took {time.time() - transcription_start_time:.2f} seconds")  # Log timing
    
    total_time = time.time() - start_time
    print(f"Total processing time: {total_time:.2f} seconds")  # Log total timing

    response_text = ""
    avg_no_speech_prob = 0
    segment_count = 0

    for s in response.segments:
        if s['no_speech_prob'] < 0.7:
            response_text += s['text']
        avg_no_speech_prob += s['no_speech_prob']
        segment_count += 1

    if segment_count > 0:
        avg_no_speech_prob /= segment_count
    else:
        avg_no_speech_prob = 1.0  # If no segments, assume it's all non-speech

    print("RESPONSE TEXT", response_text)
    print("Average no_speech_prob:", avg_no_speech_prob)

    return response_text, frame_paths, avg_no_speech_prob, new_audio_length

# Example usage
if __name__ == "__main__":
    # Example usage
    video_path = "uploads\\recording-2024-10-02T14-24-08-065Z.webm"
    transcription, frame_paths, no_speech_prob, audio_length = process_video(video_path, "")
    print("Transcription:", transcription)
    print("Frame paths:", frame_paths)
    print("No speech probability:", no_speech_prob)
    print("Audio length:", audio_length)



