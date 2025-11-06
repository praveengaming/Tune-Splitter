# Use a highly stable Python 3.10 base image
FROM python:3.10-slim

# 1. Install System Dependencies (FFmpeg and libsndfile1 for audio)
RUN apt-get update && \
    apt-get install -y ffmpeg git libsndfile1 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .

# 2. Install Dependencies (Stabilizing pip install)
# Combining and simplifying the installation step for robustness
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# 3. Cache Demucs Models (CRITICAL: Prevents runtime timeout/crash)
# This downloads the models once during the build, using the model names
# that demucs saves locally.
RUN python3 -m demucs.separate -n htdemucs --url "" && \
    python3 -m demucs.separate -n mdx_extra --url ""

COPY . .

# 4. Set Command (Ensures the path matches your project structure)
# Your traceback indicates the main file is inside a 'backend' folder.
EXPOSE 10000
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "10000"]