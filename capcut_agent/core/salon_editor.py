"""
Hair salon Shorts editor logic.

Workflow
--------
1. 상담 구간  : 영상 앞부분. 말이 많고 움직임 적음 → 핵심 발화 위주로 추출.
2. 시술 구간  : 중간. 실제 작업 장면 → 대표 하이라이트만.
3. 완성 구간  : 뒷부분. 최종 결과물 → 거의 통째로 보존.

목표 총 길이 : TARGET_MIN ~ TARGET_MAX 초 (기본 40-50 초).
"""

from typing import List, Tuple


TARGET_MIN = 40.0
TARGET_MAX = 50.0


def _clamp_section(
    intervals: List[Tuple[float, float]],
    sec_start: float,
    sec_end: float,
) -> List[Tuple[float, float]]:
    """Keep only the parts of intervals that lie within [sec_start, sec_end]."""
    result = []
    for s, e in intervals:
        cs = max(s, sec_start)
        ce = min(e, sec_end)
        if ce - cs > 0.05:
            result.append((cs, ce))
    return result


def _total(intervals: List[Tuple[float, float]]) -> float:
    return sum(e - s for s, e in intervals)


def build_salon_keep_intervals(
    total_duration: float,
    silence_cuts: List[Tuple[float, float]],
    motion_cuts: List[Tuple[float, float]],
    section_boundaries: Tuple[float, float] = None,
) -> List[Tuple[float, float]]:
    """
    Returns keep intervals for the final edit.

    section_boundaries: (consult_end, process_end)
        - [0, consult_end)       = consultation
        - [consult_end, proc_end) = treatment process
        - [proc_end, total)       = final result

    If None, uses heuristic 30%/40%/30% split.
    """
    if section_boundaries is None:
        consult_end = total_duration * 0.30
        proc_end = total_duration * 0.70
    else:
        consult_end, proc_end = section_boundaries

    # --- consultation: keep speech-active parts, max ~15s ---
    consult_cuts = _clamp_section(silence_cuts + motion_cuts, 0, consult_end)
    consult_keep = _invert(0, consult_end, consult_cuts)
    consult_keep = _trim_to_budget(consult_keep, 15.0)

    # --- treatment process: keep interesting motion, max ~10s ---
    proc_motion_cuts = _clamp_section(silence_cuts, consult_end, proc_end)
    proc_keep = _invert(consult_end, proc_end, proc_motion_cuts)
    proc_keep = _trim_to_budget(proc_keep, 10.0)

    # --- final result: keep almost everything, max ~20s ---
    finish_keep = _invert(proc_end, total_duration, [])
    finish_keep = _trim_to_budget(finish_keep, 20.0)

    all_keep = consult_keep + proc_keep + finish_keep

    # Enforce total duration limit
    all_keep = _trim_to_budget(all_keep, TARGET_MAX)

    return all_keep


def _invert(
    sec_start: float,
    sec_end: float,
    cut_intervals: List[Tuple[float, float]],
) -> List[Tuple[float, float]]:
    """Get keep intervals by inverting cuts within [sec_start, sec_end]."""
    keep = []
    cursor = sec_start
    for cs, ce in sorted(cut_intervals):
        cs = max(cs, sec_start)
        ce = min(ce, sec_end)
        if cs - cursor > 0.1:
            keep.append((cursor, cs))
        cursor = max(cursor, ce)
    if sec_end - cursor > 0.1:
        keep.append((cursor, sec_end))
    return keep


def _trim_to_budget(
    intervals: List[Tuple[float, float]],
    budget: float,
) -> List[Tuple[float, float]]:
    """Trim intervals from the end until total <= budget."""
    result = []
    remaining = budget
    for s, e in intervals:
        dur = e - s
        if remaining <= 0:
            break
        if dur <= remaining:
            result.append((s, e))
            remaining -= dur
        else:
            result.append((s, s + remaining))
            remaining = 0
    return result
