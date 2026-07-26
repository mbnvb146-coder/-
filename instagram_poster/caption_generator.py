"""OpenAI 챗 모델로 인스타그램 캡션 생성."""
from openai import OpenAI

CAPTION_SYSTEM_PROMPT = (
    "너는 인스타그램 마케팅 카피라이터야. 주어진 주제로 매력적인 한국어 캡션을 작성해줘. "
    "이모지를 자연스럽게 섞고, 본문 뒤에 줄바꿈 후 관련 해시태그를 8~12개 붙여. "
    "캡션 본문 외의 설명이나 따옴표는 출력하지 마."
)


def generate_caption(client: OpenAI, model: str, topic: str) -> str:
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": CAPTION_SYSTEM_PROMPT},
            {"role": "user", "content": f"주제: {topic}"},
        ],
    )
    return response.choices[0].message.content.strip()
