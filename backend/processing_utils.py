import os
import shutil
import subprocess
from pathlib import Path
# Note: Spleeter requires TensorFlow, which can be very slow on CPU/Render Free tier
from spleeter.separator import Separator

# --- Configuration ---
# Use 2 stems (vocals/accompaniment) as requested in your original code
SPLEETER_MODEL = "spleeter:2stems" 
# Output directory name for separation results
SEPARATION_OUTPUT_DIR = "separated_output"

# Utility functions
def ensure_dir(dir_path: Path):
    """Ensures a directory exists."""
    dir_path.mkdir(parents=True, exist_ok=True)

def cleanup_files(file_paths: list[Path]):
    """Deletes given files or directories safely."""
    for path in file_paths:
        if path.is_dir():
            # Use shutil.rmtree for directories
            shutil.rmtree(path, ignore_errors=True)
        elif path.is_file():
            # Use os.remove for files
            try:
                os.remove(path)
            except Exception as e:
                print(f"Error deleting {path}: {e}")

# --- Core Logic ---

def extract_audio(video_path: Path, audio_path: Path) -> bool:
    """Extracts audio from video or converts to WAV using ffmpeg."""
    print(f"🎬 Extracting/Converting audio from {video_path} to {audio_path}...")
    try:
        # NOTE: ffmpeg must be installed on the system (e.g., via apt-get install ffmpeg)
        subprocess.run([
            "ffmpeg",
            "-i", str(video_path),
            "-vn",                       # No video
            "-acodec", "pcm_s16le",      # PCM 16-bit little-endian WAV codec
            "-ar", "44100",              # Sample rate
            "-ac", "2",                  # Stereo audio
            str(audio_path)
        ], check=True, capture_output=True, text=True, timeout=60) # Added a 60-second timeout
        print("✅ FFmpeg extraction complete.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ FFmpeg error (return code {e.returncode}): {e.stderr}")
        return False
    except subprocess.TimeoutExpired:
        print("❌ FFmpeg operation timed out.")
        return False

def separate_audio(audio_path: Path, temp_dir: Path) -> tuple[Path | None, Path | None]:
    """Separates audio using Spleeter."""
    
    # 1. Setup paths
    output_dir = temp_dir / SEPARATION_OUTPUT_DIR
    ensure_dir(output_dir)

    print(f"🎧 Using Spleeter separation (Model: {SPLEETER_MODEL})...")
    
    try:
        # 2. Spleeter separation
        separator = Separator(SPLEETER_MODEL)

        # Spleeter expects the output_path to be a directory where it places an 
        # additional subdirectory named after the input file (without extension)
        separator.separate_to_file(str(audio_path), str(output_dir))

        # 3. Locate output files
        # Spleeter creates a folder inside output_dir based on the input filename
        input_filename_stem = audio_path.stem
        spleeter_result_path = output_dir / input_filename_stem

        vocal_file = spleeter_result_path / "vocals.wav"
        background_file = spleeter_result_path / "accompaniment.wav"

        if vocal_file.exists() and background_file.exists():
            print("✅ Audio successfully separated!")
            return vocal_file, background_file
        else:
            print("❌ Spleeter output files not found in expected location.")
            print(f"   Expected path: {spleeter_result_path}")
            return None, None

    except Exception as e:
        print(f"❌ Error during Spleeter separation: {e}")
        return None, None
    finally:
        # Clean up the intermediate directory created by Spleeter
        if 'spleeter_result_path' in locals() and spleeter_result_path.is_dir():
             shutil.rmtree(spleeter_result_path, ignore_errors=True)