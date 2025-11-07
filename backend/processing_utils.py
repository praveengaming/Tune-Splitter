# -------------------------------
# ✅ Import Dependencies
# -------------------------------
import os
import sys
import shutil
import subprocess
from pathlib import Path
from demucs.separate import main as demucs_main  # ✅ Correct import for Demucs v4+

# -------------------------------
# ⚙️ Configuration
# -------------------------------
DEMUCS_MODEL = "mdx_extra"  # or "htdemucs" / "mdx_q"
DEMUCS_DEVICE = "cpu"       # Use "cuda" if GPU available

# -------------------------------
# 🧩 Utility Functions
# -------------------------------
def ensure_dir(path: Path):
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
    """Extracts or converts audio from video using FFmpeg."""
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
    """Separates audio into vocals and background using Demucs CLI API."""
    try:
        ensure_dir(output_dir)
        print(f"🎧 Running Demucs (Model: {DEMUCS_MODEL}, Device: {DEMUCS_DEVICE})")

        sys.argv = [
            "demucs",
            "-n", DEMUCS_MODEL,
            "--two-stems=vocals",
            "--device", DEMUCS_DEVICE,
            "-o", str(output_dir),
            str(audio_path)
        ]
        demucs_main()

        # Locate generated output
        input_stem = audio_path.stem
        final_output_path = output_dir / DEMUCS_MODEL / input_stem

        vocals = final_output_path / "vocals.wav"
        background = final_output_path / "no_vocals.wav"

        if vocals.exists() and background.exists():
            print("✅ Separation successful!")
            return vocals, background
        else:
            print(f"⚠️ Output not found at {final_output_path}. Searching recursively...")
            vocals_fallback = next(output_dir.rglob("vocals.wav"), None)
            background_fallback = next(output_dir.rglob("no_vocals.wav"), None)
            return vocals_fallback, background_fallback
    except Exception as e:
        print(f"❌ Error during Demucs separation: {e}")
        return None, None
