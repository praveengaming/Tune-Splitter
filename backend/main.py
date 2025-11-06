import os
import shutil
import uuid
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

#  Ensure ffmpeg is on PATH for the running process
os.environ['TORCH_USE_FFMPEG'] = '1'
#  DOUBLE-CHECK THIS PATH
os.environ['PATH'] += os.pathsep + r"C:\ffmpeg\ffmpeg-6.0-essentials_build\bin"

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

@app.post("/upload-video/")
async def upload_video(file: UploadFile = File(...)):
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
            raise HTTPException(status_code=500, detail="Audio extraction failed.")

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
        raise HTTPException(status_code=500, detail=f"Processing failed: {e}")
        
@app.get("/")
def root():
    return {"message": "FastAPI video processing API is running!"}

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

if __name__ == "main":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

################################################
import os
import shutil
import uuid
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

# Ensure ffmpeg is on PATH for the running process
os.environ['TORCH_USE_FFMPEG'] = '1'


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

# 🔑 CHANGE 3: Changed endpoint and function name to handle generic media
@app.post("/upload-media/")
async def upload_media(file: UploadFile = File(...)):
    session_id = str(uuid.uuid4())
    session_dir = TEMP_DIR / session_id
    session_dir.mkdir()

    # Note: video_path holds either the video or the MP3 file
    video_path = session_dir / file.filename 
    audio_path = session_dir / "extracted_audio.wav"
    demucs_output_dir = session_dir / "separated"

    try:
        # 1. Save the uploaded file (MP4 or MP3)
        with open(video_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 2. Extract/Transcode to WAV. This works for both MP4 (extracts) and MP3 (transcodes).
        if not extract_audio(video_path, audio_path):
            raise HTTPException(status_code=500, detail="Audio extraction/transcoding failed.")

        # 3. Separate audio
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
        # Log the exception for debugging
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
    uvicorn.run(app, host="0.0.0.0", port=8000)