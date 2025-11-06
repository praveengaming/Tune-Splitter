FROM python:3.10-slim

# install ffmpeg and git
RUN apt-get update && apt-get install -y ffmpeg git && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .

# install dependencies
RUN pip install --upgrade pip setuptools wheel && pip install -r requirements.txt

COPY . .

EXPOSE 10000
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "10000"]
