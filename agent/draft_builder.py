"""Build CapCut draft using pycapcut."""
import os
from typing import List, Tuple, Dict, Any

from pycapcut.draft_folder import DraftFolder
from pycapcut.local_materials import VideoMaterial
from pycapcut.video_segment import VideoSegment
from pycapcut.text_segment import TextSegment, TextStyle, TextBorder
from pycapcut.time_util import Timerange
from pycapcut.segment import ClipSettings
from pycapcut.track import TrackType

US = 1_000_000  # 1 second in microseconds


def _us(sec: float) -> int:
    return int(sec * US)


def build_draft(
    video_path: str,
    total_duration: float,
    keep_intervals: List[Tuple[float, float]],
    subtitles: List[Dict[str, Any]],
    draft_root: str,
    draft_name: str,
) -> str:
    """
    Create CapCut draft folder under draft_root/draft_name.
    Returns the draft folder path.
    """
    folder = DraftFolder(draft_root)
    script = folder.create_draft(draft_name, 1080, 1920, fps=30, allow_replace=True)
    script.add_track(TrackType.video)
    script.add_track(TrackType.text)

    material = VideoMaterial(video_path)

    # Fallback: if every frame was cut, keep the whole video
    if not keep_intervals:
        keep_intervals = [(0.0, total_duration)]

    # Remap subtitles to edited timeline
    remapped = _remap_subs(subtitles, keep_intervals)

    # Add video segments + subtitle segments
    cursor = 0
    for src_s, src_e in keep_intervals:
        dur_us = _us(src_e - src_s)
        target_tr = Timerange(cursor, dur_us)
        source_tr = Timerange(_us(src_s), dur_us)
        vseg = VideoSegment(material, target_tr, source_timerange=source_tr)
        script.add_segment(vseg)
        cursor += dur_us

    # Text track: subtitle segments
    style = TextStyle(
        size=7.0,
        bold=True,
        color=(1.0, 1.0, 1.0),
        align=1,
        auto_wrapping=True,
        max_line_width=0.82,
    )
    border = TextBorder(color=(0.0, 0.0, 0.0), width=30.0)

    for sub in remapped:
        tr = Timerange(_us(sub["start"]), _us(sub["end"] - sub["start"]))
        # position near bottom via ClipSettings transform_y
        clip = ClipSettings(transform_y=-0.8)
        tseg = TextSegment(
            sub["text"], tr,
            style=style, border=border, clip_settings=clip,
        )
        script.add_segment(tseg)

    script.save()
    return os.path.dirname(script.save_path)


def _remap_subs(
    subtitles: List[Dict[str, Any]],
    keep_intervals: List[Tuple[float, float]],
) -> List[Dict[str, Any]]:
    """Remap subtitle timestamps to the edited timeline."""
    result = []
    cursor = 0.0
    for ks, ke in keep_intervals:
        for sub in subtitles:
            s = max(sub["start"], ks)
            e = min(sub["end"], ke)
            if e - s < 0.08:
                continue
            result.append({
                "text": sub["text"],
                "start": cursor + (s - ks),
                "end":   cursor + (e - ks),
            })
        cursor += ke - ks
    return result
