"""ASR, then cleanup, then insert. Each stage is replaceable in tests."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from voiceime.polish import polish_text

Transcriber = Callable[[Path], str]
Inserter = Callable[[str], str]


def dictate(
    audio_path: Path,
    *,
    transcribe: Transcriber,
    insert: Inserter,
    app: str | None = None,
    llm: Callable[[str, str | None], str] | None = None,
) -> tuple[str, str]:
    raw = transcribe(Path(audio_path)).strip()
    cleaned = polish_text(raw, app=app, llm=llm)
    if cleaned:
        insert(cleaned)
    return raw, cleaned
