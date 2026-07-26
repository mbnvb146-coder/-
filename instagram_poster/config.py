"""환경 변수 로딩 및 설정."""
import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    openai_api_key: str
    ig_username: str
    ig_password: str
    ig_session_path: str
    image_model: str
    caption_model: str


def load_settings() -> Settings:
    required = {
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
        "IG_USERNAME": os.getenv("IG_USERNAME"),
        "IG_PASSWORD": os.getenv("IG_PASSWORD"),
    }
    missing = [name for name, value in required.items() if not value]
    if missing:
        raise RuntimeError(
            f"환경 변수가 설정되지 않았습니다: {', '.join(missing)} (.env 파일을 확인하세요)"
        )

    return Settings(
        openai_api_key=required["OPENAI_API_KEY"],
        ig_username=required["IG_USERNAME"],
        ig_password=required["IG_PASSWORD"],
        ig_session_path=os.getenv("IG_SESSION_PATH", "ig_session.json"),
        image_model=os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-1"),
        caption_model=os.getenv("OPENAI_CAPTION_MODEL", "gpt-4.1-mini"),
    )
