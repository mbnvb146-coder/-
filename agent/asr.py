"""ASR via faster-whisper (Linux EE-C path). Serialised with asyncio.Lock."""
import asyncio
import hashlib
import os
import subprocess
import tempfile
from typing import List, Dict, Any

from .ffmpeg_path import FFMPEG

_LOCK = asyncio.Lock()
_CACHE: Dict[str, List[Dict[str, Any]]] = {}   # content_hash → segments
_MODEL = None


def _content_hash(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _get_model(model_size: str = "base"):
    global _MODEL
    if _MODEL is None:
        from faster_whisper import WhisperModel
        _MODEL = WhisperModel(model_size, device="cpu", compute_type="int8")
    return _MODEL


async def transcribe(path: str, language: str = "ko", model_size: str = "base") -> List[Dict[str, Any]]:
    """
    Async transcription — serialised via Lock to avoid numba segfault.
    Returns list of {start, end, text} segment dicts.
    Caches by content hash.
    """
    key = _content_hash(path)
    if key in _CACHE:
        return _CACHE[key]

    async with _LOCK:
        # Double-check after acquiring
        if key in _CACHE:
            return _CACHE[key]

        # Run in executor so we don't block the event loop
        loop = asyncio.get_event_loop()
        segments = await loop.run_in_executor(None, _run_asr, path, language, model_size)
        _CACHE[key] = segments
        return segments


def _run_asr(path: str, language: str, model_size: str) -> List[Dict[str, Any]]:
    # Extract mono 16kHz WAV
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        wav = f.name
    try:
        subprocess.run(
            [FFMPEG, "-y", "-i", path, "-ac", "1", "-ar", "16000", "-vn", wav],
            capture_output=True, check=True,
        )
        model = _get_model(model_size)
        segs, _ = model.transcribe(wav, language=language, beam_size=5)
        result = []
        for s in segs:
            text = s.text.strip()
            if text:
                result.append({"start": s.start, "end": s.end, "text": text})
        return result
    finally:
        os.unlink(wav)
