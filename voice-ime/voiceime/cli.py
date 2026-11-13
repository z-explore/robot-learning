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
from voiceime.local_asr import LocalWhisper
from voiceime.pipeline import dictate
from voiceime.polish import polish_text
from voiceime.record import record_wav


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="voiceime",
        description="把麦克风里的话转成文字。say 只做语音转文字。",
    )
    subcommands = parser.add_subparsers(dest="command", required=True)

    polish_command = subcommands.add_parser("polish", help="只整理一段已经转写的文字")
    polish_command.add_argument("text")
    _add_app(polish_command)
    polish_command.add_argument("--local", action="store_true", help="只用本地规则，不调用大模型")

    inject_command = subcommands.add_parser("inject", help="把给定文字写入当前输入框")
    inject_command.add_argument("text")
    _add_inject_flags(inject_command)

    say_command = subcommands.add_parser("say", help="语音转文字，不调用大模型整理")
    _add_source(say_command)
    _add_inject_flags(say_command)
    _add_local_asr(say_command)

    run_command = subcommands.add_parser("run", help="录音或读取音频，整理后写入")
    _add_source(run_command)
    _add_app(run_command)
    _add_inject_flags(run_command)
    _add_local_asr(run_command)
    run_command.add_argument("--engine", choices=("api", "local"), default="api")
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
        audio = _prepare_audio(args)
        temporary = audio if args.seconds is not None else None
        if args.command == "say":
            print("正在把录音转成文字，这时电脑会忙一会儿。", file=sys.stderr)
            text = LocalWhisper(model_name=args.model, language=args.language).transcribe(audio).strip()
            if not text:
                print("没有识别到文字。", file=sys.stderr)
                return 1
            inject_text(text, backend=args.inject, terminal=args.terminal)
            return 0
        raw, cleaned = dictate(
            audio,
            transcribe=_transcriber(args).transcribe,
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


def _prepare_audio(args: argparse.Namespace) -> Path:
    if args.file is not None:
        return args.file
    descriptor, name = tempfile.mkstemp(prefix="voiceime-", suffix=".wav")
    os.close(descriptor)
    path = Path(name)
    try:
        return record_wav(path, args.seconds)
    except Exception:
        path.unlink(missing_ok=True)
        raise


def _add_source(parser: argparse.ArgumentParser) -> None:
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--file", type=Path, help="已有的音频文件")
    source.add_argument("--seconds", type=float, help="用麦克风录制的秒数")


def _add_local_asr(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--model",
        default=os.environ.get("VOICEIME_LOCAL_MODEL", "base"),
        help="本机 Whisper 模型，默认 base",
    )
    parser.add_argument(
        "--language",
        default=os.environ.get("VOICEIME_LANGUAGE") or None,
        help="语言代码，例如 zh。省略时自动判断",
    )


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


def _transcriber(args: argparse.Namespace) -> WhisperAsr | LocalWhisper:
    if args.engine == "local":
        return LocalWhisper(model_name=args.model, language=args.language)
    api_key = os.environ.get("VOICEIME_ASR_API_KEY", "")
    if not api_key:
        raise RuntimeError("缺少 VOICEIME_ASR_API_KEY。只做本机转写时用 say，或给 run 加上 --engine local。")
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
