"""
Filler / NG detection from transcript segments.

Filler words (잔말): 어, 음, 아, 그, 뭐, 저, 이제, 사실, 근데, 그니까, 그래서 등
NG patterns: 다시, 잠깐만, 잠깐, 끊어, 아 잠깐, 아 맞다 등
"""
import re
from typing import List, Dict, Any, Tuple

FILLER_RE = re.compile(
    r"^(어+|음+|아+|그+|뭐|저+|이제|사실|근데|그니까|그래서|그거|아니|잠깐|"
    r"어쨌든|뭐랄까|그러니까|일단|사실은|좀|네+|예+|맞아+)[,.\s]*$",
    re.IGNORECASE,
)
NG_RE = re.compile(
    r"(다시\s*(해|합시다|할게|하겠)|잠깐만|끊어|잠깐|NG|엔지|"
    r"아\s*잠깐|에러|실수했|다시\s*찍)",
    re.IGNORECASE,
)


def detect_fillers(segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Return segments flagged as filler or NG."""
    flagged = []
    for seg in segments:
        t = seg["text"].strip()
        reason = None
        if FILLER_RE.match(t):
            reason = "filler"
        elif NG_RE.search(t):
            reason = "ng"
        if reason:
            flagged.append({**seg, "reason": reason})
    return flagged


def build_keep_intervals(
    total: float,
    silence_cuts: List[Tuple[float, float]],
    filler_segs: List[Dict[str, Any]],
    pad: float = 0.05,
) -> List[Tuple[float, float]]:
    """
    Merge silence cuts + filler/NG segment cuts, then invert.
    Returns keep intervals sorted by start.
    """
    cuts: List[Tuple[float, float]] = list(silence_cuts)
    for seg in filler_segs:
        cuts.append((max(0.0, seg["start"] - pad), seg["end"] + pad))

    # Sort and merge
    cuts.sort()
    merged: List[Tuple[float, float]] = []
    for s, e in cuts:
        if merged and s <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], e))
        else:
            merged.append((s, e))

    # Invert
    keep: List[Tuple[float, float]] = []
    cur = 0.0
    for s, e in merged:
        if s - cur > 0.1:
            keep.append((cur, s))
        cur = e
    if total - cur > 0.1:
        keep.append((cur, total))
    return keep
