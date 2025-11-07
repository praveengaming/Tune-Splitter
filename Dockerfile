# --------------------------------------------------------
# ✅ Lightweight base image
# --------------------------------------------------------
FROM python:3.10-slim

# --------------------------------------------------------
# ✅ Install only essential system dependencies
# --------------------------------------------------------
RUN apt-get update && \
    apt-get install -y ffmpeg libsndfile1 && \
    rm -rf /var/lib/apt/lists/*

# --------------------------------------------------------
# ✅ Set working directory
# --------------------------------------------------------
WORKDIR /app

# --------------------------------------------------------
# ✅ Copy and install Python dependencies
# --------------------------------------------------------
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# --------------------------------------------------------
# ✅ Copy the rest of your app
# --------------------------------------------------------
COPY . .

# --------------------------------------------------------
# ✅ Expose port (Render expects dynamic port 10000)
# --------------------------------------------------------
EXPOSE 10000

# --------------------------------------------------------
# ✅ Start FastAPI app (Free-tier compatible)
# --------------------------------------------------------
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "10000"]
