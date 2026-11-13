# voiceime

Linux 上的语音转文字。`say` 用本机 Whisper 把一段录音变成文字，不调用大模型，也不分析 Typeless。

`morluto/rea` 只能查看本机已有程序的结构，里面没有语音识别模型。拆 Typeless 的安装包不能得到一个能听你说话的入口。这里直接用公开的 Whisper。

这台云端环境没有你的麦克风。命令要在你自己的 Ubuntu 上跑。先把光标放进对话输入框，再执行；文字会粘贴进去，你按下发送就能接着对话。没有桌面工具时，结果打印在终端里，复制过来即可。

## 语音转文字

```bash
cd voice-ime
python3 -m pip install faster-whisper
sudo apt install alsa-utils
python3 -m voiceime say --seconds 8 --inject auto
```

第一次运行会下载 `base` 模型。换成 `--model small` 中文更稳，体积也更大。已有音频文件时：

```bash
python3 -m voiceime say --file note.wav --inject stdout
```

## 可选的整理

```bash
export VOICEIME_ASR_API_KEY=...
export VOICEIME_LLM_API_KEY=...   # 不设置时只用本地规则去口头禅和改口

python3 -m voiceime run --engine local --seconds 8 --inject auto
python3 -m voiceime polish --local "嗯我想订周五，不对，改成下周一上午十点"
```

`--inject auto` 在 X11 上用 `xclip` 和 `xdotool`，在 Wayland 上用 `wl-copy` 和 `wtype`。没有这些工具时把结果打印出来。终端里加上 `--terminal`，粘贴键用 Ctrl+Shift+V。

录音需要 `arecord`（Ubuntu 软件包 `alsa-utils`）。Wayland 粘贴需要 `wl-clipboard` 和 `wtype`。

接口地址默认是 `https://api.openai.com/v1`，可以用 `VOICEIME_ASR_BASE_URL`、`VOICEIME_LLM_BASE_URL`、`VOICEIME_ASR_MODEL`、`VOICEIME_LLM_MODEL` 改成别的兼容服务。

`say` 的识别在本机完成，音频不会上传。`run` 在使用云端接口时才会把音频和原文发出去。命令结束前会删掉本次录音。不要用它口述密码或验证码。它不会在后台监听键盘。

## 测试

```bash
cd voice-ime
python3 -m unittest discover -s tests -v
```
