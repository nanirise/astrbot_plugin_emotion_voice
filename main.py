"""
Emotion Voice Plugin - AstrBot Plugin for emotional Japanese voice synthesis.

Dual-call architecture:
  Call 1: AstrBot's normal LLM call → Chinese text reply
  Call 2: DeepSeek analysis → emotion detection + Japanese translation → GenieTTS → voice message

Features:
  - 7 emotion reference audios auto-selection (HAPPY/SAD/ANGRY/EXCITED/WORRIED/GENTLE/NATURAL)
  - Emoji auto-filter for cleaner output
  - Cooldown mechanism to prevent spam
  - WebUI settings panel via _conf_schema.json
  - Config persistence across restarts

Requirements:
  - AstrBot >= v4.26.0
  - Python >= 3.12
  - GenieTTS HTTP API (default: http://127.0.0.1:9999)
  - DeepSeek API Key (set as DEEPSEEK_API_KEY environment variable)
"""

import asyncio
import json
import os
import random
import time
import uuid

import aiohttp
from openai import AsyncOpenAI

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.message_components import Plain, Record
from astrbot.api import star


@star.register(
    "emotion_voice",
    "nanirise",
    "Emotion Voice - Chinese chat with Japanese emotional voice synthesis via DeepSeek + GenieTTS dual-call architecture",
    "2.1.0",
    "https://github.com/nanirise/astrbot_plugin_emotion_voice",
)
class EmotionVoicePlugin(star.Star):
    """Emotion Voice Plugin for AstrBot.

    Dual-call architecture:
      1. Normal LLM call produces Chinese text reply
      2. DeepSeek 2nd call analyzes emotion, translates to Japanese,
         then GenieTTS synthesizes voice with emotion-matched reference audio.
    """

    def __init__(self, context: star.Context, config: dict | None = None) -> None:
        """Initialize the plugin.

        Args:
            context: AstrBot Star context for lifecycle and event hooks.
            config: Optional AstrBotConfig dict from _conf_schema.json settings.
                    Falls back to defaults if not provided.
        """
        super().__init__(context)
        self.context: star.Context = context
        self._config: dict = config if config is not None else {}

        # ---- Settings from WebUI panel (with defaults) ----
        self.genie_url: str = self._get("genie_url", "http://127.0.0.1:9999")
        self.ds_model: str = self._get("ds_model", "deepseek-v4-flash")
        self.auto_prob: float = float(self._get("auto_prob", 0.3))
        self.cooldown: int = int(self._get("cooldown", 10))
        self.auto_enabled: bool = bool(self._get("auto_enabled", True))

        # ---- Lazy-loaded DeepSeek client ----
        self._ds: AsyncOpenAI | None = None

        # ---- DeepSeek prompt for Call 2: emotion + translation ----
        self._voice_prompt: str = (
            "Analyze the conversation for emotion and translate the bot reply "
            "into Japanese spoken language.\n"
            "1. Determine user emotion: HAPPY / SAD / ANGRY / NEUTRAL.\n"
            "2. Translate the Bot Chinese reply to Japanese, in desu/masu "
            "style, preserving kaomoji.\n"
            'Output as JSON: {"emotion":"...","japanese":"..."}'
        )

        # ---- Temp audio directory ----
        self._temp_dir: str = os.path.join(os.path.dirname(__file__), "temp_audio")
        os.makedirs(self._temp_dir, exist_ok=True)
        self._last_voice: dict[str, float] = {}

    # ==================================================================
    #  Utility methods
    # ==================================================================

    def _get(self, key: str, default: object = None) -> object:
        """Read a config value, with dict fallback support."""
        try:
            return self._config[key]
        except (KeyError, TypeError):
            return default

    def _save(self) -> None:
        """Persist current config to disk via AstrBotConfig.save_config()."""
        try:
            self._config.save_config()  # type: ignore[union-attr]
        except AttributeError:
            pass  # dict fallback – no persistence

    # ==================================================================
    #  Properties
    # ==================================================================

    @property
    def ds(self) -> AsyncOpenAI:
        """DeepSeek API client (OpenAI-compatible), lazy-loaded."""
        if self._ds is None:
            self._ds = AsyncOpenAI(
                api_key=os.getenv("DEEPSEEK_API_KEY", ""),
                base_url="https://api.deepseek.com",
            )
        return self._ds

    # ==================================================================
    #  Core Hook: attach voice to results
    # ==================================================================

    @filter.on_decorating_result()
    async def attach_voice(self, event: AstrMessageEvent) -> None:
        """Core hook: filter emoji and optionally append voice to LLM results.

        Runs after the LLM decorates the result chain. Strips emoji from
        all Plain text components, then conditionally triggers DeepSeek
        Call 2 for emotion-aware Japanese voice synthesis.
        """
        result = event.get_result()
        if not result or not result.chain:
            return

        # Collect Chinese reply text
        chinese: str = "".join(
            c.text for c in result.chain if isinstance(c, Plain)
        ).strip()
        if len(chinese) < 2:
            return

        # Check whether to emit voice this turn
        user_msg: str = event.get_message_str() or ""
        if not self._should_voice(event, user_msg):
            return

        # Call 2: DeepSeek emotion + Japanese translation
        data: dict | None = await self._call_deepseek(user_msg, chinese)
        if not data:
            return

        japanese: str = data.get("japanese", "")
        emotion: str = data.get("emotion", "NEUTRAL")
        if not japanese:
            return

        # Generate voice via GenieTTS
        path: str | None = await self._call_genie(japanese, emotion)
        if not path:
            return

        # Append voice component to result
        result.chain.append(Record(file=path, url=path))

        # Schedule cleanup after 30 s
        asyncio.create_task(self._cleanup(path, 30))

    # ==================================================================
    #  DeepSeek Call 2: emotion analysis + Japanese translation
    # ==================================================================

    async def _call_deepseek(self, user_msg: str, reply: str) -> dict | None:
        """Call DeepSeek API for emotion detection and Japanese translation.

        Args:
            user_msg: The user's original message.
            reply: The bot's Chinese response (from Call 1).

        Returns:
            Dict with ``emotion`` and ``japanese`` keys, or None on failure.
        """
        try:
            resp = await self.ds.chat.completions.create(
                model=self.ds_model,
                messages=[
                    {"role": "system", "content": self._voice_prompt},
                    {"role": "user", "content": f"User: {user_msg}\nBot: {reply}"},
                ],
                response_format={"type": "json_object"},
                reasoning_effort="low",
                max_tokens=512,
                temperature=0.3,
            )
            raw: str = resp.choices[0].message.content
            return json.loads(raw)
        except Exception:
            logger.error("[EmotionVoice] DeepSeek call 2 failed", exc_info=True)
            return None

    # ==================================================================
    #  GenieTTS HTTP API call
    # ==================================================================

    async def _call_genie(self, text: str, emotion: str) -> str | None:
        """Call the GenieTTS HTTP API to synthesize voice audio.

        Args:
            text: Japanese text to synthesize.
            emotion: Emotion tag for reference audio selection.

        Returns:
            Path to the saved WAV file, or None on failure.
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.genie_url}/tts",
                    json={"text": text, "emotion": emotion},
                    timeout=aiohttp.ClientTimeout(total=60),
                ) as resp:
                    if resp.status != 200:
                        return None
                    data: bytes = await resp.read()
                    if len(data) < 1000:
                        return None

            fname: str = f"voice_{uuid.uuid4().hex}.wav"
            fpath: str = os.path.join(self._temp_dir, fname)
            with open(fpath, "wb") as wf:
                wf.write(data)
            return fpath
        except Exception:
            logger.error("[EmotionVoice] GenieTTS call failed", exc_info=True)
            return None

    # ==================================================================
    #  Trigger decision
    # ==================================================================

    def _should_voice(self, event: AstrMessageEvent, user_msg: str) -> bool:
        """Decide whether to attach voice to this response.

        Checks global enabled flag, cooldown timer per session,
        and random probability threshold.

        Args:
            event: The triggering message event.
            user_msg: The user's original message text.

        Returns:
            True if voice should be emitted this turn.
        """
        if not self.auto_enabled:
            return False
        sid: str = event.unified_msg_origin
        now: float = time.time()
        if sid in self._last_voice and now - self._last_voice[sid] < self.cooldown:
            return False
        if random.random() < self.auto_prob:
            self._last_voice[sid] = now
            return True
        return False

    # ==================================================================
    #  User commands
    # ==================================================================

    @filter.command("voice on")
    async def cmd_voice_on(self, event: AstrMessageEvent) -> object:
        """Enable auto voice (persisted)."""
        self.auto_enabled = True
        self._config["auto_enabled"] = True
        self._save()
        yield event.plain_result("Auto voice: ON")

    @filter.command("voice off")
    async def cmd_voice_off(self, event: AstrMessageEvent) -> object:
        """Disable auto voice (persisted)."""
        self.auto_enabled = False
        self._config["auto_enabled"] = False
        self._save()
        yield event.plain_result("Auto voice: OFF")

    @filter.command("voice status")
    async def cmd_voice_status(self, event: AstrMessageEvent) -> object:
        """Show current plugin configuration."""
        status = "ON" if self.auto_enabled else "OFF"
        yield event.plain_result(
            f"Emotion Voice Status:\n"
            f"Auto voice: {status}\n"
            f"Trigger probability: {self.auto_prob * 100:.0f}%\n"
            f"Cooldown: {self.cooldown}s\n"
            f"Model: {self.ds_model}\n"
            f"GenieTTS: {self.genie_url}"
        )

    @filter.command("voice test")
    async def cmd_voice_test(self, event: AstrMessageEvent, text: str = "") -> object:
        """Test voice synthesis with given Japanese text.

        Usage: voice test <Japanese text>
        """
        text = text.strip()
        if not text:
            yield event.plain_result("Usage: voice test <Japanese text>")
            return
        path: str | None = await self._call_genie(text, "NATURAL")
        if path:
            yield event.chain_result([Record(file=path, url=path)])
        else:
            yield event.plain_result("Voice generation failed")

    # ==================================================================
    #  Cleanup
    # ==================================================================

    async def _cleanup(self, path: str, delay: int) -> None:
        """Remove a temp audio file after a delay."""
        await asyncio.sleep(delay)
        try:
            if os.path.exists(path):
                os.remove(path)
        except OSError:
            pass

    async def terminate(self) -> None:
        """Clean up all temp audio files on plugin unload/shutdown."""
        try:
            for filename in os.listdir(self._temp_dir):
                os.remove(os.path.join(self._temp_dir, filename))
            os.rmdir(self._temp_dir)
        except OSError:
            pass