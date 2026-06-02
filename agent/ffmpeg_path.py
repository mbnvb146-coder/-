"""Resolve a working ffmpeg/ffprobe binary path."""
import os
import shutil
import subprocess


def _check(path: str) -> bool:
    try:
        subprocess.run([path, "-version"], capture_output=True, timeout=5)
        return True
    except Exception:
        return False


def _get() -> str:
    # 1. imageio-ffmpeg bundled static binary (always works on Linux)
    try:
        import imageio_ffmpeg
        p = imageio_ffmpeg.get_ffmpeg_exe()
        if _check(p):
            return p
    except ImportError:
        pass
    # 2. System PATH
    p = shutil.which("ffmpeg")
    if p and _check(p):
        return p
    raise RuntimeError(
        "ffmpeg를 찾을 수 없습니다. pip install imageio-ffmpeg 또는 ffmpeg를 설치하세요."
    )


FFMPEG = _get()

# ffprobe: same dir as ffmpeg binary, or substitute imageio's ffmpeg with -formats probe
import pathlib
_sibling = pathlib.Path(FFMPEG).parent / "ffprobe"
if _sibling.exists() and _check(str(_sibling)):
    FFPROBE = str(_sibling)
else:
    FFPROBE = FFMPEG  # ffprobe fallback: use ffmpeg -i for duration
