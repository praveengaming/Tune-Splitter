import os
import shutil
from pathlib import Path
from spleeter.separator import Separator
import subprocess

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
    """
    Extracts audio from a video file or converts MP3 to WAV using ffmpeg.
    """
    try:
        subprocess.run(
            [
                "ffmpeg",
                "-i", str(video_path),
                "-vn",  # Disable video
                "-acodec", "pcm_s16le",  # WAV codec
                "-ar", "44100",  # Sample rate
                "-ac", "2",  # Stereo
                str(audio_path),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error during audio extraction/transcoding: {e.stderr}")
        return False


def separate_audio(audio_path, output_dir):
    """
    Separates audio into vocals and background using Spleeter.
    This version runs entirely in Python — no external CLI.
    """
    try:
        ensure_dir(output_dir)

        # Use Spleeter's 2-stem model (vocals + accompaniment)
        separator = Separator("spleeter:2stems")

        # Perform separation
        separator.separate_to_file(str(audio_path), str(output_dir))

        # Find generated files
        vocal_file = next(Path(output_dir).rglob("vocals.wav"), None)
        background_file = next(Path(output_dir).rglob("accompaniment.wav"), None)

        if vocal_file and background_file:
            print("Separation successful.")
            return vocal_file, background_file
        else:
            print("Spleeter output files not found.")
            return None, None

    except Exception as e:
        print(f"Error during Spleeter separation: {e}")
        return None, None
