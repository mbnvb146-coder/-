"""네이버 블로그 자동 작성 서버"""
import os
import uuid
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .blog_writer import generate_blog_post
from .image_generator import generate_blog_images
from .naver_poster import markdown_to_naver_html, inject_images_into_html
from .scheduler import (
    load_config, save_config, apply_schedule, start_scheduler,
    list_drafts, load_draft, save_draft, delete_draft,
    auto_generate_job,
)

BASE_DIR = Path(__file__).parent.parent


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    yield


app = FastAPI(title="네이버 블로그 자동 작성기", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    drafts = list_drafts()
    cfg = load_config()
    return templates.TemplateResponse("index.html", {
        "request": request,
        "drafts": drafts,
        "config": cfg,
    })


@app.post("/api/generate")
async def generate(
    topic: str = Form(...),
    style: str = Form("정보성"),
    tone: str = Form("친근한"),
    image_count: int = Form(2),
):
    if not os.environ.get("OPENAI_API_KEY"):
        raise HTTPException(400, "OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")

    post = await generate_blog_post(topic, style, tone)
    images = await generate_blog_images(topic, count=image_count)

    html_body = markdown_to_naver_html(post["content"])
    valid_urls = [img["url"] for img in images if img.get("url")]
    final_html = inject_images_into_html(html_body, valid_urls)

    from datetime import datetime
    draft = {
        "id": str(uuid.uuid4()),
        "title": post["title"],
        "markdown": post["content"],
        "html": final_html,
        "images": images,
        "topic": topic,
        "style": style,
        "tone": tone,
        "created_at": datetime.now().isoformat(),
        "auto": False,
    }
    save_draft(draft)
    return JSONResponse({"draft_id": draft["id"], "title": draft["title"]})


@app.post("/api/generate-now")
async def generate_now():
    """스케줄 설정 기반으로 즉시 1건 자동 생성"""
    if not os.environ.get("OPENAI_API_KEY"):
        raise HTTPException(400, "OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
    await auto_generate_job()
    drafts = list_drafts()
    if drafts:
        return JSONResponse({"draft_id": drafts[0]["id"], "title": drafts[0]["title"]})
    raise HTTPException(500, "생성 실패")


@app.get("/review/{draft_id}", response_class=HTMLResponse)
async def review(request: Request, draft_id: str):
    draft = load_draft(draft_id)
    if not draft:
        raise HTTPException(404, "초안을 찾을 수 없습니다.")
    return templates.TemplateResponse("review.html", {"request": request, "draft": draft})


@app.post("/api/update-draft/{draft_id}")
async def update_draft(draft_id: str, request: Request):
    draft = load_draft(draft_id)
    if not draft:
        raise HTTPException(404, "초안을 찾을 수 없습니다.")

    body = await request.json()
    if "title" in body:
        draft["title"] = body["title"]
    if "markdown" in body:
        draft["markdown"] = body["markdown"]
        html_body = markdown_to_naver_html(body["markdown"])
        valid_urls = [img["url"] for img in draft.get("images", []) if img.get("url")]
        draft["html"] = inject_images_into_html(html_body, valid_urls)

    save_draft(draft)
    return JSONResponse({"success": True, "html": draft["html"]})


@app.delete("/api/draft/{draft_id}")
async def remove_draft(draft_id: str):
    if delete_draft(draft_id):
        return JSONResponse({"success": True})
    raise HTTPException(404, "초안을 찾을 수 없습니다.")


@app.get("/api/draft/{draft_id}")
async def get_draft(draft_id: str):
    draft = load_draft(draft_id)
    if not draft:
        raise HTTPException(404, "초안을 찾을 수 없습니다.")
    return JSONResponse(draft)


@app.get("/api/drafts")
async def get_drafts():
    return JSONResponse(list_drafts())


@app.post("/api/schedule")
async def update_schedule(request: Request):
    body = await request.json()
    cfg = load_config()
    cfg.update(body)
    save_config(cfg)
    apply_schedule(cfg)
    return JSONResponse({"success": True, "config": cfg})


@app.get("/api/schedule")
async def get_schedule():
    return JSONResponse(load_config())
