# -------------------------------
# ✅ Import Dependencies
# -------------------------------
import os
import shutil
import subprocess
from pathlib import Path
from spleeter.separator import Separator  # ✅ Lightweight Spleeter import

# -------------------------------
# ⚙️ Configuration
# -------------------------------
SPLEETER_MODEL = "spleeter:2stems"  # 2 stems = vocals + accompaniment

# -------------------------------
# 🧩 Utility Functions
# -------------------------------
def ensure_dir(path: Path):
    """Ensure a directory exists."""
    path.mkdir(parents=True, exist_ok=True)

def cleanup_files(file_paths):
    """Removes files and directories safely."""
    for path in file_paths:
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
        elif path.is_file():
            try:
                os.remove(path)
            except OSError:
                pass

# -------------------------------
# 🎧 Core Audio Processing
# -------------------------------
def extract_audio(video_path: Path, audio_path: Path) -> bool:
    """
    Extracts or converts audio from video using FFmpeg.
    """
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
                str(audio_path)
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ FFmpeg error: {e}")
        return False
    except FileNotFoundError:
        print("❌ FFmpeg not found. Ensure it's installed in Docker.")
        return False


def separate_audio(audio_path: Path, output_dir: Path):
    """
    Separates audio into vocals and background using Spleeter (Free Plan Safe).
    """
    try:
        ensure_dir(output_dir)
        print(f"🎵 Running Spleeter separation (Model: {SPLEETER_MODEL})...")

        # Initialize Spleeter separator
        separator = Separator(SPLEETER_MODEL)

        # Perform separation and save output files
        separator.separate_to_file(str(audio_path), str(output_dir))

        # Locate generated output files
        song_name = Path(audio_path).stem
        vocals = Path(output_dir) / song_name / "vocals.wav"
        background = Path(output_dir) / song_name / "accompaniment.wav"

        if vocals.exists() and background.exists():
            print("✅ Separation successful!")
            return vocals, background
        else:
            print(f"⚠️ Output files not found at expected path: {output_dir}")
            # fallback search
            vocals_r = next(output_dir.rglob("vocals.wav"), None)
            background_r = next(output_dir.rglob("accompaniment.wav"), None)
            return vocals_r, background_r

    except Exception as e:
        print(f"❌ Error during Spleeter separation: {e}")
        return None, None
