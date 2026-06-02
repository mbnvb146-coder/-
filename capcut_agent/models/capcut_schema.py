"""CapCut draft_content.json schema models."""
import uuid
import time
from dataclasses import dataclass, field
from typing import List, Optional


def new_id() -> str:
    return str(uuid.uuid4()).upper().replace("-", "")


def us(seconds: float) -> int:
    """Convert seconds to microseconds (CapCut time unit)."""
    return int(seconds * 1_000_000)


@dataclass
class VideoMaterial:
    path: str
    duration_us: int
    width: int = 1080
    height: int = 1920
    material_id: str = field(default_factory=new_id)

    def to_dict(self) -> dict:
        return {
            "id": self.material_id,
            "type": "video",
            "path": self.path,
            "duration": self.duration_us,
            "width": self.width,
            "height": self.height,
            "has_audio": True,
        }


@dataclass
class AudioMaterial:
    path: str
    duration_us: int
    material_id: str = field(default_factory=new_id)

    def to_dict(self) -> dict:
        return {
            "id": self.material_id,
            "type": "audio",
            "path": self.path,
            "duration": self.duration_us,
        }


@dataclass
class Segment:
    """A clip on the main video track."""
    material_id: str
    source_start_us: int
    source_end_us: int
    target_start_us: int
    target_end_us: int
    segment_id: str = field(default_factory=new_id)
    speed: float = 1.0

    @property
    def duration_us(self) -> int:
        return self.target_end_us - self.target_start_us

    def to_dict(self) -> dict:
        return {
            "id": self.segment_id,
            "material_id": self.material_id,
            "source_timerange": {
                "start": self.source_start_us,
                "duration": self.source_end_us - self.source_start_us,
            },
            "target_timerange": {
                "start": self.target_start_us,
                "duration": self.duration_us,
            },
            "speed": self.speed,
            "clip": {
                "alpha": 1.0,
                "flip": {"horizontal": False, "vertical": False},
                "rotation": 0.0,
                "scale": {"x": 1.0, "y": 1.0},
                "translation": {"x": 0.0, "y": 0.0},
            },
            "volume": 1.0,
        }


@dataclass
class TextSegment:
    """A subtitle/text segment."""
    text: str
    start_us: int
    end_us: int
    segment_id: str = field(default_factory=new_id)
    material_id: str = field(default_factory=new_id)
    font_size: float = 8.0
    color: str = "#FFFFFF"
    bold: bool = True

    def material_dict(self) -> dict:
        return {
            "id": self.material_id,
            "type": "text",
            "content": self.text,
            "font_size": self.font_size,
            "text_color": self.color,
            "bold": self.bold,
            "italic": False,
            "underline": False,
            "alignment": "center",
            "background_color": "",
            "background_alpha": 0.0,
            "border_color": "#000000",
            "border_width": 0.08,
            "line_spacing": 0.02,
            "letter_spacing": 0.0,
        }

    def track_dict(self) -> dict:
        return {
            "id": self.segment_id,
            "material_id": self.material_id,
            "target_timerange": {
                "start": self.start_us,
                "duration": self.end_us - self.start_us,
            },
            "clip": {
                "alpha": 1.0,
                "flip": {"horizontal": False, "vertical": False},
                "rotation": 0.0,
                "scale": {"x": 1.0, "y": 1.0},
                "translation": {"x": 0.0, "y": -0.7},
            },
        }


def build_draft(
    video_material: VideoMaterial,
    segments: List[Segment],
    subtitles: List[TextSegment],
    canvas_width: int = 1080,
    canvas_height: int = 1920,
) -> dict:
    """Build the CapCut draft_content.json dictionary."""
    total_duration = max((s.target_end_us for s in segments), default=0)

    text_materials = [s.material_dict() for s in subtitles]
    text_segments = [s.track_dict() for s in subtitles]

    tracks = [
        {
            "id": new_id(),
            "type": "video",
            "segments": [s.to_dict() for s in segments],
        }
    ]
    if subtitles:
        tracks.append(
            {
                "id": new_id(),
                "type": "text",
                "segments": text_segments,
            }
        )

    return {
        "canvas_config": {
            "width": canvas_width,
            "height": canvas_height,
            "ratio": "9:16",
        },
        "duration": total_duration,
        "fps": 30.0,
        "id": new_id(),
        "create_time": int(time.time()),
        "update_time": int(time.time()),
        "materials": {
            "videos": [video_material.to_dict()],
            "audios": [],
            "texts": text_materials,
            "stickers": [],
            "transitions": [],
            "effects": [],
        },
        "tracks": tracks,
        "version": 360000,
    }
