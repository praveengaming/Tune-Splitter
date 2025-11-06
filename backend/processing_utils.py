import os
import shutil
import subprocess
from pathlib import Path
from demucs.separate import main as demucs_main  # ✅ Use Demucs Python API

# === Utility Functions ===

def ensure_dir(dir_path):
    Path(dir_path).mkdir(exist_ok=True, parents=True)


def cleanup_files(file_paths):
    """Removes a list of files and directories."""
    for path in file_paths:
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
        elif path.is_file():
            os.remove(path)


# === Core Audio Functions ===

def extract_audio(video_path, audio_path):
    """
    Extracts audio from a video file or transcodes an MP3 file to WAV using ffmpeg.
    """
    try:
        subprocess.run(
            [
                "ffmpeg",
                "-i", str(video_path),
                "-vn",  # Disable video
                "-acodec", "pcm_s16le",  # WAV format
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
        print(f"❌ FFmpeg error: {e.stderr}")
        return False


def separate_audio(audio_path, output_dir):
    """
    Separates audio into vocals and background music using Demucs (Python API).
    """
    try:
        ensure_dir(output_dir)

        print("🎧 Starting Demucs audio separation...")
        # Run Demucs as if from command line, but within Python
        demucs_main([
            "--two-stems", "vocals",
            "-o", str(output_dir),
            str(audio_path),
        ])

        # Find resulting files
        vocal_file = next(Path(output_dir).rglob("vocals.wav"), None)
        background_file = next(Path(output_dir).rglob("no_vocals.wav"), None)

        if vocal_file and background_file:
            print("✅ Separation successful!")
            return vocal_file, background_file
        else:
            print("❌ Could not find separated files.")
            return None, None

    except Exception as e:
        print(f"Error during Demucs separation: {e}")
        return None, None
