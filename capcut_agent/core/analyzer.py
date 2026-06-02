"""Video analysis: detect silence, low-motion, and micro-jitter segments."""
import subprocess
import json
import os
import tempfile
from typing import List, Tuple
import numpy as np


def get_video_info(video_path: str) -> dict:
    """Return basic video metadata via ffprobe."""
    cmd = [
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_streams", "-show_format", video_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return json.loads(result.stdout)


def extract_audio(video_path: str, out_wav: str) -> None:
    """Extract mono 16kHz WAV for Whisper / librosa."""
    subprocess.run(
        ["ffmpeg", "-y", "-i", video_path, "-ac", "1", "-ar", "16000",
         "-vn", out_wav],
        capture_output=True,
    )


def detect_silence_ffmpeg(
    video_path: str,
    noise_db: float = -35.0,
    min_duration: float = 0.4,
) -> List[Tuple[float, float]]:
    """Return list of (start, end) silence intervals in seconds."""
    cmd = [
        "ffmpeg", "-i", video_path,
        "-af", f"silencedetect=noise={noise_db}dB:d={min_duration}",
        "-f", "null", "-",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    stderr = result.stderr

    silences: List[Tuple[float, float]] = []
    start = None
    for line in stderr.splitlines():
        if "silence_start" in line:
            start = float(line.split("silence_start: ")[1].split()[0])
        elif "silence_end" in line and start is not None:
            end = float(line.split("silence_end: ")[1].split("|")[0].strip())
            silences.append((start, end))
            start = None
    return silences


def detect_low_motion(
    video_path: str,
    sample_fps: float = 2.0,
    motion_threshold: float = 1.5,
    min_duration: float = 0.5,
) -> List[Tuple[float, float]]:
    """Return (start, end) intervals where motion is below threshold."""
    try:
        import cv2
    except ImportError:
        return []

    cap = cv2.VideoCapture(video_path)
    orig_fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    frame_skip = max(1, int(orig_fps / sample_fps))

    prev_gray = None
    frame_idx = 0
    low_motion_frames: List[Tuple[float, float]] = []
    seg_start = None

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if frame_idx % frame_skip == 0:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            t = frame_idx / orig_fps
            if prev_gray is not None:
                diff = cv2.absdiff(gray, prev_gray)
                score = float(np.mean(diff))
                if score < motion_threshold:
                    if seg_start is None:
                        seg_start = t
                else:
                    if seg_start is not None:
                        duration = t - seg_start
                        if duration >= min_duration:
                            low_motion_frames.append((seg_start, t))
                        seg_start = None
            prev_gray = gray
        frame_idx += 1

    if seg_start is not None:
        t = frame_idx / orig_fps
        if t - seg_start >= min_duration:
            low_motion_frames.append((seg_start, t))

    cap.release()
    return low_motion_frames


def merge_cut_intervals(
    intervals: List[Tuple[float, float]],
    gap: float = 0.1,
) -> List[Tuple[float, float]]:
    """Merge overlapping/adjacent cut intervals."""
    if not intervals:
        return []
    merged = sorted(intervals)
    result = [merged[0]]
    for start, end in merged[1:]:
        if start <= result[-1][1] + gap:
            result[-1] = (result[-1][0], max(result[-1][1], end))
        else:
            result.append((start, end))
    return result


def get_keep_intervals(
    total_duration: float,
    cut_intervals: List[Tuple[float, float]],
    min_keep: float = 0.2,
) -> List[Tuple[float, float]]:
    """Invert cut intervals to get segments to keep."""
    keep = []
    cursor = 0.0
    for cut_start, cut_end in sorted(cut_intervals):
        if cut_start - cursor >= min_keep:
            keep.append((cursor, cut_start))
        cursor = cut_end
    if total_duration - cursor >= min_keep:
        keep.append((cursor, total_duration))
    return keep
