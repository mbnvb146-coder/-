"""GPT-4 기반 블로그 글 자동 생성"""
import os
from openai import AsyncOpenAI

client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

SYSTEM_PROMPT = """당신은 네이버 블로그 전문 작가입니다.
주어진 주제로 네이버 블로그에 최적화된 글을 작성합니다.
글은 다음 구조를 따릅니다:
- 흥미로운 제목 (이모지 포함)
- 도입부: 독자의 관심을 끄는 서론 (2-3문장)
- 본문: 소제목(##)을 활용한 3-5개 섹션
- 각 섹션은 실용적이고 구체적인 내용
- 마무리: 행동 유도 문구 포함
- SEO를 위한 해시태그 5-10개

HTML 태그 없이 마크다운 형식으로 작성하세요."""


async def generate_blog_post(topic: str, style: str = "정보성", tone: str = "친근한") -> dict:
    """주제를 받아 블로그 글 생성"""
    user_prompt = f"""주제: {topic}
스타일: {style}
톤: {tone}

위 조건으로 네이버 블로그 포스팅을 작성해주세요.
제목은 첫 줄에 # 으로 시작하고, 마지막에 해시태그를 넣어주세요."""

    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.8,
        max_tokens=2000,
    )

    content = response.choices[0].message.content
    lines = content.strip().split("\n")

    title = ""
    for line in lines:
        if line.startswith("# "):
            title = line[2:].strip()
            break

    if not title:
        title = topic

    return {
        "title": title,
        "content": content,
        "topic": topic,
        "style": style,
        "tone": tone,
    }
