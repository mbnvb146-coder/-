"""instagrapi를 이용한 인스타그램 로그인/업로드.

instagrapi는 인스타그램 비공식(모바일 내부) API를 사용하므로 인스타그램 이용약관 위반
소지가 있고, 과도한 자동화는 계정 제재로 이어질 수 있다. 개인 계정에서 낮은 빈도로
사용하는 용도로만 사용할 것.
"""
from pathlib import Path

from instagrapi import Client
from instagrapi.exceptions import LoginRequired


def get_client(username: str, password: str, session_path: str) -> Client:
    """세션 파일이 있으면 재사용하고, 없거나 만료되었으면 새로 로그인한다.

    최초 로그인 시 2단계 인증(2FA)이나 챌린지 코드를 콘솔에서 입력해야 할 수 있다.
    """
    cl = Client()
    session_file = Path(session_path)

    if session_file.exists():
        cl.load_settings(session_file)
        try:
            cl.login(username, password)
            cl.get_timeline_feed()  # 세션 유효성 확인
            return cl
        except LoginRequired:
            cl = Client()  # 세션 만료 -> 새 클라이언트로 재로그인

    cl.login(username, password)
    cl.dump_settings(session_file)
    return cl


def upload_photo(cl: Client, image_path: Path, caption: str):
    return cl.photo_upload(str(image_path), caption)
