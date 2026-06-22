# Emotion Voice - AstrBot Plugin / 情感语音插件

[![Version](https://img.shields.io/badge/version-2.1.0-blue)](https://github.com/nanirise/astrbot_plugin_emotion_voice)
[![AstrBot](https://img.shields.io/badge/astrbot-%3E%3D4.26.0b1-green)](https://github.com/AstrBotDevs/AstrBot)
[![License](https://img.shields.io/badge/license-AGPL--3.0-orange)](./LICENSE)

[English](#english) | [中文](#中文)

---

## English

Chinese chat + Japanese emotional voice synthesis, powered by GenieTTS with 7 emotion-tracking reference audios. Works with any OpenAI-compatible LLM (DeepSeek, OpenAI, SiliconFlow, etc).

### Architecture

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

### Features

- **Dual-call architecture** — text responds instantly, voice generates separately
- **Voice + text in one message** — Chinese reply is included with the Japanese voice
- **7 emotion reference audios** — HAPPY / SAD / ANGRY / EXCITED / WORRIED / GENTLE / NATURAL
- **LLM-agnostic** — any OpenAI-compatible provider (DeepSeek, OpenAI, SiliconFlow, Qwen, etc.)
- **WebUI settings panel** — `_conf_schema.json` with real-time config changes
- **Cooldown + probability** — prevent voice spam
- **Config persistence** — settings survive reboots

### Requirements

- AstrBot >= v4.26.0
- Python >= 3.12
- GenieTTS HTTP API (default: `http://127.0.0.1:9999`)
- Any OpenAI-compatible LLM provider configured in AstrBot
- LLM API key set as env var (`OPENAI_API_KEY`)

### Installation

```bash
# Place plugin in AstrBot plugin directory
cp -r emotion_voice /opt/qq-bot/astrbot/data/plugins/

# Set your API key
echo 'OPENAI_API_KEY=sk-xxx' >> /etc/systemd/system/astrbot.service

# Restart AstrBot
systemctl restart astrbot
```

### Commands

| Command | Description |
|---------|-------------|
| `voice on` | Enable auto voice (persisted across restarts) |
| `voice off` | Disable auto voice (persisted across restarts) |
| `voice status` | Show current config: probability, cooldown, model, GenieTTS URL |
| `voice test <Japanese>` | Test voice synthesis with given Japanese text |

### Configuration

Path: **WebUI → Plugins → emotion_voice → Settings**

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| GenieTTS URL | string | `http://127.0.0.1:9999` | GenieTTS HTTP API address |
| LLM Model | select | `deepseek-v4-flash` | Model for Call 2 (emotion + translation) |
| Auto Probability | float | `0.30` | Probability of auto voice per reply (0.0–1.0) |
| Cooldown | int | `10` | Minimum seconds between voice messages |
| Enable Auto Voice | bool | `true` | Global on/off switch |

All changes take effect immediately and persist across restarts.

### GenieTTS Setup

Requires a GenieTTS HTTP API at the configured URL:

```bash
POST /tts
Content-Type: application/json

{"text": "日本語テキスト", "emotion": "HAPPY"}

# Response: WAV audio file
```

Reference audios should use the naming format `【EMOTION】reference_text.wav`.

### Troubleshooting

| Problem | Solution |
|---------|----------|
| Voice not triggering | Check `voice status` — auto may be off or probability too low |
| GenieTTS connection failed | Verify: `curl http://127.0.0.1:9999/health` |
| API key error | Ensure `OPENAI_API_KEY` is set in systemd env for plugin Call 2 |
| Voice test works but auto doesn't | Increase `auto_prob` or check cooldown hasn't elapsed |
| Using a different LLM | Change model in settings panel — any OpenAI-compatible model works |

---

## 中文

中文聊天 + 日语情感语音合成，基于 GenieTTS 和 7 种情感参考音频。支持任意兼容 OpenAI 格式的大模型。**当语音触发时，中文原文会与日语语音一同发送。**

### 架构

```
用户消息 → AstrBot → LLM 调用① → 中文文字回复（即时送达）
                            ↓
（触发条件: voice on / 自动概率）
                            ↓
                      LLM 调用②
                      ├─ 分析用户情感 → 选择匹配的参考音频
                      └─ 中文回复 → 日语翻译
                            ↓
                      GenieTTS
                      ├─ 参考音频（情感匹配）
                      └─ 日语文本
                            ↓
                      QQ: 中文文字 + 日语语音（一条消息）
```

**语音触发时，中文原文与日语语音在同一条消息中发送。**

### 功能

- **双调用架构** — 文字即时回复，语音独立生成
- **语音 + 文字同条发送** — 中文回复与日语语音在一条消息中
- **7 种情感参考音频** — HAPPY / SAD / ANGRY / EXCITED / WORRIED / GENTLE / NATURAL
- **不限定大模型** — 任意兼容 OpenAI 格式的提供商均可使用（DeepSeek、OpenAI、SiliconFlow、Qwen 等）
- **WebUI 设置面板** — 通过 `_conf_schema.json` 实现，实时修改无需编辑代码
- **冷却 + 概率机制** — 防止语音刷屏
- **配置持久化** — 重启后设置不丢失

### 依赖

- AstrBot >= v4.26.0
- Python >= 3.12
- GenieTTS HTTP API（默认: `http://127.0.0.1:9999`）
- AstrBot 中已配置任意兼容 OpenAI 格式的 LLM 提供商
- LLM API Key 设为环境变量 (`OPENAI_API_KEY`)

### 安装

```bash
# 将插件放入 AstrBot 插件目录
cp -r emotion_voice /opt/qq-bot/astrbot/data/plugins/

# 设置 API Key
echo 'OPENAI_API_KEY=sk-xxx' >> /etc/systemd/system/astrbot.service

# 重启 AstrBot
systemctl restart astrbot
```

### 指令

| 指令 | 说明 |
|------|------|
| `voice on` | 开启自动语音（重启后保持） |
| `voice off` | 关闭自动语音（重启后保持） |
| `voice status` | 查看当前配置：概率、冷却、模型、GenieTTS 地址 |
| `voice test <日语文本>` | 测试语音合成 |

### 配置

路径: **WebUI → 插件 → emotion_voice → 设置**

| 设置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| GenieTTS 地址 | string | `http://127.0.0.1:9999` | GenieTTS HTTP API 地址 |
| LLM 模型 | select | `deepseek-v4-flash` | 调用② 使用的模型（情感分析 + 翻译） |
| 自动语音概率 | float | `0.30` | 每次回复触发语音的概率（0.0–1.0） |
| 冷却时间 | int | `10` | 同一会话两次语音的最小间隔（秒） |
| 启用自动语音 | bool | `true` | 全局开关 |

所有修改即时生效，重启后保持。

### GenieTTS 部署

需要在配置的 URL 上运行 GenieTTS HTTP API：

```bash
POST /tts
Content-Type: application/json

{"text": "日本語テキスト", "emotion": "HAPPY"}

# Response: WAV audio file
```

参考音频命名格式: `【情感】参考文本.wav`

### 常见问题

| 问题 | 解决方案 |
|------|----------|
| 语音不触发 | 检查 `voice status` — 可能自动语音已关闭或概率太低 |
| GenieTTS 连接失败 | 验证: `curl http://127.0.0.1:9999/health` |
| API Key 错误 | 确保 `OPENAI_API_KEY` 已设置在 systemd env 中，供插件调用②使用 |
| voice test 能用于自动不行 | 提高 `auto_prob` 或检查冷却时间是否未过 |
| 换用其他大模型 | 在设置面板中修改模型名 — 任何兼容 OpenAI 格式的模型均可 |

## License / 许可

AGPL-3.0 (与 AstrBot 框架协议一致)