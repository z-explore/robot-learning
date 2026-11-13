"""Insert text into the focused window, or print it when no desktop is available.

This only runs when the user invokes the command. It does not watch the keyboard.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from collections.abc import Callable, Sequence

CommandRunner = Callable[[Sequence[str], str | None], subprocess.CompletedProcess[str]]


class InjectError(RuntimeError):
    pass


def default_runner(command: Sequence[str], text: str | None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(command),
        input=text,
        text=True,
        capture_output=True,
        check=False,
    )


def choose_backend() -> str:
    if os.environ.get("WAYLAND_DISPLAY") and _have("wl-copy", "wtype"):
        return "wayland"
    if os.environ.get("DISPLAY") and _have("xclip", "xdotool"):
        return "x11"
    return "stdout"


def inject_text(
    text: str,
    *,
    backend: str = "auto",
    terminal: bool = False,
    run: CommandRunner = default_runner,
) -> str:
    cleaned = text.strip()
    if not cleaned:
        return ""
    selected = choose_backend() if backend == "auto" else backend
    if selected == "stdout":
        print(cleaned)
        return cleaned
    if selected == "x11":
        _inject_x11(cleaned, terminal=terminal, run=run)
        return cleaned
    if selected == "wayland":
        _inject_wayland(cleaned, terminal=terminal, run=run)
        return cleaned
    raise InjectError(f"不认识的写入方式：{selected}")


def _inject_x11(text: str, *, terminal: bool, run: CommandRunner) -> None:
    previous = run(("xclip", "-selection", "clipboard", "-o"), None)
    saved = previous.stdout if previous.returncode == 0 else None
    copied = run(("xclip", "-selection", "clipboard"), text)
    if copied.returncode != 0:
        raise InjectError(copied.stderr.strip() or "无法写入剪贴板")
    shortcut = ("key", "--clearmodifiers", "ctrl+shift+v" if terminal else "ctrl+v")
    pasted = run(("xdotool", *shortcut), None)
    if saved is not None:
        run(("xclip", "-selection", "clipboard"), saved)
    if pasted.returncode != 0:
        raise InjectError(pasted.stderr.strip() or "无法把文字粘贴到当前窗口")


def _inject_wayland(text: str, *, terminal: bool, run: CommandRunner) -> None:
    previous = run(("wl-paste", "--no-newline"), None)
    saved = previous.stdout if previous.returncode == 0 else None
    copied = run(("wl-copy", "--"), text)
    if copied.returncode != 0:
        raise InjectError(copied.stderr.strip() or "无法写入剪贴板")
    keys = ("ctrl", "shift", "v") if terminal else ("ctrl", "v")
    sequence: list[str] = ["wtype"]
    for key in keys:
        sequence.extend(("-M", key) if key != "v" else ("-k", key))
    for key in reversed(keys[:-1]):
        sequence.extend(("-m", key))
    pasted = run(tuple(sequence), None)
    if saved is not None:
        run(("wl-copy", "--"), saved)
    if pasted.returncode != 0:
        raise InjectError(pasted.stderr.strip() or "无法把文字粘贴到当前窗口")


def _have(*commands: str) -> bool:
    return all(shutil.which(command) for command in commands)
