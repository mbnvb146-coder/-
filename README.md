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
