"""
CapCut 미용실 쇼츠 에이전트 CLI

사용법:
  python -m capcut_agent.main <video_file> [옵션]

예시:
  python -m capcut_agent.main consultation.mp4
  python -m capcut_agent.main consultation.mp4 --consult-end 60 --process-end 180
  python -m capcut_agent.main consultation.mp4 --no-subtitles
"""
import os
import sys
import json
import click
from tqdm import tqdm

from .core.analyzer import (
    get_video_info,
    detect_silence_ffmpeg,
    detect_low_motion,
    merge_cut_intervals,
)
from .core.salon_editor import build_salon_keep_intervals
from .core.transcriber import transcribe, remap_subtitle_times
from .utils.capcut_writer import create_capcut_project


@click.command()
@click.argument("video_path", type=click.Path(exists=True))
@click.option("--output-dir", "-o", default="./output", help="출력 폴더 경로")
@click.option("--project-name", "-p", default=None, help="프로젝트 이름 (기본: 파일명)")
@click.option(
    "--consult-end", type=float, default=None,
    help="상담 구간 종료 시각(초). 미지정 시 자동(30%)",
)
@click.option(
    "--process-end", type=float, default=None,
    help="시술 구간 종료 시각(초). 미지정 시 자동(70%)",
)
@click.option("--no-subtitles", is_flag=True, default=False, help="자막 생성 건너뛰기")
@click.option(
    "--whisper-model", default="base",
    type=click.Choice(["tiny", "base", "small", "medium"]),
    help="Whisper 모델 크기 (클수록 정확, 느림)",
)
@click.option(
    "--silence-db", default=-35.0, type=float,
    help="침묵 감지 임계값 dB (기본: -35)",
)
@click.option(
    "--silence-min", default=0.4, type=float,
    help="최소 침묵 길이(초) (기본: 0.4)",
)
@click.option(
    "--motion-threshold", default=1.5, type=float,
    help="저동작 감지 임계값 (낮을수록 민감, 기본: 1.5)",
)
def run(
    video_path, output_dir, project_name,
    consult_end, process_end,
    no_subtitles, whisper_model,
    silence_db, silence_min, motion_threshold,
):
    """미용실 쇼츠 자동 컷편집 + 자막 생성 → CapCut 프로젝트 파일 출력"""

    if project_name is None:
        project_name = os.path.splitext(os.path.basename(video_path))[0] + "_shorts"

    click.echo(f"\n📹  영상 분석 시작: {video_path}")

    # 1. 영상 정보 읽기
    click.echo("  ▸ 영상 정보 읽기...")
    info = get_video_info(video_path)
    duration = float(info["format"]["duration"])
    video_stream = next(
        (s for s in info["streams"] if s["codec_type"] == "video"), {}
    )
    width = video_stream.get("width", 1080)
    height = video_stream.get("height", 1920)
    click.echo(f"     길이: {duration:.1f}초  해상도: {width}x{height}")

    # 2. 침묵 구간 감지
    click.echo("  ▸ 침묵 구간 감지...")
    silences = detect_silence_ffmpeg(video_path, silence_db, silence_min)
    click.echo(f"     침묵 구간 {len(silences)}개 감지됨")

    # 3. 저동작 구간 감지
    click.echo("  ▸ 저동작(버벅임/잔동작) 구간 감지...")
    low_motion = detect_low_motion(
        video_path,
        motion_threshold=motion_threshold,
    )
    click.echo(f"     저동작 구간 {len(low_motion)}개 감지됨")

    # 4. 컷 구간 합산
    all_cuts = merge_cut_intervals(silences + low_motion)
    click.echo(f"  ▸ 총 컷 구간: {len(all_cuts)}개 ({sum(e-s for s,e in all_cuts):.1f}초 제거 예정)")

    # 5. 쇼츠 편집 로직 적용
    click.echo("  ▸ 미용실 쇼츠 구조 편집 적용 (상담/시술/완성)...")
    boundaries = None
    if consult_end is not None and process_end is not None:
        boundaries = (consult_end, process_end)

    keep_intervals = build_salon_keep_intervals(
        total_duration=duration,
        silence_cuts=silences,
        motion_cuts=low_motion,
        section_boundaries=boundaries,
    )
    total_kept = sum(e - s for s, e in keep_intervals)
    click.echo(f"     유지 구간: {len(keep_intervals)}개  편집 후 길이: {total_kept:.1f}초")

    # 6. 자막 생성
    subtitles = []
    if not no_subtitles:
        click.echo("  ▸ 자막 생성 중 (Whisper)... ⏳ 시간이 걸릴 수 있습니다")
        try:
            raw_subs = transcribe(video_path, language="ko", model_size=whisper_model)
            subtitles = remap_subtitle_times(raw_subs, keep_intervals)
            click.echo(f"     자막 {len(subtitles)}개 생성됨")
        except RuntimeError as e:
            click.echo(f"     ⚠ 자막 건너뜀: {e}")

    # 7. CapCut 프로젝트 파일 생성
    click.echo("  ▸ CapCut 프로젝트 파일 생성...")
    os.makedirs(output_dir, exist_ok=True)
    project_path = create_capcut_project(
        video_path=video_path,
        video_duration=duration,
        keep_intervals=keep_intervals,
        subtitles=subtitles,
        output_dir=output_dir,
        project_name=project_name,
        video_width=width,
        video_height=height,
    )

    click.echo(f"\n✅  완료!")
    click.echo(f"   프로젝트 폴더: {project_path}")
    click.echo(f"   draft_content.json  → 이 폴더를 CapCut 프로젝트 폴더에 복사하세요")
    click.echo(f"   cut_summary.txt     → 컷 내역 요약")
    click.echo()
    click.echo("📋  CapCut에서 여는 방법:")
    click.echo("   1. CapCut 앱 → 새 프로젝트 폴더 위치 확인")
    click.echo("      (Android: /storage/emulated/0/DCIM/CapCut/Projects/)")
    click.echo("      (iPhone:  Files > CapCut > Projects/)")
    click.echo("   2. 생성된 프로젝트 폴더를 해당 위치에 복사")
    click.echo("   3. CapCut 앱 재시작 → 프로젝트 목록에 나타남")


if __name__ == "__main__":
    run()
