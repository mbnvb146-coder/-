FROM python:3.11-slim

# ffmpeg
RUN apt-get update && apt-get install -y ffmpeg --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download Whisper tiny model at build time
RUN python3 -c "from faster_whisper import WhisperModel; WhisperModel('tiny', device='cpu', compute_type='int8')" || true

COPY . .

RUN mkdir -p uploads drafts

ENV PORT=8000
EXPOSE 8000

CMD ["sh", "-c", "python3 -m uvicorn agent.server:app --host 0.0.0.0 --port ${PORT}"]
