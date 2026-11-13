import io
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from urllib.request import Request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from voiceime.asr import WhisperAsr, encode_multipart
from voiceime.cli import main
from voiceime.inject import inject_text
from voiceime.local_asr import LocalWhisper
from voiceime.pipeline import dictate
from voiceime.polish import polish_locally, polish_text
from voiceime.record import record_wav


class PolishTests(unittest.TestCase):
    def test_keeps_the_wording_after_a_correction(self) -> None:
        raw = "嗯我想订周五，不对，改成下周一上午十点"
        self.assertEqual(polish_locally(raw), "改成下周一上午十点")

    def test_drops_a_repeated_sentence_and_leading_filler(self) -> None:
        raw = "那个，明天下午三点开会。明天下午三点开会。"
        self.assertEqual(polish_locally(raw), "明天下午三点开会。")

    def test_code_mode_keeps_spoken_identifiers(self) -> None:
        raw = "把 um 改成 user_id"
        self.assertEqual(polish_locally(raw, app="code"), raw)

    def test_llm_failure_uses_the_local_cleaner(self) -> None:
        def fail(text: str, app: str | None) -> str:
            raise RuntimeError("offline")

        self.assertEqual(polish_text("嗯，明天开会", llm=fail), "明天开会")


class PipelineTests(unittest.TestCase):
    def test_transcribe_then_polish_then_insert(self) -> None:
        inserted: list[str] = []

        raw, cleaned = dictate(
            Path("clip.wav"),
            transcribe=lambda path: "嗯，发布改到周三。不对，改到周四。",
            insert=inserted.append,
            llm=lambda text, app: "发布改到周四。",
        )

        self.assertEqual(raw, "嗯，发布改到周三。不对，改到周四。")
        self.assertEqual(cleaned, "发布改到周四。")
        self.assertEqual(inserted, ["发布改到周四。"])

    def test_empty_transcript_is_not_inserted(self) -> None:
        inserted: list[str] = []
        raw, cleaned = dictate(
            Path("clip.wav"),
            transcribe=lambda path: "   ",
            insert=inserted.append,
        )
        self.assertEqual((raw, cleaned, inserted), ("", "", []))


class AsrTests(unittest.TestCase):
    def test_posts_audio_to_the_transcription_endpoint(self) -> None:
        seen: list[Request] = []

        def transport(request: Request, timeout: float) -> bytes:
            seen.append(request)
            return '{"text":" 下周一开会 "}'.encode()

        with TemporaryDirectory() as directory:
            audio = Path(directory) / "note.wav"
            audio.write_bytes(b"RIFF")
            text = WhisperAsr(
                base_url="https://example.test/v1/",
                api_key="secret",
                transport=transport,
            ).transcribe(audio)

        self.assertEqual(text, "下周一开会")
        self.assertEqual(seen[0].full_url, "https://example.test/v1/audio/transcriptions")
        self.assertEqual(seen[0].get_header("Authorization"), "Bearer secret")
        body = seen[0].data
        assert isinstance(body, bytes)
        self.assertIn(b'name="model"', body)
        self.assertIn(b"whisper-1", body)
        self.assertIn(b'filename="note.wav"', body)
        self.assertNotIn(b"secret", body)

    def test_multipart_closes_the_boundary(self) -> None:
        body, content_type = encode_multipart(
            fields={"model": "whisper-1"},
            file_field="file",
            filename="note.wav",
            content=b"audio",
            content_type="audio/wav",
        )
        boundary = content_type.split("boundary=")[1]
        self.assertTrue(body.endswith(f"--{boundary}--\r\n".encode()))


