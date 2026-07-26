"""OpenAI 이미지 생성."""
import base64
from pathlib import Path

from openai import OpenAI


def generate_image(
    client: OpenAI,
    model: str,
    prompt: str,
    output_path: Path,
    size: str = "1024x1024",
) -> Path:
    """프롬프트로 이미지를 생성해 output_path에 저장하고 경로를 반환한다."""
    result = client.images.generate(model=model, prompt=prompt, size=size, n=1)
    image_b64 = result.data[0].b64_json

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(base64.b64decode(image_b64))
    return output_path
