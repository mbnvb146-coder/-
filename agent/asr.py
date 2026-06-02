"""ASR via faster-whisper. Serialised with asyncio.Lock (no numba segfault)."""
import asyncio
import hashlib
import os
import subprocess
import tempfile
from typing import List, Dict, Any, Optional

from .ffmpeg_path import get_ffmpeg

# Lock created lazily inside running event loop (not at module import time)
_LOCK: Optional[asyncio.Lock] = None
_CACHE: Dict[str, List[Dict[str, Any]]] = {}
_MODEL = None


def _get_lock() -> asyncio.Lock:
    global _LOCK
    if _LOCK is None:
        _LOCK = asyncio.Lock()
    return _LOCK


def _content_hash(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _get_model(model_size: str):
    global _MODEL
    if _MODEL is None:
        from faster_whisper import WhisperModel
        _MODEL = WhisperModel(model_size, device="cpu", compute_type="int8")
    return _MODEL


async def transcribe(path: str, language: str = "ko", model_size: str = "tiny") -> List[Dict[str, Any]]:
    key = _content_hash(path)
    if key in _CACHE:
        return _CACHE[key]

    async with _get_lock():
        if key in _CACHE:
            return _CACHE[key]
        loop = asyncio.get_event_loop()
        segments = await loop.run_in_executor(None, _run_asr, path, language, model_size)
        _CACHE[key] = segments
        return segments


def _run_asr(path: str, language: str, model_size: str) -> List[Dict[str, Any]]:
    ffmpeg = get_ffmpeg()
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        wav = f.name
    try:
        subprocess.run(
            [ffmpeg, "-y", "-i", path, "-ac", "1", "-ar", "16000", "-vn", wav],
            capture_output=True, check=True,
        )
        model = _get_model(model_size)
        segs, _ = model.transcribe(wav, language=language, beam_size=5)
        return [
            {"start": s.start, "end": s.end, "text": s.text.strip()}
            for s in segs if s.text.strip()
        ]
    finally:
        if os.path.exists(wav):
            os.unlink(wav)
