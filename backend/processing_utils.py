import os
import shutil
import subprocess
from pathlib import Path
from demucs.api import Separator # 🛠️ CORRECT IMPORT for Python API

# === Configuration ===
# Use the best model you've pre-cached in your Dockerfile (mdx_extra is recommended)
DEMUCS_MODEL = "mdx_extra" 
# Use 'cpu' as you are on the Render Free/Standard tier without a GPU
DEMUCS_DEVICE = "cpu"

# === Utility Functions ===

def ensure_dir(dir_path):
    Path(dir_path).mkdir(exist_ok=True, parents=True)


def cleanup_files(file_paths):
    """Removes a list of files and directories."""
    for path in file_paths:
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
        elif path.is_file():
            try:
                os.remove(path)
            except OSError:
                # Handle potential permission errors if files are still in use
                pass


# === Core Audio Functions ===

def extract_audio(video_path, audio_path):
    """
    Extracts audio from a video file or transcodes an MP3 file to WAV using ffmpeg.
    """
    try:
        # 💡 NOTE: This relies on the FFmpeg executable being installed via the Dockerfile
        subprocess.run(
            [
                "ffmpeg",
                "-i", str(video_path),
                "-vn",             # Disable video
                "-acodec", "pcm_s16le", # WAV format
                "-ar", "44100",    # Sample rate
                "-ac", "2",        # Stereo
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
    except FileNotFoundError:
        print("❌ FFmpeg executable not found. Ensure it's installed on the system PATH.")
        return False


def separate_audio(audio_path: Path, output_dir: Path):
    """
    Separates audio into vocals and background music using the Demucs Python API.
    """
    try:
        ensure_dir(output_dir)

        print(f"🎧 Starting Demucs separation (Model: {DEMUCS_MODEL}, Device: {DEMUCS_DEVICE})...")
        
        # 1. Initialize the Separator
        # The 'stems=2' setting ensures it separates into vocals and 'no_vocals'
        separator = Separator(model=DEMUCS_MODEL, device=DEMUCS_DEVICE, stems=2)
        
        # 2. Run the separation
        # Demucs will save files inside output_dir/model_name/track_name/...
        # The save_path argument saves the results directly to disk.
        separator.separate_files([audio_path], save_path=str(output_dir))

        # 3. Determine the final output directory path created by Demucs
        # Example output structure: output_dir/mdx_extra/extracted_audio/
        input_stem = audio_path.stem
        final_output_path = output_dir / DEMUCS_MODEL / input_stem 

        # 4. Find resulting files
        vocal_file = final_output_path / "vocals.wav"
        background_file = final_output_path / "no_vocals.wav"

        if vocal_file.exists() and background_file.exists():
            print("✅ Separation successful!")
            return vocal_file, background_file
        else:
            print(f"❌ Could not find separated files in expected location: {final_output_path}")
            # Recursively search the output_dir just in case Demucs changed the naming slightly
            vocal_file_r = next(Path(output_dir).rglob("vocals.wav"), None)
            background_file_r = next(Path(output_dir).rglob("no_vocals.wav"), None)
            return vocal_file_r, background_file_r

    except Exception as e:
        print(f"Error during Demucs separation: {e}")
        return None, None