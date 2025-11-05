from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path
from typing import Iterable

from genesis.config import get_settings


def _run_ffmpeg(args: list[str]) -> None:
    settings = get_settings()
    cmd = [settings.ffmpeg_binary, *args]
    completed = subprocess.run(cmd, capture_output=True, text=True)
    if completed.returncode != 0:
        raise RuntimeError(
            f"ffmpeg command failed: {' '.join(cmd)}\nstdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
        )


def extract_scene_frame(video_path: Path, timestamp_seconds: float, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    args = [
        "-y",
        "-ss",
        f"{timestamp_seconds:.3f}",
        "-i",
        str(video_path),
        "-frames:v",
        "1",
        "-q:v",
        "2",
        str(output_path),
    ]
    _run_ffmpeg(args)


def trim_segment(video_path: Path, start_seconds: float, end_seconds: float, output_path: Path) -> None:
    duration = max(end_seconds - start_seconds, 0.1)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    args = [
        "-y",
        "-ss",
        f"{start_seconds:.3f}",
        "-i",
        str(video_path),
        "-t",
        f"{duration:.3f}",
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-crf",
        "20",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        str(output_path),
    ]
    _run_ffmpeg(args)


def render_concatenation(segments: Iterable[Path], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as concat_file:
        for segment in segments:
            concat_file.write(f"file '{segment.resolve().as_posix()}'\n")
        concat_file_path = Path(concat_file.name)

    args = [
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(concat_file_path),
        "-c",
        "copy",
        str(output_path),
    ]
    try:
        _run_ffmpeg(args)
    finally:
        concat_file_path.unlink(missing_ok=True)


def convert_audio_to_wav(input_path: Path, output_path: Path, sample_rate: int = 48000) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    args = [
        "-y",
        "-i",
        str(input_path),
        "-ar",
        str(sample_rate),
        "-ac",
        "2",
        str(output_path),
    ]
    _run_ffmpeg(args)


def mix_voiceover(
    base_video: Path,
    voiceover_wav: Path,
    output_path: Path,
    *,
    offset_seconds: float = 0.0,
    voiceover_gain: float = 1.0,
    bed_gain: float = 0.3,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    offset_ms = max(int(offset_seconds * 1000), 0)

    filter_complex = (
        f"[0:a]volume={bed_gain}[bg];"
        f"[1:a]adelay={offset_ms}|{offset_ms},volume={voiceover_gain}[vo];"
        "[bg][vo]amix=inputs=2:duration=first:dropout_transition=2[aout]"
    )

    args = [
        "-y",
        "-i",
        str(base_video),
        "-i",
        str(voiceover_wav),
        "-filter_complex",
        filter_complex,
        "-map",
        "0:v",
        "-map",
        "[aout]",
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        str(output_path),
    ]
    _run_ffmpeg(args)
