"""Resolve a working ffmpeg binary. Prefers system ffmpeg (Docker), falls back to imageio-ffmpeg."""
import shutil
import subprocess
import pathlib


def _check(path: str) -> bool:
    try:
        r = subprocess.run([path, "-version"], capture_output=True, timeout=5)
        return r.returncode == 0
    except Exception:
        return False


def _get() -> str:
    # 1. System ffmpeg (installed via apt in Docker)
    p = shutil.which("ffmpeg")
    if p and _check(p):
        return p

    # 2. imageio-ffmpeg bundled static binary (local dev fallback)
    try:
        import imageio_ffmpeg
        p = imageio_ffmpeg.get_ffmpeg_exe()
        if _check(p):
            return p
    except ImportError:
        pass

    raise RuntimeError(
        "ffmpeg not found. Install with: apt install ffmpeg  or  pip install imageio-ffmpeg"
    )


FFMPEG = _get()

# ffprobe: look next to ffmpeg binary
_sibling = pathlib.Path(FFMPEG).parent / "ffprobe"
FFPROBE = str(_sibling) if (_sibling.exists() and _check(str(_sibling))) else FFMPEG
