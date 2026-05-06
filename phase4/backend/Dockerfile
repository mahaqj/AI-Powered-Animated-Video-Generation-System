FROM python:3.11-slim

# Install ffmpeg
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy entire project (shared/, phase1-5/ all needed for imports)
COPY . /app

RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r phase4/backend/requirements.txt

EXPOSE 8000

CMD ["uvicorn", "phase4.backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
