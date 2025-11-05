import os
import shutil
import uuid
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from datetime import datetime, timedelta

# ➡️ NEW IMPORT for scheduling background tasks
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Ensure ffmpeg is on PATH... (existing code)
os.environ['TORCH_USE_FFMPEG'] = '1'



from .processing_utils import extract_audio, separate_audio, cleanup_files

# Initialize FastAPI app
app = FastAPI()

# Configure CORS (existing code)
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

# ------------------------------------------------
# ➡️ NEW: Scheduled Cleanup Function
# ------------------------------------------------
def automatic_cleanup(minutes_threshold=30):
    """Deletes all session folders in temp/ older than the specified time."""
    threshold_time = datetime.now() - timedelta(minutes=minutes_threshold)
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Running automatic cleanup (threshold: {minutes_threshold} min)...")
    
    deleted_count = 0
    
    # Iterate over all session directories inside temp/
    for session_dir in TEMP_DIR.iterdir():
        if session_dir.is_dir():
            try:
                # Use the directory's last modification time (st_mtime)
                mod_time = datetime.fromtimestamp(session_dir.stat().st_mtime)
                
                if mod_time < threshold_time:
                    cleanup_files([session_dir])
                    deleted_count += 1
                    print(f"Deleted old session folder: {session_dir.name}")
            except Exception as e:
                print(f"Error during cleanup of {session_dir.name}: {e}")

    print(f"Automatic cleanup finished. Deleted {deleted_count} old sessions.")
# ------------------------------------------------


# Initialize the scheduler
scheduler = AsyncIOScheduler()

# ➡️ NEW: Event to start the scheduler when the FastAPI app starts up
@app.on_event("startup")
async def start_scheduler():
    # Schedule the cleanup function to run every 30 minutes
    scheduler.add_job(automatic_cleanup, 'interval', minutes=30)
    scheduler.start()
    print("Background cleanup scheduler started.")
    # Run cleanup once on startup to clear any leftover files from a previous run/crash
    automatic_cleanup(minutes_threshold=30) 

# ➡️ NEW: Event to stop the scheduler when the FastAPI app shuts down
@app.on_event("shutdown")
async def stop_scheduler():
    scheduler.shutdown()
    print("Background cleanup scheduler shut down.")


# ------------------------------------------------
# Existing FastAPI Routes (upload_media, serve-file, etc.)
# ------------------------------------------------

@app.post("/upload-media/")
async def upload_media(file: UploadFile = File(...)):
    session_id = str(uuid.uuid4())
    session_dir = TEMP_DIR / session_id
    session_dir.mkdir()

    video_path = session_dir / file.filename 
    audio_path = session_dir / "extracted_audio.wav"
    demucs_output_dir = session_dir / "separated"

    try:
        with open(video_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        if not extract_audio(video_path, audio_path):
            raise HTTPException(status_code=500, detail="Audio extraction/transcoding failed.")

        vocal_file, background_file = separate_audio(audio_path, demucs_output_dir)
        if not vocal_file or not background_file:
            raise HTTPException(status_code=500, detail="Audio separation failed.")

        return JSONResponse({
            "status": "success",
            "vocals_url": f"/serve-file/{session_id}/{vocal_file.name}",
            "background_url": f"/serve-file/{session_id}/{background_file.name}",
            "vocals_download_url": f"/download-file/{session_id}/{vocal_file.name}",
            "background_download_url": f"/download-file/{session_id}/{background_file.name}",
            "session_id": session_id
        })
    except Exception as e:
        cleanup_files([session_dir])
        print(f"Error during processing: {e}") 
        raise HTTPException(status_code=500, detail=f"Processing failed: {e}")
        
@app.get("/")
def root():
    return {"message": "FastAPI media processing API is running!"}

@app.get("/serve-file/{session_id}/{filename}")
async def serve_file(session_id: str, filename: str):
    """Serves a processed file for playback."""
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10000)
