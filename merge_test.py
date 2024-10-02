import os
import subprocess
from pathlib import Path
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def check_file(file_path):
    try:
        result = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', 
                                 '-count_packets', '-show_entries', 'stream=nb_read_packets', 
                                 '-of', 'csv=p=0', file_path], 
                                capture_output=True, text=True, check=True)
        return int(result.stdout.strip()) > 0
    except subprocess.CalledProcessError:
        return False

def merge_last_4_webm_videos():
    # Get the path to the uploads folder
    uploads_folder = Path("uploads")

    # Get all webm files in the uploads folder, sorted by modification time (newest first)
    video_files = sorted(uploads_folder.glob("*.webm"), key=os.path.getmtime, reverse=True)

    # Take the last 4 files (or all if there are fewer than 4)
    files_to_merge = video_files[:4]
    
    # Reverse the order so they're in chronological order (oldest first)
    files_to_merge = list(reversed(files_to_merge))
    
    logger.info(f"Files to merge (in chronological order): {files_to_merge}")

    if not files_to_merge:
        logger.warning("No webm files found in the uploads folder.")
        return

    # Output file name
    output_file = "merged_output.webm"

    # Prepare FFmpeg command
    ffmpeg_command = ['ffmpeg']
    
    # Add input files
    for file in files_to_merge:
        ffmpeg_command.extend(['-i', str(file)])
    
    # Add filter complex for concatenation
    filter_complex = f"concat=n={len(files_to_merge)}:v=1:a=1[outv][outa]"
    ffmpeg_command.extend(['-filter_complex', filter_complex])
    
    # Output options
    ffmpeg_command.extend([
        '-map', '[outv]',
        '-map', '[outa]',
        '-c:v', 'libvpx-vp9',  # Use VP9 codec for video
        '-crf', '30',
        '-b:v', '0',
        '-b:a', '128k',
        '-c:a', 'libopus',  # Use Opus codec for audio
        '-y',  # Overwrite output file if it exists
        output_file
    ])

    logger.debug(f"FFmpeg command: {' '.join(ffmpeg_command)}")

    try:
        # Execute the FFmpeg command
        result = subprocess.run(ffmpeg_command, check=True, capture_output=True, text=True)
        logger.info(f"Successfully merged videos into {output_file}")
        logger.debug(f"FFmpeg output: {result.stdout}")
    except subprocess.CalledProcessError as e:
        logger.error(f"An error occurred while merging videos: {e}")
        logger.error(f"FFmpeg error output: {e.stderr}")

if __name__ == "__main__":
    merge_last_4_webm_videos()

