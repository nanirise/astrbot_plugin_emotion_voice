# Emotion Voice - AstrBot 情感语音插件

中文文字聊天 + 日语情感语音，基于 DeepSeek V4 + GenieTTS 双调用架构。

## 工作流程

```
用户消息 → AstrBot → LLM 调用① → 中文文字回复
                           ↓
                     DeepSeek 调用②
                     ├─ 分析用户情感 → 选择参考音频
                     └─ 翻译中文→日语
                           ↓
                     GenieTTS
                     ├─ 参考音频 (情感)
                     └─ 日语文本
                           ↓
                     QQ 语音消息
```

## 依赖

- AstrBot >= v4.26.0
- Python >= 3.12
- GenieTTS HTTP API (`http://127.0.0.1:9999`)
- DeepSeek API Key (环境变量 `DEEPSEEK_API_KEY`)

## 安装

```bash
# 放到 AstrBot 插件目录
cp -r emotion_voice /opt/qq-bot/astrbot/data/plugins/

# 设置 API Key
echo 'DEEPSEEK_API_KEY=sk-xxx' >> /etc/systemd/system/astrbot.service

# 重启 AstrBot
systemctl restart astrbot
```

## 设置页面

在 AstrBot WebUI 管理面板中直接配置，无需编辑代码：

| 设置项 | 说明 | 默认值 |
|--------|------|--------|
| GenieTTS 地址 | GenieTTS HTTP API 地址 | `http://127.0.0.1:9999` |
| DeepSeek 模型 | 调用②使用的模型 | `deepseek-v4-flash` |
| 自动语音概率 | 每次回复合成语音的概率 | `0.30` |
| 冷却时间 | 同一会话两次语音间隔 | `10s` |
| 启用自动语音 | 全局开关 | `true` |

路径：**WebUI → 插件 → emotion_voice → 设置**

## 指令

| 指令 | 说明 |
|------|------|
| `voice on` | 开启自动语音（持久化） |
| `voice off` | 关闭自动语音（持久化） |
| `voice status` | 查看当前配置状态 |
| `voice test <日语>` | 测试语音合成 |

## 触发逻辑

- 通过 `voice on/off` 全局开关控制
- 自动语音按 `auto_prob` 概率触发
- 同一会话在 `cooldown` 秒内不重复
- WebUI 设置页实时修改所有参数

## GenieTTS API

```bash
POST /tts
Content-Type: application/json

{
  "text": "日本語テキスト",
  "emotion": "HAPPY"
}

# 返回: WAV 音频文件
```

## 情感参考音频

插件根据 DeepSeek 分析结果自动选择对应情感的参考音频：

```
genie-tts/references/
├── 【ANGRY】*.wav
├── 【EXCITED】*.wav
├── 【GENTLE】*.wav
├── 【HAPPY】*.wav
├── 【NATURAL】*.wav
├── 【SAD】*.wav
└── 【WORRIED】*.wav
```

## 临时文件

音频文件保存在 `temp_audio/`，发送后 30 秒自动清理。
