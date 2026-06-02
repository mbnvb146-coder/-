FROM python:3.11-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p uploads drafts static

# Verify the app imports cleanly at build time — fail fast if broken
RUN python3 -c "from agent.server import app; print('import check OK')"

ENV PORT=8000
EXPOSE 8000

CMD ["python3", "start.py"]
