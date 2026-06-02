"""Write a CapCut-compatible project folder."""
import json
import os
import shutil
from typing import List, Tuple

from ..models.capcut_schema import (
    VideoMaterial, Segment, TextSegment, build_draft, us
)


def create_capcut_project(
    video_path: str,
    video_duration: float,
    keep_intervals: List[Tuple[float, float]],
    subtitles: List[dict],
    output_dir: str,
    project_name: str = "salon_shorts",
    video_width: int = 1080,
    video_height: int = 1920,
) -> str:
    """
    Write a CapCut project folder containing draft_content.json.

    Returns the path to the project folder.
    """
    project_path = os.path.join(output_dir, project_name)
    os.makedirs(project_path, exist_ok=True)

    material = VideoMaterial(
        path=os.path.abspath(video_path),
        duration_us=us(video_duration),
        width=video_width,
        height=video_height,
    )

    # Build timeline segments
    segments: List[Segment] = []
    cursor = 0
    for src_s, src_e in keep_intervals:
        seg = Segment(
            material_id=material.material_id,
            source_start_us=us(src_s),
            source_end_us=us(src_e),
            target_start_us=cursor,
            target_end_us=cursor + us(src_e - src_s),
        )
        segments.append(seg)
        cursor += us(src_e - src_s)

    # Build subtitle segments
    text_segs: List[TextSegment] = []
    for sub in subtitles:
        ts = TextSegment(
            text=sub["text"],
            start_us=us(sub["start"]),
            end_us=us(sub["end"]),
        )
        text_segs.append(ts)

    draft = build_draft(
        video_material=material,
        segments=segments,
        subtitles=text_segs,
        canvas_width=video_width,
        canvas_height=video_height,
    )

    draft_path = os.path.join(project_path, "draft_content.json")
    with open(draft_path, "w", encoding="utf-8") as f:
        json.dump(draft, f, ensure_ascii=False, indent=2)

    # Write a human-readable cut summary
    summary_path = os.path.join(project_path, "cut_summary.txt")
    total_kept = sum(e - s for s, e in keep_intervals)
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(f"원본 영상: {video_path}\n")
        f.write(f"원본 길이: {video_duration:.1f}초\n")
        f.write(f"편집 후 길이: {total_kept:.1f}초\n")
        f.write(f"유지 구간 수: {len(keep_intervals)}\n\n")
        f.write("=== 유지 구간 ===\n")
        for i, (s, e) in enumerate(keep_intervals, 1):
            f.write(f"  [{i:02d}] {s:7.2f}s ~ {e:7.2f}s  ({e-s:.2f}s)\n")
        if subtitles:
            f.write("\n=== 자막 ===\n")
            for sub in subtitles:
                f.write(f"  [{sub['start']:6.2f}s] {sub['text']}\n")

    return project_path
