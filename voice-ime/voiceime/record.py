"""Record a short microphone clip with arecord."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


def record_wav(path: Path, seconds: float) -> Path:
    if seconds <= 0:
        raise ValueError("录音时长必须大于 0")
    duration = int(round(seconds))
    if duration < 1:
        raise ValueError("录音时长至少 1 秒")
    if shutil.which("arecord") is None:
        raise RuntimeError("没有找到 arecord。Ubuntu 上可以安装 alsa-utils。")
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(
        [
            "arecord",
            "-q",
            "-f",
            "S16_LE",
            "-r",
            "16000",
            "-c",
            "1",
            "-d",
            str(duration),
            str(destination),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or "arecord 录音失败"
        raise RuntimeError(detail)
    return destination
