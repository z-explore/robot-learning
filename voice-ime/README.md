# voiceime

Linux 上的语音输入小工具。按一次录音：语音识别，大模型整理，再把文字粘贴进当前输入框。

`morluto/rea` 是本地逆向分析工具，仓库里没有语音识别、文本整理或输入框写入。这版不调用 REA，也不分析 Typeless 的程序。链路是公开的三步：Whisper 兼容接口、聊天补全接口、剪贴板粘贴。

## 用法

```bash
cd voice-ime
export VOICEIME_ASR_API_KEY=...
export VOICEIME_LLM_API_KEY=...   # 不设置时只用本地规则去口头禅和改口

python3 -m voiceime run --seconds 8 --inject auto
python3 -m voiceime run --file note.wav --app mail --inject auto
python3 -m voiceime polish --local "嗯我想订周五，不对，改成下周一上午十点"
```

`--inject auto` 在 X11 上用 `xclip` 和 `xdotool`，在 Wayland 上用 `wl-copy` 和 `wtype`。没有这些工具时把结果打印出来。终端里加上 `--terminal`，粘贴键用 Ctrl+Shift+V。

录音需要 `arecord`（Ubuntu 软件包 `alsa-utils`）。Wayland 粘贴需要 `wl-clipboard` 和 `wtype`。

接口地址默认是 `https://api.openai.com/v1`，可以用 `VOICEIME_ASR_BASE_URL`、`VOICEIME_LLM_BASE_URL`、`VOICEIME_ASR_MODEL`、`VOICEIME_LLM_MODEL` 改成别的兼容服务。

音频和原文会发到你配置的接口。命令结束前会删掉本次录音。不要用它口述密码或验证码。它不会在后台监听键盘。

## 测试

```bash
cd voice-ime
python3 -m unittest discover -s tests -v
```
