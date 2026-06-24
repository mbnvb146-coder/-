"""네이버 블로그 자동 작성 서버"""
import os
import json
import uuid
from pathlib import Path

from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .blog_writer import generate_blog_post
from .image_generator import generate_blog_images
from .naver_poster import markdown_to_naver_html, inject_images_into_html, post_to_naver_blog

app = FastAPI(title="네이버 블로그 자동 작성기")

BASE_DIR = Path(__file__).parent.parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")

# 임시 초안 저장소 (메모리)
drafts: dict[str, dict] = {}


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/api/generate")
async def generate(
    topic: str = Form(...),
    style: str = Form("정보성"),
    tone: str = Form("친근한"),
    image_count: int = Form(2),
):
    """블로그 글 + 이미지 자동 생성"""
    if not os.environ.get("OPENAI_API_KEY"):
        raise HTTPException(400, "OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")

    # 글 생성
    post = await generate_blog_post(topic, style, tone)

    # 이미지 생성
    images = await generate_blog_images(topic, count=image_count)

    # HTML 변환
    html_body = markdown_to_naver_html(post["content"])
    valid_urls = [img["url"] for img in images if img.get("url")]
    final_html = inject_images_into_html(html_body, valid_urls)

    draft_id = str(uuid.uuid4())
    drafts[draft_id] = {
        "id": draft_id,
        "title": post["title"],
        "markdown": post["content"],
        "html": final_html,
        "images": images,
        "topic": topic,
        "style": style,
        "tone": tone,
    }

    return JSONResponse({"draft_id": draft_id, "title": post["title"]})


@app.get("/review/{draft_id}", response_class=HTMLResponse)
async def review(request: Request, draft_id: str):
    """최종 검토 페이지"""
    draft = drafts.get(draft_id)
    if not draft:
        raise HTTPException(404, "초안을 찾을 수 없습니다.")
    return templates.TemplateResponse("review.html", {"request": request, "draft": draft})


@app.post("/api/update-draft/{draft_id}")
async def update_draft(draft_id: str, request: Request):
    """검토 후 수정 내용 저장"""
    draft = drafts.get(draft_id)
    if not draft:
        raise HTTPException(404, "초안을 찾을 수 없습니다.")

    body = await request.json()
    if "title" in body:
        draft["title"] = body["title"]
    if "markdown" in body:
        draft["markdown"] = body["markdown"]
        html_body = markdown_to_naver_html(body["markdown"])
        valid_urls = [img["url"] for img in draft["images"] if img.get("url")]
        draft["html"] = inject_images_into_html(html_body, valid_urls)

    return JSONResponse({"success": True, "html": draft["html"]})


@app.post("/api/publish/{draft_id}")
async def publish(draft_id: str, request: Request):
    """네이버 블로그에 최종 게시"""
    draft = drafts.get(draft_id)
    if not draft:
        raise HTTPException(404, "초안을 찾을 수 없습니다.")

    body = await request.json()
    access_token = body.get("access_token") or os.environ.get("NAVER_ACCESS_TOKEN", "")

    if not access_token:
        raise HTTPException(400, "네이버 액세스 토큰이 필요합니다.")

    result = await post_to_naver_blog(
        title=draft["title"],
        html_content=draft["html"],
        access_token=access_token,
    )

    return JSONResponse(result)


@app.get("/api/draft/{draft_id}")
async def get_draft(draft_id: str):
    draft = drafts.get(draft_id)
    if not draft:
        raise HTTPException(404, "초안을 찾을 수 없습니다.")
    return JSONResponse(draft)
