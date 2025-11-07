FROM python:3.10-slim

# 1️⃣ Install system dependencies
RUN apt-get update && \
    apt-get install -y ffmpeg libsndfile1 build-essential python3-dev && \
    rm -rf /var/lib/apt/lists/*

# 2️⃣ Set working directory
WORKDIR /app

# 3️⃣ Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 4️⃣ Copy app source
COPY . .

# 5️⃣ Expose port
EXPOSE 10000

# 6️⃣ Start the FastAPI app
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "10000"]
