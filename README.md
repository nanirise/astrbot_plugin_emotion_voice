# Emotion Voice - AstrBot Plugin

[![Version](https://img.shields.io/badge/version-2.1.0-blue)](https://github.com/nanirise/astrbot_plugin_emotion_voice)
[![AstrBot](https://img.shields.io/badge/astrbot->=4.26.0b1-green)](https://github.com/AstrBotDevs/AstrBot)
[![License](https://img.shields.io/badge/license-AGPL--3.0-orange)](./LICENSE)

Chinese chat + Japanese emotional voice synthesis, powered by GenieTTS with 7 emotion-tracking reference audios. Works with any OpenAI-compatible LLM (DeepSeek, OpenAI, SiliconFlow, etc).

中文聊天 + 日语情感语音合成，基于 GenieTTS 和 7 种情感参考音频。支持任意兼容 OpenAI 格式的大模型。**当语音触发时，中文原文会与日语语音一同发送，一条消息即可看到文字 + 听到语音。**

---

## Architecture

```
User message → AstrBot → LLM Call 1 → Chinese text reply (instant)
                            ↓
(trigger: voice on / auto-probability)
                            ↓
                      LLM Call 2
                      ├─ emotion analysis → select reference audio
                      └─ Chinese → Japanese translation
                            ↓
                      GenieTTS
                      ├─ reference audio (emotion-matched)
                      └─ Japanese text
                            ↓
                      QQ: Chinese text + Japanese voice (one message)
```

**When voice triggers, the Chinese reply text is sent alongside the Japanese voice in a single message.**

---

## Features

- **Dual-call architecture** — text responds instantly, voice generates separately
- **Voice + text in one message** — Chinese reply is included with the Japanese voice
- **7 emotion reference audios** — HAPPY / SAD / ANGRY / EXCITED / WORRIED / GENTLE / NATURAL
- **LLM-agnostic** — any OpenAI-compatible provider (DeepSeek, OpenAI, SiliconFlow, Qwen, etc.)
- **WebUI settings panel** — `_conf_schema.json` with real-time config changes
- **Cooldown + probability** — prevent voice spam
- **Config persistence** — settings survive reboots

## Requirements

- AstrBot >= v4.26.0
- Python >= 3.12
- GenieTTS HTTP API (default: `http://127.0.0.1:9999`)
- Any OpenAI-compatible LLM provider configured in AstrBot
- LLM API key set as env var (`DEEPSEEK_API_KEY` for DeepSeek, `OPENAI_API_KEY` for OpenAI, etc.)

## Installation

```bash
# Place plugin in AstrBot plugin directory
cp -r emotion_voice /opt/qq-bot/astrbot/data/plugins/

# Set your API key
echo 'DEEPSEEK_API_KEY=sk-xxx' >> /etc/systemd/system/astrbot.service

# Restart AstrBot
systemctl restart astrbot
```

## Commands

| Command | Description |
|---------|-------------|
| `voice on` | Enable auto voice (persisted across restarts) |
| `voice off` | Disable auto voice (persisted across restarts) |
| `voice status` | Show current config: probability, cooldown, model, GenieTTS URL |
| `voice test <Japanese>` | Test voice synthesis with given Japanese text |

## Configuration

Path: **WebUI → Plugins → emotion_voice → Settings**

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| GenieTTS URL | string | `http://127.0.0.1:9999` | GenieTTS HTTP API address |
| LLM Model | select | `deepseek-v4-flash` | Model for Call 2 (emotion + translation) |
| Auto Probability | float | `0.30` | Probability of auto voice per reply (0.0–1.0) |
| Cooldown | int | `10` | Minimum seconds between voice messages |
| Enable Auto Voice | bool | `true` | Global on/off switch |

All changes take effect immediately and persist across restarts.

## GenieTTS Setup

Requires a GenieTTS HTTP API at the configured URL:

```bash
POST /tts
Content-Type: application/json

{"text": "日本語テキスト", "emotion": "HAPPY"}

# Response: WAV audio file
```

Reference audios should use the naming format `【EMOTION】reference_text.wav`.

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Voice not triggering | Check `voice status` — auto may be off or probability too low |
| GenieTTS connection failed | Verify: `curl http://127.0.0.1:9999/health` |
| API key error | Ensure `DEEPSEEK_API_KEY` (or your provider's equivalent) is set in systemd env |
| Voice test works but auto doesn't | Increase `auto_prob` or check cooldown hasn't elapsed |
| Using a different LLM | Change model in settings panel — any OpenAI-compatible model works |

## License

AGPL-3.0 (compatible with the AstrBot framework)