FROM python:3.11-slim

# ffmpeg (system — reliable in Docker)
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first (layer cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download Whisper tiny model so first request is fast
# (HuggingFace access required at build time; skip silently if blocked)
RUN python3 -c "\
from faster_whisper import WhisperModel; \
WhisperModel('tiny', device='cpu', compute_type='int8'); \
print('Whisper tiny model cached')" 2>&1 || echo "Whisper pre-cache skipped"

COPY . .

# Ensure runtime dirs exist
RUN mkdir -p uploads drafts

# Railway injects PORT env var; default 8000
ENV PORT=8000
EXPOSE 8000

CMD python3 -m uvicorn agent.server:app --host 0.0.0.0 --port $PORT
