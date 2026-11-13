"""Turn a raw transcript into the sentence the speaker meant.

The local cleaner is deterministic and does not call a network. When an LLM
client is configured, it does the same job with a stricter prompt and falls
back to the local cleaner if the request fails.
"""

from __future__ import annotations

import re
from collections.abc import Callable

CORRECTION_MARKERS = (
    "scratch that",
    "i mean",
    "重新说",
    "我是说",
    "应该是",
    "不对",
)

LEADING_FILLER = re.compile(
    r"^(?:嗯+|啊+|呃+|那个|就是说|um+|uh+|you know)[，,\s]*",
    re.IGNORECASE,
)
SURROUNDED_FILLER = re.compile(
    r"([\s，,。！？!?\n])(?:嗯+|啊+|呃+|那个|就是说|um+|uh+|you know)(?=[\s，,。！？!?\n]|$)",
    re.IGNORECASE,
)

SENTENCE_SPLIT = re.compile(r"(?<=[。！？!?])\s*|\n+")

APP_HINTS = {
    "mail": "语气正式，适合邮件。",
    "slack": "语气简短，适合聊天。",
    "notes": "整理成清楚的笔记。",
    "code": "保留原话、标识符和术语，不要改写成散文。",
}


def polish_locally(text: str, *, app: str | None = None) -> str:
    """Remove fillers, repeated sentences, and wording the speaker replaced."""
    cleaned = text.replace("\r\n", "\n").strip()
    if not cleaned:
        return ""
    cleaned = _keep_final_intent(cleaned)
    if app != "code":
        cleaned = _remove_fillers(cleaned)
    cleaned = _drop_repeated_sentences(cleaned)
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
    cleaned = re.sub(r"\s+([，,。！？!?])", r"\1", cleaned)
    cleaned = re.sub(r"^[，,\s]+", "", cleaned)
    return cleaned.strip()


def _remove_fillers(text: str) -> str:
    previous = None
    while previous != text:
        previous = text
        text = LEADING_FILLER.sub("", text)
        text = SURROUNDED_FILLER.sub(r"\1", text)
    return text


def _keep_final_intent(text: str) -> str:
    lowered = text.lower()
    cut_at = -1
    marker_length = 0
    for marker in CORRECTION_MARKERS:
        index = lowered.rfind(marker.lower())
        if index > cut_at:
            cut_at = index
            marker_length = len(marker)
    if cut_at < 0:
        return text
    remainder = text[cut_at + marker_length :]
    return remainder.lstrip(" ，,。:：")


def _drop_repeated_sentences(text: str) -> str:
    parts = [part.strip() for part in SENTENCE_SPLIT.split(text) if part.strip()]
    if len(parts) < 2:
        return text
    kept: list[str] = []
    for part in parts:
        if kept and kept[-1].rstrip("。！？!?") == part.rstrip("。！？!?"):
            continue
        kept.append(part)
    if len(kept) == len(parts):
        return text
    return "".join(part if part[-1] in "。！？!?" else part + "。" for part in kept)


LlmClient = Callable[[str, str | None], str]


def polish_text(text: str, *, app: str | None = None, llm: LlmClient | None = None) -> str:
    """Prefer the configured model, and keep the local result when it fails."""
    local = polish_locally(text, app=app)
    if llm is None or not text.strip():
        return local
    try:
        rewritten = llm(text, app).strip()
    except Exception:
        return local
    return rewritten or local


def system_prompt(app: str | None) -> str:
    hint = APP_HINTS.get(app or "", "语气自然。")
    return (
        "你是语音听写整理器。只输出整理后的正文，不要解释，不要加引号。\n"
        "删掉口头禅（嗯、啊、呃、那个）和紧挨着的重复句。\n"
        "说话人中途改口时，只保留最后想表达的内容。\n"
        "分点口述时整理成列表。\n"
        f"{hint}"
    )
