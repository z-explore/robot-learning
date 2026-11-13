"""Chat-completions client used to rewrite a transcript."""

from __future__ import annotations

import json
from collections.abc import Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from voiceime.polish import system_prompt

Transport = Callable[[Request, float], bytes]


def _urllib_transport(request: Request, timeout: float) -> bytes:
    try:
        with urlopen(request, timeout=timeout) as response:
            return response.read()
    except HTTPError as error:
        raise RuntimeError(f"整理请求失败，HTTP {error.code}") from error
    except URLError as error:
        raise RuntimeError(f"整理请求失败：{error.reason}") from error


class ChatPolish:
    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        timeout: float = 60,
        transport: Transport | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.transport = transport or _urllib_transport

    def __call__(self, text: str, app: str | None) -> str:
        request = Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(
                {
                    "model": self.model,
                    "temperature": 0,
                    "messages": [
                        {"role": "system", "content": system_prompt(app)},
                        {"role": "user", "content": text},
                    ],
                }
            ).encode(),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        payload = json.loads(self.transport(request, self.timeout).decode("utf-8"))
        try:
            content = payload["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as error:
            raise RuntimeError("整理响应里没有正文") from error
        if not isinstance(content, str):
            raise RuntimeError("整理响应里没有正文")
        return content.strip()
