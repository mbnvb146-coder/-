# CapCut 미용실 쇼츠 에이전트

미용실 촬영 영상을 분석해 **상담 → 시술 → 완성본** 구조의 40-50초 쇼츠를 자동으로 컷편집하고 자막을 생성해 **CapCut 프로젝트 파일**로 출력합니다.

## 기능

| 기능 | 설명 |
|------|------|
| 🔇 침묵 컷 | 말이 없는 구간 자동 제거 |
| 🎬 저동작 컷 | 버벅임·잔동작 구간 자동 제거 |
| 📝 자막 생성 | Whisper AI로 한국어 자막 자동 생성 |
| ✂️ 쇼츠 구조 | 상담(핵심 발화) / 시술(하이라이트) / 완성본 자동 배분 |
| 📁 CapCut 출력 | `draft_content.json` 직접 생성 (앱에서 바로 열기) |

## 설치

```bash
pip install -r requirements.txt

# ffmpeg 필요
# macOS:  brew install ffmpeg
# Ubuntu: sudo apt install ffmpeg
# Windows: https://ffmpeg.org/download.html
```

## 사용법

### 기본 사용 (자동 구간 분배)
```bash
python -m capcut_agent.main 영상파일.mp4
```

### 구간 직접 지정 (더 정확한 편집)
```bash
# 상담 0~60초, 시술 60~180초, 완성 180초~끝
python -m capcut_agent.main 영상파일.mp4 --consult-end 60 --process-end 180
```

### 자막 없이 빠르게
```bash
python -m capcut_agent.main 영상파일.mp4 --no-subtitles
```

### 전체 옵션
```
  -o, --output-dir TEXT          출력 폴더 (기본: ./output)
  -p, --project-name TEXT        프로젝트 이름
  --consult-end FLOAT            상담 구간 종료 시각(초)
  --process-end FLOAT            시술 구간 종료 시각(초)
  --no-subtitles                 자막 생성 건너뛰기
  --whisper-model [tiny|base|small|medium]
  --silence-db FLOAT             침묵 감지 dB 임계값 (기본: -35)
  --silence-min FLOAT            최소 침묵 길이 초 (기본: 0.4)
  --motion-threshold FLOAT       저동작 감지 임계값 (기본: 1.5)
```

## CapCut에서 열기

1. 생성된 폴더(`output/영상명_shorts/`)를 스마트폰으로 복사
2. 복사 위치:
   - **Android**: `/storage/emulated/0/DCIM/CapCut/Projects/`
   - **iPhone**: `파일 앱 > CapCut > Projects/`
3. CapCut 재시작 → 프로젝트 목록에 나타남

## 프로젝트 구조

```
capcut_agent/
├── core/
│   ├── analyzer.py      # 영상 분석 (침묵/저동작 감지)
│   ├── salon_editor.py  # 미용실 쇼츠 편집 로직
│   └── transcriber.py   # Whisper 자막 생성
├── models/
│   └── capcut_schema.py # CapCut JSON 스키마
├── utils/
│   └── capcut_writer.py # 프로젝트 파일 출력
└── main.py              # CLI 진입점
```

---

## Instagram 자동 사진 업로드 (GPT 이미지 + 캡션)

`instagram_poster/` 모듈은 GPT로 사진과 캡션을 생성한 뒤 인스타그램에 자동으로 업로드합니다.

1. GPT 이미지 생성 모델(`gpt-image-1`)로 사진 생성
2. GPT 챗 모델로 주제에 맞는 캡션 + 해시태그 생성
3. [instagrapi](https://github.com/subzeroid/instagrapi)로 로그인 후 사진 업로드

### 설치

```bash
pip install -r requirements.txt
```

`instagram_poster/.env.example`을 프로젝트 루트에 `.env`로 복사하고 값을 채웁니다.

```bash
cp instagram_poster/.env.example .env
```

| 변수 | 설명 |
|------|------|
| `OPENAI_API_KEY` | OpenAI API 키 |
| `IG_USERNAME` / `IG_PASSWORD` | 인스타그램 로그인 계정 |
| `IG_SESSION_PATH` | 로그인 세션 캐시 파일 경로 (기본: `ig_session.json`) |
| `OPENAI_IMAGE_MODEL` | 이미지 생성 모델 (기본: `gpt-image-1`) |
| `OPENAI_CAPTION_MODEL` | 캡션 생성 모델 (기본: `gpt-4.1-mini`) |

### 사용법

```bash
# 이미지 + 캡션만 확인 (업로드 안 함)
python -m instagram_poster.main --prompt "노을 지는 해변, 미니멀한 감성 사진" --dry-run

# 실제 업로드
python -m instagram_poster.main \
  --prompt "노을 지는 해변, 미니멀한 감성 사진" \
  --topic "여름 휴가 감성"
```

- `--prompt`: 이미지 생성용 프롬프트
- `--topic`: 캡션 생성용 주제 (생략 시 `--prompt`를 그대로 사용)
- `--output`: 생성 이미지 저장 경로 (기본: `output/generated.png`)

### 주의사항

- **이용약관**: instagrapi는 인스타그램 비공식(모바일 내부) API를 사용합니다. 인스타그램 정책상 자동화는 계정 제재 사유가 될 수 있으니, 개인 계정에서 낮은 빈도로만 사용하세요. 비즈니스/크리에이터 계정으로 공식적인 방식이 필요하다면 Meta의 [Instagram Graph API](https://developers.facebook.com/docs/instagram-platform)(Facebook 페이지 연동, 이미지는 공개 URL 필요)를 고려하세요.
- **최초 로그인**: 인스타그램이 2단계 인증이나 챌린지 코드를 요구하면 콘솔에서 코드를 입력해야 할 수 있습니다. 로그인에 성공하면 세션이 `IG_SESSION_PATH`에 캐시되어 이후 실행에서는 재로그인 없이 동작합니다.
- **자동 스케줄링**: 정기적으로 자동 게시하고 싶다면 cron, GitHub Actions 스케줄 트리거, 혹은 APScheduler 등으로 `python -m instagram_poster.main ...` 명령을 주기 실행하면 됩니다.
