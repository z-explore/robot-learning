"""Command line for the Linux voice input tool."""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
from pathlib import Path

from voiceime.asr import WhisperAsr
from voiceime.inject import InjectError, choose_backend, inject_text
from voiceime.llm import ChatPolish
from voiceime.pipeline import dictate
from voiceime.polish import polish_text
from voiceime.record import record_wav


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="voiceime",
        description="录音数秒：语音识别，大模型整理，再写入当前输入框。",
    )
    subcommands = parser.add_subparsers(dest="command", required=True)

    polish_command = subcommands.add_parser("polish", help="只整理一段已经转写的文字")
    polish_command.add_argument("text")
    _add_app(polish_command)
    polish_command.add_argument("--local", action="store_true", help="只用本地规则，不调用大模型")

    inject_command = subcommands.add_parser("inject", help="把给定文字写入当前输入框")
    inject_command.add_argument("text")
    _add_inject_flags(inject_command)

    run_command = subcommands.add_parser("run", help="录音或读取音频，整理后写入")
    source = run_command.add_mutually_exclusive_group(required=True)
    source.add_argument("--file", type=Path, help="已有的音频文件")
    source.add_argument("--seconds", type=float, help="用麦克风录制的秒数")
    _add_app(run_command)
    _add_inject_flags(run_command)
    run_command.add_argument("--local", action="store_true", help="只用本地规则整理")

    args = parser.parse_args(argv)
    temporary: Path | None = None
    try:
        if args.command == "polish":
            print(polish_text(args.text, app=args.app, llm=None if args.local else _llm_client()))
            return 0
        if args.command == "inject":
            inject_text(args.text, backend=args.inject, terminal=args.terminal)
            return 0
        audio = args.file
        if args.seconds is not None:
            descriptor, name = tempfile.mkstemp(prefix="voiceime-", suffix=".wav")
            os.close(descriptor)
            temporary = Path(name)
            audio = record_wav(temporary, args.seconds)
        assert audio is not None
        raw, cleaned = dictate(
            audio,
            transcribe=_transcriber().transcribe,
            insert=lambda text: inject_text(text, backend=args.inject, terminal=args.terminal),
            app=args.app,
            llm=None if args.local else _llm_client(),
        )
        if not cleaned:
            print("没有识别到文字。", file=sys.stderr)
            return 1
        selected = args.inject if args.inject != "auto" else choose_backend()
        if selected != "stdout":
            print(f"原文：{raw}\n整理：{cleaned}", file=sys.stderr)
        return 0
    except (InjectError, RuntimeError, FileNotFoundError, ValueError, OSError) as error:
        print(str(error), file=sys.stderr)
        return 1
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _add_app(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--app", choices=("mail", "slack", "notes", "code"), default=None)


def _add_inject_flags(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--inject",
        choices=("auto", "stdout", "x11", "wayland"),
        default="auto",
        help="写入方式。auto 在有桌面时粘贴到当前窗口，否则打印。",
    )
    parser.add_argument("--terminal", action="store_true", help="终端里用 Ctrl+Shift+V 粘贴")


def _transcriber() -> WhisperAsr:
    api_key = os.environ.get("VOICEIME_ASR_API_KEY", "")
    if not api_key:
        raise RuntimeError("缺少 VOICEIME_ASR_API_KEY。识别走你自己的 Whisper 兼容接口。")
    return WhisperAsr(
        base_url=os.environ.get("VOICEIME_ASR_BASE_URL", "https://api.openai.com/v1"),
        api_key=api_key,
        model=os.environ.get("VOICEIME_ASR_MODEL", "whisper-1"),
    )


def _llm_client() -> ChatPolish | None:
    api_key = os.environ.get("VOICEIME_LLM_API_KEY", "")
    if not api_key:
        return None
    return ChatPolish(
        base_url=os.environ.get("VOICEIME_LLM_BASE_URL", "https://api.openai.com/v1"),
        api_key=api_key,
        model=os.environ.get("VOICEIME_LLM_MODEL", "gpt-4o-mini"),
    )


if __name__ == "__main__":
    raise SystemExit(main())