class InjectTests(unittest.TestCase):
    def test_x11_pastes_with_ctrl_v_and_restores_the_clipboard(self) -> None:
        calls: list[tuple[tuple[str, ...], str | None]] = []

        def run(command: tuple[str, ...], text: str | None) -> subprocess.CompletedProcess[str]:
            calls.append((tuple(command), text))
            stdout = "previous" if command[-1] == "-o" else ""
            return subprocess.CompletedProcess(command, 0, stdout=stdout, stderr="")

        self.assertEqual(inject_text("周四开会", backend="x11", run=run), "周四开会")
        self.assertEqual(
            [command for command, _ in calls],
            [
                ("xclip", "-selection", "clipboard", "-o"),
                ("xclip", "-selection", "clipboard"),
                ("xdotool", "key", "--clearmodifiers", "ctrl+v"),
                ("xclip", "-selection", "clipboard"),
            ],
        )
        self.assertEqual(calls[1][1], "周四开会")
        self.assertEqual(calls[3][1], "previous")

    def test_terminal_uses_ctrl_shift_v(self) -> None:
        calls: list[tuple[str, ...]] = []

        def run(command: tuple[str, ...], text: str | None) -> subprocess.CompletedProcess[str]:
            calls.append(tuple(command))
            return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

        inject_text("周四开会", backend="x11", terminal=True, run=run)
        self.assertIn(("xdotool", "key", "--clearmodifiers", "ctrl+shift+v"), calls)

    def test_stdout_backend_prints_without_a_desktop_tool(self) -> None:
        output = io.StringIO()
        with patch("sys.stdout", output):
            inject_text("只打印", backend="stdout")
        self.assertEqual(output.getvalue(), "只打印\n")


class RecordTests(unittest.TestCase):
    def test_arecord_receives_whole_seconds(self) -> None:
        with TemporaryDirectory() as directory:
            destination = Path(directory) / "note.wav"
            with patch("voiceime.record.shutil.which", return_value="/usr/bin/arecord"):
                with patch("voiceime.record.subprocess.run") as run:
                    run.return_value = subprocess.CompletedProcess([], 0, "", "")
                    record_wav(destination, 8.0)
        command = run.call_args.args[0]
        self.assertEqual(command[command.index("-d") + 1], "8")


class LocalAsrTests(unittest.TestCase):
    def test_joins_whisper_segments(self) -> None:
        class Segment:
            def __init__(self, text: str) -> None:
                self.text = text

        class Model:
            def transcribe(self, path: str, language: str | None = None) -> tuple[list[Segment], None]:
                self.path = path
                self.language = language
                return [Segment("明天"), Segment("开会")], None

        model = Model()
        with TemporaryDirectory() as directory:
            audio = Path(directory) / "note.wav"
            audio.write_bytes(b"RIFF")
            text = LocalWhisper(model_name="base", language="zh", loader=lambda name: model).transcribe(audio)
        self.assertEqual(text, "明天开会")
        self.assertEqual(model.language, "zh")

    def test_missing_package_explains_how_to_install(self) -> None:
        real_import = __import__

        def fail_import(name: str, *args: object, **kwargs: object) -> object:
            if name == "faster_whisper":
                raise ImportError("missing")
            return real_import(name, *args, **kwargs)

        with TemporaryDirectory() as directory:
            audio = Path(directory) / "note.wav"
            audio.write_bytes(b"RIFF")
            with patch("builtins.__import__", fail_import):
                with self.assertRaises(RuntimeError) as raised:
                    LocalWhisper().transcribe(audio)
        self.assertIn("faster-whisper", str(raised.exception))


class CliTests(unittest.TestCase):
    def test_polish_command_uses_the_local_cleaner(self) -> None:
        output = io.StringIO()
        with patch("sys.stdout", output):
            status = main(["polish", "--local", "嗯，明天开会"])
        self.assertEqual(status, 0)
        self.assertEqual(output.getvalue(), "明天开会\n")

    def test_run_requires_an_api_key_before_reading_audio(self) -> None:
        with patch.dict("os.environ", {}, clear=True):
            with patch("sys.stderr") as stderr:
                written: list[str] = []
                stderr.write = written.append
                status = main(["run", "--file", "missing.wav", "--inject", "stdout"])
        self.assertEqual(status, 1)
        self.assertTrue(any("VOICEIME_ASR_API_KEY" in item for item in written))

    def test_say_prints_the_transcript_without_a_model_download(self) -> None:
        class Fake:
            def transcribe(self, path: Path) -> str:
                return "帮我看一下这段代码"

        output = io.StringIO()
        with patch("voiceime.cli.LocalWhisper", return_value=Fake()):
            with patch("sys.stdout", output):
                status = main(["say", "--file", "note.wav", "--inject", "stdout"])
        self.assertEqual(status, 0)
        self.assertEqual(output.getvalue(), "帮我看一下这段代码\n")


if __name__ == "__main__":
    unittest.main()
