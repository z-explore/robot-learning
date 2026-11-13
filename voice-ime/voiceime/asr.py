"""Speech-to-text over an OpenAI-compatible transcription endpoint."""

from __future__ import annotations

import json
import mimetypes
import uuid
from collections.abc import Callable
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

Transport = Callable[[Request, float], bytes]


def _urllib_transport(request: Request, timeout: float) -> bytes:
    try:
        with urlopen(request, timeout=timeout) as response:
            return response.read()
    except HTTPError as error:
        raise RuntimeError(f"语音识别请求失败，HTTP {error.code}") from error
    except URLError as error:
        raise RuntimeError(f"语音识别请求失败：{error.reason}") from error


class WhisperAsr:
    """POST audio to ``{base_url}/audio/transcriptions``."""

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str = "whisper-1",
        timeout: float = 60,
        transport: Transport | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.transport = transport or _urllib_transport

    def transcribe(self, audio_path: Path) -> str:
        path = Path(audio_path)
        if not path.is_file():
            raise FileNotFoundError(path)
        body, content_type = encode_multipart(
            fields={"model": self.model},
            file_field="file",
            filename=path.name,
            content=path.read_bytes(),
            content_type=mimetypes.guess_type(path.name)[0] or "application/octet-stream",
        )
        request = Request(
            f"{self.base_url}/audio/transcriptions",
            data=body,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": content_type,
            },
            method="POST",
        )
        payload = json.loads(self.transport(request, self.timeout).decode("utf-8"))
        text = payload.get("text")
        if not isinstance(text, str):
            raise RuntimeError("语音识别响应里没有 text 字段")
        return text.strip()


def encode_multipart(
    *,
    fields: dict[str, str],
    file_field: str,
    filename: str,
    content: bytes,
    content_type: str,
) -> tuple[bytes, str]:
    boundary = f"----voiceime{uuid.uuid4().hex}"
    chunks: list[bytes] = []
    for name, value in fields.items():
        chunks.append(
            (
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="{name}"\r\n\r\n'
                f"{value}\r\n"
            ).encode()
        )
    chunks.append(
        (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="{file_field}"; filename="{filename}"\r\n'
            f"Content-Type: {content_type}\r\n\r\n"
        ).encode()
        + content
        + b"\r\n"
    )
    chunks.append(f"--{boundary}--\r\n".encode())
    return b"".join(chunks), f"multipart/form-data; boundary={boundary}"
