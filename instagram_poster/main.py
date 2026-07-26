"""GPT로 사진 + 캡션을 만들고 인스타그램에 자동 업로드하는 CLI.

사용 예:
    python -m instagram_poster.main --prompt "노을 지는 해변, 미니멀한 감성 사진" --topic "여름 휴가"
"""
import argparse
from pathlib import Path

from openai import OpenAI

from .caption_generator import generate_caption
from .config import load_settings
from .image_generator import generate_image
from .uploader import get_client, upload_photo


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="GPT로 사진과 캡션을 만들어 인스타그램에 자동 업로드합니다."
    )
    parser.add_argument("--prompt", required=True, help="이미지 생성 프롬프트")
    parser.add_argument("--topic", help="캡션 생성 주제 (미입력 시 --prompt 재사용)")
    parser.add_argument("--size", default="1024x1024", help="이미지 크기 (기본: 1024x1024)")
    parser.add_argument(
        "--output", default="output/generated.png", help="생성된 이미지 저장 경로"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="인스타그램 업로드 없이 이미지/캡션만 생성해서 확인",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    settings = load_settings()
    client = OpenAI(api_key=settings.openai_api_key)

    print("[1/3] 이미지 생성 중...")
    image_path = generate_image(
        client, settings.image_model, args.prompt, Path(args.output), size=args.size
    )
    print(f"      -> {image_path}")

    print("[2/3] 캡션 생성 중...")
    caption = generate_caption(client, settings.caption_model, args.topic or args.prompt)
    print("--- 캡션 ---")
    print(caption)
    print("------------")

    if args.dry_run:
        print("[dry-run] 인스타그램 업로드를 건너뜁니다.")
        return

    print("[3/3] 인스타그램 로그인 및 업로드 중...")
    cl = get_client(settings.ig_username, settings.ig_password, settings.ig_session_path)
    media = upload_photo(cl, image_path, caption)
    print(f"업로드 완료! media id: {media.pk}")


if __name__ == "__main__":
    main()
