# --------------------------------------------------------
# ✅ Stable, Optimized Dockerfile for Demucs + FastAPI
# --------------------------------------------------------
FROM python:3.10-slim

# 1️⃣ Install system dependencies
RUN apt-get update && \
    apt-get install -y ffmpeg git libsndfile1 && \
    rm -rf /var/lib/apt/lists/*

# 2️⃣ Set working directory
WORKDIR /app

# 3️⃣ Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 4️⃣ Pre-cache Demucs models (optional but faster first run)
RUN python3 - <<'PYTHON'
from demucs.pretrained import get_model
for model_name in ["htdemucs", "mdx_extra"]:
    print(f"🔹 Downloading Demucs model: {model_name}")
    model = get_model(model_name)
    model.cpu()
print("✅ All Demucs models cached successfully.")
PYTHON

# 5️⃣ Copy app source
COPY . .

# 6️⃣ Expose API port
EXPOSE 10000

# 7️⃣ Start FastAPI app
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "10000"]
