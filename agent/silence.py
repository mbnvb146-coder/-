"""Silence detection via ffmpeg silencedetect filter."""
import subprocess
import re
from typing import List, Tuple

from .ffmpeg_path import FFMPEG, FFPROBE


def detect_silence(
    path: str,
    noise_db: float = -35.0,
    min_dur: float = 0.35,
) -> List[Tuple[float, float]]:
    """Return list of (start, end) silence intervals in seconds."""
    cmd = [
        FFMPEG, "-hide_banner", "-i", path,
        "-af", f"silencedetect=noise={noise_db}dB:d={min_dur}",
        "-f", "null", "-",
    ]
    out = subprocess.run(cmd, capture_output=True, text=True).stderr
    starts = [float(m) for m in re.findall(r"silence_start: ([\d.]+)", out)]
    ends   = [float(m) for m in re.findall(r"silence_end: ([\d.]+)", out)]
    return list(zip(starts, ends[:len(starts)]))


def silence_to_keep(
    total: float,
    silences: List[Tuple[float, float]],
    pad: float = 0.05,
) -> List[Tuple[float, float]]:
    """Invert silence list → keep intervals with small padding."""
    keep: List[Tuple[float, float]] = []
    cur = 0.0
    for s, e in sorted(silences):
        seg_end = max(cur, s - pad)
        if seg_end - cur > 0.1:
            keep.append((cur, seg_end))
        cur = e + pad
    if total - cur > 0.1:
        keep.append((cur, total))
    return keep


def get_duration(path: str) -> float:
    """Return video duration in seconds."""
    # Use ffmpeg -i and parse 'Duration:' line (works without ffprobe)
    r = subprocess.run(
        [FFMPEG, "-hide_banner", "-i", path],
        capture_output=True, text=True,
    )
    for line in (r.stdout + r.stderr).splitlines():
        if "Duration:" in line:
            t = line.split("Duration:")[1].split(",")[0].strip()  # HH:MM:SS.ss
            h, m, s = t.split(":")
            return float(h) * 3600 + float(m) * 60 + float(s)
    raise ValueError(f"Duration not found in ffmpeg output for {path}")
