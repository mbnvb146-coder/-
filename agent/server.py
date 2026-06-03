"""CapCut Agent — FastAPI server with SSE progress streaming."""
import asyncio
import json
import os
import shutil
import time
import uuid
import zipfile
from pathlib import Path
from io import BytesIO
from typing import AsyncGenerator

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse as FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import StreamingResponse

from .silence import detect_silence, silence_to_keep, get_duration
from .asr import transcribe
from .filler import detect_fillers, build_keep_intervals
from .draft_builder import build_draft

BASE = Path(__file__).parent.parent
UPLOAD_DIR = BASE / "uploads"
DRAFT_DIR  = BASE / "drafts"
STATIC_DIR = BASE / "static"

UPLOAD_DIR.mkdir(exist_ok=True)
DRAFT_DIR.mkdir(exist_ok=True)

app = FastAPI(title="CapCut Agent")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", response_class=HTMLResponse)
async def index():
    return (STATIC_DIR / "index.html").read_text(encoding="utf-8")


@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    job_id = uuid.uuid4().hex[:10]
    ext = Path(file.filename).suffix.lower() or ".mp4"
    dest = UPLOAD_DIR / f"{job_id}{ext}"
    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)
    return {"job_id": job_id, "filename": file.filename, "path": str(dest)}


@app.get("/process/{job_id}")
async def process(job_id: str, whisper: str = "base"):
    """SSE endpoint: streams pipeline steps."""
    # Find uploaded file
    matches = list(UPLOAD_DIR.glob(f"{job_id}.*"))
    if not matches:
        return JSONResponse({"error": "job not found"}, status_code=404)
    video_path = str(matches[0])

    return StreamingResponse(
        _pipeline_sse(job_id, video_path, whisper),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/download/{job_id}")
async def download(job_id: str):
    """Download the generated CapCut draft as a zip file."""
    draft_path = DRAFT_DIR / f"agent_{job_id}"
    if not draft_path.exists():
        return JSONResponse({"error": "draft not found"}, status_code=404)

    buf = BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in draft_path.iterdir():
            zf.write(f, f"agent_{job_id}/{f.name}")
    buf.seek(0)

    return FileResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=capcut_draft_{job_id}.zip"},
    )


async def _send(event: str, data: dict) -> str:
    await asyncio.sleep(0.5)   # min 0.5s per step for animation visibility
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


async def _pipeline_sse(
    job_id: str, video_path: str, whisper_model: str
) -> AsyncGenerator[str, None]:
    try:
        # ── Step 1: silence ──────────────────────────────────────────────
        yield await _send("step", {"step": "silence", "status": "running", "msg": "무음 구간 감지 중…"})
        total = get_duration(video_path)
        silences = detect_silence(video_path)
        keep_silence = silence_to_keep(total, silences)
        cut_secs = sum(e - s for s, e in silences)
        yield await _send("step", {
            "step": "silence", "status": "done",
            "msg": f"무음 {len(silences)}구간 감지",
            "detail": f"{cut_secs:.1f}s 제거 예정",
            "total": round(total, 2),
            "silences": len(silences),
            "cut_secs": round(cut_secs, 2),
        })

        # ── Step 2: ASR ──────────────────────────────────────────────────
        yield await _send("step", {"step": "asr", "status": "running", "msg": "음성 인식 중… (Whisper)"})
        asr_error = None
        try:
            segments = await transcribe(video_path, language="ko", model_size=whisper_model)
        except Exception as e:
            asr_error = str(e).split("\n")[0]
            segments = []
        word_count = sum(len(s["text"].split()) for s in segments)
        if asr_error:
            yield await _send("step", {
                "step": "asr", "status": "done",
                "msg": f"ASR 건너뜀 (모델 미설치)",
                "detail": "자막 없이 진행",
                "segments": 0, "words": 0, "transcript": [],
            })
        else:
            yield await _send("step", {
                "step": "asr", "status": "done",
                "msg": f"자막 세그먼트 {len(segments)}개",
                "detail": f"단어 {word_count}개",
                "segments": len(segments),
                "words": word_count,
                "transcript": [{"s": round(s["start"],2), "e": round(s["end"],2), "t": s["text"]} for s in segments[:40]],
            })

        # ── Step 3: filler / NG ──────────────────────────────────────────
        yield await _send("step", {"step": "filler", "status": "running", "msg": "잔말·NG 감지 중…"})
        fillers = detect_fillers(segments)
        keep_intervals = build_keep_intervals(total, silences, fillers)
        edited_dur = sum(e - s for s, e in keep_intervals)
        yield await _send("step", {
            "step": "filler", "status": "done",
            "msg": f"잔말/NG {len(fillers)}개 제거",
            "detail": f"편집 후 {edited_dur:.1f}s",
            "fillers": len(fillers),
            "keep_count": len(keep_intervals),
            "edited_dur": round(edited_dur, 2),
            "filler_list": [{"s": round(f["start"],2), "e": round(f["end"],2), "t": f["text"], "r": f["reason"]} for f in fillers],
        })

        # ── Step 4: draft ────────────────────────────────────────────────
        yield await _send("step", {"step": "draft", "status": "running", "msg": "CapCut 드래프트 생성 중…"})
        draft_name = f"agent_{job_id}"
        draft_path = build_draft(
            video_path=video_path,
            total_duration=total,
            keep_intervals=keep_intervals,
            subtitles=segments,
            draft_root=str(DRAFT_DIR),
            draft_name=draft_name,
        )
        yield await _send("step", {
            "step": "draft", "status": "done",
            "msg": "드래프트 생성 완료",
            "detail": draft_path,
            "draft_path": draft_path,
            "draft_name": draft_name,
        })

        yield await _send("done", {
            "job_id": job_id,
            "total": round(total, 2),
            "edited": round(edited_dur, 2),
            "removed": round(total - edited_dur, 2),
            "ratio": round((total - edited_dur) / total * 100, 1),
            "draft_path": draft_path,
            "segments": len(segments),
            "fillers": len(fillers),
            "silences": len(silences),
            "transcript": [{"s": round(s["start"],2), "e": round(s["end"],2), "t": s["text"]} for s in segments],
        })

    except Exception as exc:
        import traceback
        yield await _send("error", {"msg": str(exc), "trace": traceback.format_exc()})
