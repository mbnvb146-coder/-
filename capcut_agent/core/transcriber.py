"""Speech-to-text using Whisper for Korean subtitle generation."""
import os
import tempfile
from typing import List, Tuple

from ..core.analyzer import extract_audio


def transcribe(
    video_path: str,
    language: str = "ko",
    model_size: str = "base",
) -> List[dict]:
    """
    Run Whisper transcription.
    Returns list of {start, end, text} dicts.
    """
    try:
        import whisper
    except ImportError:
        raise RuntimeError(
            "openai-whisper not installed. Run: pip install openai-whisper"
        )

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        wav_path = f.name

    try:
        extract_audio(video_path, wav_path)
        model = whisper.load_model(model_size)
        result = model.transcribe(wav_path, language=language, word_timestamps=False)
        segments = [
            {"start": seg["start"], "end": seg["end"], "text": seg["text"].strip()}
            for seg in result["segments"]
            if seg["text"].strip()
        ]
    finally:
        os.unlink(wav_path)

    return segments


def remap_subtitle_times(
    subtitles: List[dict],
    keep_intervals: List[Tuple[float, float]],
) -> List[dict]:
    """
    Remap subtitle timestamps to the edited timeline.
    Subtitles that fall entirely in cut sections are dropped.
    Subtitles that overlap a kept section are trimmed.
    """
    remapped = []
    cursor = 0.0  # position in output timeline

    for keep_start, keep_end in keep_intervals:
        keep_dur = keep_end - keep_start

        for sub in subtitles:
            # Clamp subtitle to this keep interval
            s = max(sub["start"], keep_start)
            e = min(sub["end"], keep_end)
            if e - s < 0.1:
                continue

            # Offset into output timeline
            out_start = cursor + (s - keep_start)
            out_end = cursor + (e - keep_start)
            remapped.append(
                {"start": out_start, "end": out_end, "text": sub["text"]}
            )

        cursor += keep_dur

    return remapped
