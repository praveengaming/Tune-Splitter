
FROM python:3.10-slim

RUN apt-get update && \
    apt-get install -y ffmpeg git libsndfile1 && \
    rm -rf /var/lib/apt/lists/*


WORKDIR /app


COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt


RUN python3 - <<'PYTHON'
from demucs.pretrained import get_model
for model_name in ["htdemucs", "mdx_extra"]:
    print(f"🔹 Downloading Demucs model: {model_name}")
    model = get_model(model_name)
    model.cpu()  # Ensure cached to CPU weights
print("✅ All Demucs models cached successfully.")
PYTHON


COPY . .

EXPOSE 10000


CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "10000"]
