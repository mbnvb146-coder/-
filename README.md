# 네이버 블로그 자동 작성기

GPT-4로 블로그 글을 자동 작성하고, DALL-E 3로 이미지를 자동 생성한 뒤, 최종 검토 후 네이버 블로그에 바로 게시할 수 있는 웹 앱입니다.

## 주요 기능

| 기능 | 설명 |
|------|------|
| ✍️ 글 자동 생성 | GPT-4o로 주제·스타일·톤에 맞는 블로그 글 작성 |
| 🖼️ 이미지 자동 생성 | DALL-E 3로 주제에 맞는 블로그 이미지 1-3장 생성 |
| 👁️ 미리보기 검토 | 게시 전 제목·본문·이미지 직접 수정 가능 |
| 🚀 1클릭 게시 | 검토 후 네이버 블로그에 바로 포스팅 |

## 설치

```bash
pip install -r requirements.txt
```

## 환경변수 설정

`.env.example`을 복사해 `.env`로 만들고 값을 채웁니다:

```bash
cp .env.example .env
```

```env
# 필수: OpenAI API 키
OPENAI_API_KEY=sk-...

# 선택: 네이버 액세스 토큰 (웹 UI에서도 입력 가능)
NAVER_ACCESS_TOKEN=
```

## 실행

```bash
python main.py
# 브라우저에서 http://localhost:8000 접속
```

## 사용 흐름

1. **주제 입력**: 블로그 주제, 스타일(정보성/리뷰/일상 등), 톤, 이미지 수 선택
2. **자동 생성**: GPT-4가 글 작성 + DALL-E 3가 이미지 생성 (약 20-40초)
3. **검토 페이지**: 제목·본문 자유롭게 수정, 이미지 선택/해제
4. **게시**: 네이버 액세스 토큰 입력 후 1클릭 게시

## 네이버 액세스 토큰 발급

1. [네이버 개발자센터](https://developers.naver.com) 앱 등록
2. 블로그 Write 권한 포함한 OAuth 인증
3. 발급된 `access_token`을 웹 UI 또는 `.env`에 입력

## 프로젝트 구조

```
├── agent/
│   ├── blog_writer.py      # GPT-4 블로그 글 생성
│   ├── image_generator.py  # DALL-E 3 이미지 생성
│   ├── naver_poster.py     # 네이버 블로그 API 포스팅
│   └── server.py           # FastAPI 서버
├── templates/
│   ├── index.html          # 생성 폼 페이지
│   └── review.html         # 검토/게시 페이지
├── main.py
└── requirements.txt
```

## Railway 배포

```toml
# railway.toml 이미 설정됨
# OPENAI_API_KEY 환경변수를 Railway 대시보드에 추가하세요
```
