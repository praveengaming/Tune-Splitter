import os
import subprocess
import shutil
from pathlib import Path

# Utility Functions 

def ensure_dir(dir_path):
    Path(dir_path).mkdir(exist_ok=True, parents=True)

def cleanup_files(file_paths):
    """Removes a list of files and directories."""
    for path in file_paths:
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
        elif path.is_file():
            os.remove(path)

# Core Processing Functions 

def extract_audio(video_path, audio_path):
    """Extracts audio from a video file using ffmpeg."""
    try:
        subprocess.run(
            ['ffmpeg', '-i', str(video_path), '-vn', '-acodec', 'pcm_s16le', '-ar', '44100', '-ac', '2', str(audio_path)],
            check=True,
            capture_output=True,
            text=True
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error during audio extraction: {e.stderr}")
        return False

def separate_audio(audio_path, output_dir):
    """Separates audio into vocals and background music using Demucs."""
    try:
        demucs_command = ['demucs', '--two-stems', 'vocals', '-o', str(output_dir), str(audio_path)]
        subprocess.run(demucs_command, check=True, capture_output=True, text=True)
        
        vocal_file_list = list(Path(output_dir).rglob('vocals.wav'))
        background_file_list = list(Path(output_dir).rglob('no_vocals.wav'))

        if vocal_file_list and background_file_list:
            vocal_file = vocal_file_list[0]
            background_file = background_file_list[0]
            return vocal_file, background_file
        else:
            print("Separated audio files not found.")
            return None, None
        
    except subprocess.CalledProcessError as e:
        print(f"Error during audio separation: {e.stderr}")
        return None, None

############################################################
import os
import subprocess
import shutil
from pathlib import Path

# Utility Functions 

def ensure_dir(dir_path):
    Path(dir_path).mkdir(exist_ok=True, parents=True)

def cleanup_files(file_paths):
    """Removes a list of files and directories."""
    for path in file_paths:
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
        elif path.is_file():
            os.remove(path)

# Core Processing Functions 

def extract_audio(video_path, audio_path):
    """Extracts audio from a video file or transcodes an audio file (MP3) to WAV using ffmpeg."""
    try:
        subprocess.run(
            [
                'ffmpeg', 
                '-i', str(video_path), 
                '-vn', # Disables video
                '-acodec', 'pcm_s16le', # Forces uncompressed WAV codec
                '-ar', '44100', # Sample rate
                '-ac', '2', # Stereo channels
                str(audio_path)
            ],
            check=True,
            capture_output=True,
            text=True
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error during audio extraction/transcoding: {e.stderr}")
        return False

def separate_audio(audio_path, output_dir):
    """Separates audio into vocals and background music using Demucs."""
    try:
        demucs_command = ['demucs', '--two-stems', 'vocals', '-o', str(output_dir), str(audio_path)]
        subprocess.run(demucs_command, check=True, capture_output=True, text=True)
        
        # Demucs output paths
        vocal_file_list = list(Path(output_dir).rglob('vocals.wav'))
        background_file_list = list(Path(output_dir).rglob('no_vocals.wav'))

        if vocal_file_list and background_file_list:
            vocal_file = vocal_file_list[0]
            background_file = background_file_list[0]
            return vocal_file, background_file
        else:
            print("Separated audio files not found.")
            return None, None
        
    except subprocess.CalledProcessError as e:
        print(f"Error during audio separation: {e.stderr}")
        return None, None