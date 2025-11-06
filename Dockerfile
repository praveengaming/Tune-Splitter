# --------------------------------------------------------
# 1️⃣ Use a lightweight, stable Python image
# --------------------------------------------------------
FROM python:3.10-slim

# --------------------------------------------------------
# 2️⃣ Install system dependencies
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
# 5️⃣ Robust model caching (Python-level initialization)
# --------------------------------------------------------
# This imports the Demucs package and ensures model weights
# are downloaded once during build — no input audio required.
RUN python3 - <<'PYTHON'
from demucs.pretrained import get_model
for model_name in ["htdemucs", "mdx_extra"]:
    print(f"🔹 Downloading Demucs model: {model_name}")
    model = get_model(model_name)
    model.cpu()  # Ensure cached to CPU weights
print("✅ All Demucs models cached successfully.")
PYTHON

# --------------------------------------------------------
# 6️⃣ Copy project files
# --------------------------------------------------------
COPY . .

# --------------------------------------------------------
# 7️⃣ Expose service port (Render uses dynamic env PORT=10000)
# --------------------------------------------------------
EXPOSE 10000

# --------------------------------------------------------
# 8️⃣ Start the FastAPI app
# --------------------------------------------------------
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "10000"]
