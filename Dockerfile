# --------------------------------------------------------
# 1️⃣ Use a stable and minimal Python base image
# --------------------------------------------------------
FROM python:3.10-slim

# --------------------------------------------------------
# 2️⃣ Install required system dependencies
# --------------------------------------------------------
RUN apt-get update && \
    apt-get install -y ffmpeg git libsndfile1 && \
    rm -rf /var/lib/apt/lists/*

# --------------------------------------------------------
# 3️⃣ Set working directory
# --------------------------------------------------------
WORKDIR /app

# --------------------------------------------------------
# 4️⃣ Copy and install Python dependencies
# --------------------------------------------------------
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# --------------------------------------------------------
# 5️⃣ Pre-cache Demucs models to avoid runtime downloads
# --------------------------------------------------------
# Using “--list-models” triggers model verification and caching
RUN python3 -m demucs --list-models && \
    python3 -m demucs -n htdemucs --list-models && \
    python3 -m demucs -n mdx_extra --list-models

# --------------------------------------------------------
# 6️⃣ Copy the remaining application files
# --------------------------------------------------------
COPY . .

# --------------------------------------------------------
# 7️⃣ Expose the app port
# --------------------------------------------------------
EXPOSE 10000

# --------------------------------------------------------
# 8️⃣ Start the FastAPI app with Uvicorn (Render compatible)
# --------------------------------------------------------
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "10000"]
