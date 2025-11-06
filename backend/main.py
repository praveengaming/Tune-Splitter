import os
import shutil
import uuid
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware

from .processing_utils import extract_audio, separate_audio, cleanup_files

# === FastAPI initialization ===
app = FastAPI()

# === CORS setup ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Temporary storage folder ===
TEMP_DIR = Path("temp")
TEMP_DIR.mkdir(exist_ok=True)

# === Upload + Processing route ===
@app.post("/upload-media/")
async def upload_media(file: UploadFile = File(...)):
    session_id = str(uuid.uuid4())
    session_dir = TEMP_DIR / session_id
    session_dir.mkdir()

    video_path = session_dir / file.filename
    audio_path = session_dir / "extracted_audio.wav"
    demucs_output_dir = session_dir / "separated"

    try:
        # 1️⃣ Save uploaded file
        with open(video_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 2️⃣ Extract or transcode audio
        if not extract_audio(video_path, audio_path):
            raise HTTPException(status_code=500, detail="Audio extraction/transcoding failed.")

        # 3️⃣ Separate vocals and background
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

# === Root endpoint ===
@app.get("/")
def root():
    return {"message": "FastAPI media processing API is running!"}

# === Serve processed files ===
@app.get("/serve-file/{session_id}/{filename}")
async def serve_file(session_id: str, filename: str):
    session_dir = TEMP_DIR / session_id / "separated"
    candidates = list(session_dir.rglob(filename))
    if not candidates:
        raise HTTPException(status_code=404, detail="File not found.")
    return FileResponse(candidates[0])

# === Download processed files ===
@app.get("/download-file/{session_id}/{filename}")
async def download_file(session_id: str, filename: str):
    session_dir = TEMP_DIR / session_id / "separated"
    candidates = list(session_dir.rglob(filename))
    if not candidates:
        raise HTTPException(status_code=404, detail="File not found.")
    return FileResponse(candidates[0], media_type="audio/wav", filename=filename)

# === Clean session files ===
@app.get("/clean-session/{session_id}")
async def clean_session(session_id: str):
    session_dir = TEMP_DIR / session_id
    if session_dir.is_dir():
        cleanup_files([session_dir])
        return {"status": "success", "message": "Session files cleaned up."}
    return {"status": "not found", "message": "Session not found."}

# === Health check endpoint (for Render) ===
@app.get("/healthz")
def health_check():
    return {"status": "ok"}

# === Entry point ===
if __name__ == "__main__":
    import uvicorn
    # ⚠️ Must use port 10000 for Render
    uvicorn.run(app, host="0.0.0.0", port=10000)
