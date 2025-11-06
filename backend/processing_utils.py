import os
import shutil
import subprocess
from pathlib import Path
from spleeter.separator import Separator

# Utility functions
def ensure_dir(dir_path):
    Path(dir_path).mkdir(parents=True, exist_ok=True)

def cleanup_files(file_paths):
    """Deletes given files or directories safely."""
    for path in file_paths:
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
        elif path.is_file():
            try:
                os.remove(path)
            except Exception as e:
                print(f"Error deleting {path}: {e}")

# Extract audio from video or convert to WAV
def extract_audio(video_path, audio_path):
    """Extracts audio from video or converts to WAV using ffmpeg."""
    try:
        subprocess.run([
            "ffmpeg",
            "-i", str(video_path),
            "-vn",
            "-acodec", "pcm_s16le",
            "-ar", "44100",
            "-ac", "2",
            str(audio_path)
        ], check=True, capture_output=True, text=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"FFmpeg error: {e.stderr}")
        return False

# Separate vocals and background using Spleeter
def separate_audio(audio_path, output_dir):
    """Separates audio into vocals and accompaniment using Spleeter."""
    try:
        ensure_dir(output_dir)

        print("🎧 Using Spleeter separation...")

        # Load the 2-stem model (vocals + accompaniment)
        separator = Separator("spleeter:2stems")

        # Separate the audio
        separator.separate_to_file(str(audio_path), str(output_dir))

        # Find output files
        vocal_file = next(Path(output_dir).rglob("vocals.wav"), None)
        background_file = next(Path(output_dir).rglob("accompaniment.wav"), None)

        if vocal_file and background_file:
            print("✅ Audio successfully separated!")
            return vocal_file, background_file
        else:
            print("❌ Spleeter output files not found.")
            return None, None

    except Exception as e:
        print(f"Error during Spleeter separation: {e}")
        return None, None
