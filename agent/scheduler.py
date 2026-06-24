"""블로그 자동 생성 스케줄러"""
import os
import json
import uuid
import asyncio
from datetime import datetime
from pathlib import Path

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from .blog_writer import generate_blog_post
from .image_generator import generate_blog_images
from .naver_poster import markdown_to_naver_html, inject_images_into_html

DRAFTS_DIR = Path("drafts")
DRAFTS_DIR.mkdir(exist_ok=True)

CONFIG_FILE = Path("schedule_config.json")

DEFAULT_CONFIG = {
    "enabled": False,
    "hour": 9,
    "minute": 0,
    "days": ["mon", "wed", "fri"],
    "category": "라이프스타일",
    "style": "정보성",
    "tone": "친근한",
    "image_count": 2,
    "keywords": [],
}

scheduler = AsyncIOScheduler(timezone="Asia/Seoul")


def load_config() -> dict:
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, encoding="utf-8") as f:
            cfg = json.load(f)
        # 새 키 기본값 채우기
        for k, v in DEFAULT_CONFIG.items():
            cfg.setdefault(k, v)
        return cfg
    return DEFAULT_CONFIG.copy()


def save_config(cfg: dict):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


def list_drafts() -> list[dict]:
    drafts = []
    for p in sorted(DRAFTS_DIR.glob("*.json"), reverse=True):
        try:
            with open(p, encoding="utf-8") as f:
                d = json.load(f)
            drafts.append(d)
        except Exception:
            pass
    return drafts


def load_draft(draft_id: str) -> dict | None:
    p = DRAFTS_DIR / f"{draft_id}.json"
    if not p.exists():
        return None
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def save_draft(draft: dict):
    p = DRAFTS_DIR / f"{draft['id']}.json"
    with open(p, "w", encoding="utf-8") as f:
        json.dump(draft, f, ensure_ascii=False, indent=2)


def delete_draft(draft_id: str) -> bool:
    p = DRAFTS_DIR / f"{draft_id}.json"
    if p.exists():
        p.unlink()
        return True
    return False


async def _pick_topic(cfg: dict) -> str:
    """키워드 목록이 있으면 순서대로, 없으면 GPT가 자동 선정"""
    from openai import AsyncOpenAI
    client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    keywords = cfg.get("keywords", [])
    if keywords:
        # 이미 생성된 주제 확인 후 안 쓴 것 선택
        used = {d.get("topic", "") for d in list_drafts()}
        for kw in keywords:
            if kw not in used:
                return kw
        return keywords[0]  # 모두 썼으면 처음으로

    # GPT가 카테고리에 맞는 인기 주제 자동 선정
    category = cfg.get("category", "라이프스타일")
    today = datetime.now().strftime("%Y년 %m월 %d일")
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": f"오늘({today}) 네이버 블로그에 올리기 좋은 '{category}' 카테고리 주제를 딱 1개만 추천해주세요. 주제만 짧게, 예시처럼: '봄철 피부 관리 루틴 5가지'"
        }],
        max_tokens=50,
    )
    return response.choices[0].message.content.strip().strip('"').strip("'")


async def auto_generate_job():
    """스케줄러가 실행하는 자동 생성 작업"""
    cfg = load_config()
    if not os.environ.get("OPENAI_API_KEY"):
        print("[스케줄러] OPENAI_API_KEY 미설정 — 건너뜀")
        return

    print(f"[스케줄러] 자동 블로그 생성 시작 ({datetime.now().strftime('%Y-%m-%d %H:%M')})")

    try:
        topic = await _pick_topic(cfg)
        print(f"[스케줄러] 주제: {topic}")

        post = await generate_blog_post(topic, cfg["style"], cfg["tone"])
        images = await generate_blog_images(topic, count=cfg["image_count"])

        html_body = markdown_to_naver_html(post["content"])
        valid_urls = [img["url"] for img in images if img.get("url")]
        final_html = inject_images_into_html(html_body, valid_urls)

        draft = {
            "id": str(uuid.uuid4()),
            "title": post["title"],
            "markdown": post["content"],
            "html": final_html,
            "images": images,
            "topic": topic,
            "style": cfg["style"],
            "tone": cfg["tone"],
            "created_at": datetime.now().isoformat(),
            "auto": True,
        }
        save_draft(draft)
        print(f"[스케줄러] 완료: {draft['title']}")
    except Exception as e:
        print(f"[스케줄러] 오류: {e}")


def apply_schedule(cfg: dict):
    """스케줄 설정 적용"""
    scheduler.remove_all_jobs()
    if not cfg.get("enabled"):
        return

    days = ",".join(cfg.get("days", ["mon"]))
    trigger = CronTrigger(
        day_of_week=days,
        hour=cfg["hour"],
        minute=cfg["minute"],
        timezone="Asia/Seoul",
    )
    scheduler.add_job(auto_generate_job, trigger=trigger, id="auto_blog")
    print(f"[스케줄러] 등록됨: {days} {cfg['hour']:02d}:{cfg['minute']:02d} KST")


def start_scheduler():
    cfg = load_config()
    apply_schedule(cfg)
    scheduler.start()
