"""On-device speech to text with faster-whisper.

The model is OpenAI Whisper, which is public. Nothing here inspects Typeless.
"""

from __future__ import annotations

import os
from collections.abc import Callable
from pathlib import Path

ModelLoader = Callable[[str], object]


class LocalWhisper:
    def __init__(
        self,
        *,
        model_name: str = "base",
        language: str | None = None,
        loader: ModelLoader | None = None,
    ) -> None:
        self.model_name = model_name
        self.language = language or None
        self._loader = loader or _load_faster_whisper
        self._model: object | None = None

    def transcribe(self, audio_path: Path) -> str:
        path = Path(audio_path)
        if not path.is_file():
            raise FileNotFoundError(path)
        segments, _info = self._load().transcribe(
            str(path),
            language=self.language,
            beam_size=1,
            best_of=1,
            condition_on_previous_text=False,
        )
        return "".join(segment.text for segment in segments).strip()

    def _load(self) -> object:
        if self._model is None:
            self._model = self._loader(self.model_name)
        return self._model


def _load_faster_whisper(model_name: str) -> object:
    try:
        from faster_whisper import WhisperModel
    except ImportError as error:
        raise RuntimeError(
            "没有安装 faster-whisper。在本机执行 python3 -m pip install faster-whisper 后再试。"
        ) from error
    threads = _cpu_threads()
    os.environ["OMP_NUM_THREADS"] = str(threads)
    os.environ["MKL_NUM_THREADS"] = str(threads)
    return WhisperModel(
        model_name,
        device="cpu",
        compute_type="int8",
        cpu_threads=threads,
        num_workers=1,
    )


def _cpu_threads() -> int:
    raw = os.environ.get("VOICEIME_CPU_THREADS", "2")
    try:
        threads = int(raw)
    except ValueError:
        return 2
    return max(1, threads)
