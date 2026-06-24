"""네이버 블로그 포스팅 (Open API 사용)"""
import os
import httpx
import json
import re


NAVER_API_URL = "https://openapi.naver.com/blog/writePost.json"


def markdown_to_naver_html(md: str) -> str:
    """마크다운을 네이버 블로그용 HTML로 변환"""
    lines = md.split("\n")
    html_parts = []

    for line in lines:
        # H1
        if line.startswith("# "):
            html_parts.append(f'<h2 style="color:#333;font-size:22px;font-weight:bold;margin:20px 0 10px;">{line[2:].strip()}</h2>')
        # H2
        elif line.startswith("## "):
            html_parts.append(f'<h3 style="color:#444;font-size:18px;font-weight:bold;margin:16px 0 8px;border-left:4px solid #03C75A;padding-left:10px;">{line[3:].strip()}</h3>')
        # H3
        elif line.startswith("### "):
            html_parts.append(f'<h4 style="color:#555;font-size:16px;font-weight:bold;margin:12px 0 6px;">{line[4:].strip()}</h4>')
        # 해시태그 줄
        elif line.strip().startswith("#") and all(w.startswith("#") for w in line.strip().split()):
            tags = line.strip().split()
            tag_html = " ".join(f'<span style="color:#03C75A;font-size:14px;">{t}</span>' for t in tags)
            html_parts.append(f'<p style="margin:20px 0 5px;">{tag_html}</p>')
        # 빈 줄
        elif not line.strip():
            html_parts.append('<br>')
        # 일반 텍스트 (볼드/이탤릭 처리)
        else:
            text = line
            # **bold**
            text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
            # *italic*
            text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
            # 리스트
            if text.strip().startswith("- ") or text.strip().startswith("* "):
                text = f'<li style="margin:4px 0;">{text.strip()[2:]}</li>'
                html_parts.append(text)
                continue
            html_parts.append(f'<p style="line-height:1.8;margin:6px 0;">{text}</p>')

    return "\n".join(html_parts)


def inject_images_into_html(html: str, image_urls: list[str]) -> str:
    """이미지를 HTML에 삽입 (균등 배치)"""
    if not image_urls:
        return html

    img_tags = []
    for url in image_urls:
        img_tags.append(
            f'<div style="text-align:center;margin:20px 0;">'
            f'<img src="{url}" style="max-width:100%;border-radius:8px;"/>'
            f'</div>'
        )

    # 첫 번째 이미지: 맨 위
    result = img_tags[0] + html

    # 나머지 이미지: 본문 중간에 균등 배치
    if len(img_tags) > 1:
        result += "\n" + "\n".join(img_tags[1:])

    return result


async def post_to_naver_blog(
    title: str,
    html_content: str,
    access_token: str,
) -> dict:
    """네이버 블로그에 포스팅"""
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {
        "title": title,
        "contents": html_content,
        "categoryNo": "0",  # 기본 카테고리
    }

    async with httpx.AsyncClient(timeout=30) as h:
        resp = await h.post(NAVER_API_URL, headers=headers, data=data)

    if resp.status_code == 200:
        return {"success": True, "data": resp.json()}
    else:
        return {
            "success": False,
            "status_code": resp.status_code,
            "error": resp.text,
        }
