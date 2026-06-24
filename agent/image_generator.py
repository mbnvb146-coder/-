"""DALL-E 3 기반 블로그 이미지 자동 생성"""
import os
import httpx
import base64
from openai import AsyncOpenAI

client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


async def generate_blog_images(topic: str, count: int = 2) -> list[dict]:
    """블로그 주제에 맞는 이미지 생성 (최대 3장)"""
    count = min(count, 3)
    prompts = _make_prompts(topic, count)
    images = []

    for i, prompt in enumerate(prompts):
        try:
            response = await client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1792x1024",
                quality="standard",
                n=1,
            )
            url = response.data[0].url
            revised = response.data[0].revised_prompt
            images.append({
                "index": i,
                "url": url,
                "prompt": prompt,
                "revised_prompt": revised,
                "caption": f"이미지 {i + 1}",
            })
        except Exception as e:
            images.append({
                "index": i,
                "url": None,
                "error": str(e),
                "prompt": prompt,
                "caption": f"이미지 {i + 1} (생성 실패)",
            })

    return images


def _make_prompts(topic: str, count: int) -> list[str]:
    """주제별 이미지 프롬프트 생성"""
    base = f"A high-quality blog header image for a Korean blog post about: {topic}. "
    styles = [
        base + "Bright, modern, clean aesthetic. No text overlay. Photorealistic.",
        base + "Flat design illustration style, pastel colors, minimalist. No text.",
        base + "Professional lifestyle photography style, warm tones. No text.",
    ]
    return styles[:count]


async def download_image_as_base64(url: str) -> str | None:
    """이미지 URL을 base64로 다운로드 (미리보기용)"""
    try:
        async with httpx.AsyncClient(timeout=30) as h:
            r = await h.get(url)
            r.raise_for_status()
            return base64.b64encode(r.content).decode()
    except Exception:
        return None
