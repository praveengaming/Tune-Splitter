import os
import shutil
import uuid
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Import utility functions from your local file
# Assuming processing_utils.py is in the same directory or correctly imported
from .processing_utils import extract_audio, separate_audio, cleanup_files 

# Initialize FastAPI app
app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set the path for temporary file storage
TEMP_DIR = Path("temp")
TEMP_DIR.mkdir(exist_ok=True)

# Set environment variable for the underlying libraries (like Spleeter/FFmpeg-Python)
# This is often done but doesn't fix a missing executable.
# It just ensures internal library calls use the correct pathing internally.
os.environ['TORCH_USE_FFMPEG'] = '1'

# ------------------------------------------------
# Scheduled Cleanup Function
# ------------------------------------------------
def automatic_cleanup(minutes_threshold=30):
    """Deletes all session folders in temp/ older than the specified time."""
    threshold_time = datetime.now() - timedelta(minutes=minutes_threshold)
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Running automatic cleanup (threshold: {minutes_threshold} min)...")
    
    deleted_count = 0
    
    for session_dir in TEMP_DIR.iterdir():
        if session_dir.is_dir():
            try:
                mod_time = datetime.fromtimestamp(session_dir.stat().st_mtime)
                
                if mod_time < threshold_time:
                    cleanup_files([session_dir])
                    deleted_count += 1
                    print(f"Deleted old session folder: {session_dir.name}")
            except Exception as e:
                print(f"Error during cleanup of {session_dir.name}: {e}")

    print(f"Automatic cleanup finished. Deleted {deleted_count} old sessions.")

# Initialize the scheduler
scheduler = AsyncIOScheduler()

# Event to start the scheduler
@app.on_event("startup")
async def start_scheduler():
    scheduler.add_job(automatic_cleanup, 'interval', minutes=30)
    scheduler.start()
    print("Background cleanup scheduler started.")
    automatic_cleanup(minutes_threshold=30) 

# Event to stop the scheduler
@app.on_event("shutdown")
async def stop_scheduler():
    scheduler.shutdown()
    print("Background cleanup scheduler shut down.")


# ------------------------------------------------
# FastAPI Routes
# ------------------------------------------------

@app.post("/upload-media/")
async def upload_media(file: UploadFile = File(...)):
    session_id = str(uuid.uuid4())
    session_dir = TEMP_DIR / session_id
    session_dir.mkdir()

    video_path = session_dir / file.filename 
    audio_path = session_dir / "extracted_audio.wav"
    
    # Rename for clarity: This output directory is for Spleeter's results
    spleeter_output_dir = session_dir / "separated" 

    try:
        # Save uploaded file
        with open(video_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 1. Extract Audio (uses ffmpeg system executable)
        if not extract_audio(video_path, audio_path):
            raise HTTPException(status_code=500, detail="Audio extraction/transcoding failed. Is FFmpeg installed?")

        # 2. Separate Audio (uses Spleeter/TensorFlow)
        # Note: If the demucs error persists, it's occurring inside separate_audio()
        vocal_file, background_file = separate_audio(audio_path, spleeter_output_dir)
        if not vocal_file or not background_file:
            # We catch the error in the utility function and re-raise a generic 500
            raise HTTPException(status_code=500, detail="Audio separation failed. Check Spleeter logs.")

        # 3. Success Response
        return JSONResponse({
            "status": "success",
            "vocals_url": f"/serve-file/{session_id}/{vocal_file.name}",
            "background_url": f"/serve-file/{session_id}/{background_file.name}",
            "vocals_download_url": f"/download-file/{session_id}/{vocal_file.name}",
            "background_download_url": f"/download-file/{session_id}/{background_file.name}",
            "session_id": session_id
        })
    except HTTPException:
        # Re-raise explicit HTTP exceptions (like the 500s above)
        raise
    except Exception as e:
        # Catch all other exceptions, log, and clean up the session
        cleanup_files([session_dir])
        # The log line that includes the demucs error
        print(f"Error during processing: {e}") 
        raise HTTPException(status_code=500, detail=f"Processing failed due to an internal error.") # Provide a safe message
        
@app.get("/")
# Add handling for HEAD requests to prevent 405 Method Not Allowed in logs
@app.head("/") 
def root():
    return {"message": "FastAPI media processing API is running!"}

@app.get("/serve-file/{session_id}/{filename}")
async def serve_file(session_id: str, filename: str):
    """Serves a processed file for playback."""
    # Note: Search must look in the directory *containing* the files, not the root of the session
    session_dir = TEMP_DIR / session_id / "separated"
    candidates = list(session_dir.rglob(filename))
    if not candidates:
        raise HTTPException(status_code=404, detail="File not found.")
    return FileResponse(candidates[0])

@app.get("/download-file/{session_id}/{filename}")
async def download_file(session_id: str, filename: str):
    """Provides a processed file for download."""
    session_dir = TEMP_DIR / session_id / "separated"
    candidates = list(session_dir.rglob(filename))
    if not candidates:
        raise HTTPException(status_code=404, detail="File not found.")
    return FileResponse(candidates[0], media_type="audio/wav", filename=filename)

@app.get("/clean-session/{session_id}")
async def clean_session(session_id: str):
    """Cleans up temporary files for a given session."""
    session_dir = TEMP_DIR / session_id
    if session_dir.is_dir():
        cleanup_files([session_dir])
        return {"status": "success", "message": "Session files cleaned up."}
    return {"status": "not found", "message": "Session not found."}