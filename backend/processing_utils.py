# -------------------------------
# ✅ Import Dependencies (Lightweight for Free Tier)
# -------------------------------
import os
import shutil
import subprocess
from pathlib import Path
from spleeter.separator import Separator

# -------------------------------
# ⚙️ Utility Functions
# -------------------------------
def ensure_dir(path: Path):
    """Ensure directory exists."""
    path.mkdir(parents=True, exist_ok=True)

def cleanup_files(file_paths):
    """Removes files or directories safely."""
    for path in file_paths:
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
        elif path.is_file():
            try:
                os.remove(path)
            except OSError:
                pass

# -------------------------------
# 🎧 Core Audio Functions (Spleeter-based)
# -------------------------------
def extract_audio(video_path: Path, audio_path: Path) -> bool:
    """Extracts audio from a video file using ffmpeg (keeps quality)."""
    try:
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i", str(video_path),
                "-vn",
                "-acodec", "pcm_s16le",
                "-ar", "44100",
                "-ac", "2",
                str(audio_path),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except Exception as e:
        print(f"❌ FFmpeg error: {e}")
        return False


def separate_audio(audio_path: Path, output_dir: Path):
    """Separates vocals and background using Spleeter (Render Free Compatible)."""
    try:
        ensure_dir(output_dir)
        print("🎵 Starting Spleeter separation (2 stems: vocals + accompaniment)...")

        # Initialize and run Spleeter
        separator = Separator('spleeter:2stems')
        separator.separate_to_file(str(audio_path), str(output_dir))

        song_name = Path(audio_path).stem
        vocals = Path(output_dir) / song_name / 'vocals.wav'
        background = Path(output_dir) / song_name / 'accompaniment.wav'

        if vocals.exists() and background.exists():
            print("✅ Separation successful!")
            return vocals, background
        else:
            print("⚠️ Could not find separated files.")
            return None, None
    except Exception as e:
        print(f"❌ Error during Spleeter separation: {e}")
        return None, None
