"""Resolve a working ffmpeg binary — lazy initialization (no subprocess at import time)."""
import shutil
import subprocess
import pathlib
from typing import Optional

_FFMPEG: Optional[str] = None
_FFPROBE: Optional[str] = None


def _check(path: str) -> bool:
    try:
        r = subprocess.run([path, "-version"], capture_output=True, timeout=5)
        return r.returncode == 0
    except Exception:
        return False


def _resolve() -> str:
    # 1. System ffmpeg (apt install ffmpeg in Docker)
    p = shutil.which("ffmpeg")
    if p and _check(p):
        return p
    # 2. imageio-ffmpeg static binary (local dev)
    try:
        import imageio_ffmpeg
        p = imageio_ffmpeg.get_ffmpeg_exe()
        if p and _check(p):
            return p
    except ImportError:
        pass
    raise RuntimeError("ffmpeg not found. Run: apt install ffmpeg")


def get_ffmpeg() -> str:
    global _FFMPEG
    if _FFMPEG is None:
        _FFMPEG = _resolve()
    return _FFMPEG


def get_ffprobe() -> str:
    global _FFPROBE
    if _FFPROBE is None:
        ff = get_ffmpeg()
        sibling = pathlib.Path(ff).parent / "ffprobe"
        _FFPROBE = str(sibling) if (sibling.exists() and _check(str(sibling))) else ff
    return _FFPROBE
