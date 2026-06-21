import asyncio
import hashlib
import json
import logging
from dataclasses import dataclass

from app.delivery.telegram.telegram_app import TelegramApp
from app.delivery.telegram.telegram_service import TelegramService
from app.core.config import settings
from app.core.encryption import decrypt_value


logger = logging.getLogger(__name__)


@dataclass
class RunningTelegramBot:
    app: TelegramApp
    fingerprint: str


class TelegramAppsManager:
    """Run and reconcile Telegram bot apps with DB state."""

    def __init__(self, check_interval_seconds: int = 60):
        self.check_interval = check_interval_seconds
        self._service = TelegramService()
        self._running: dict[int, RunningTelegramBot] = {}
        self._active = False

    @staticmethod
    def _fingerprint_bot(bot: dict) -> str:
        payload = {
            "id": bot.get("id"),
            "bot_token": bot.get("bot_token"),
            "is_active": bot.get("is_active"),
        }
        serialized = json.dumps(payload, sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    async def _start_bot(self, bot: dict, fingerprint: str) -> None:
        bot_id = bot["id"]
        encrypted_token = bot.get("bot_token")
        if not encrypted_token:
            raise ValueError(f"Missing bot token for bot_id={bot_id}")

        app = TelegramApp(
            bot_token=decrypt_value(
                encrypted_token,
                settings.ENCRYPTION_KEY,
            )
        )
        await app.start()
        self._running[bot_id] = RunningTelegramBot(
            app=app,
            fingerprint=fingerprint,
        )
        logger.info("Started Telegram app bot_id=%s", bot_id)

    async def _stop_bot(self, bot_id: int) -> None:
        running_bot = self._running.get(bot_id)
        if not running_bot:
            return
        await running_bot.app.stop()
        del self._running[bot_id]
        logger.info("Stopped Telegram app bot_id=%s", bot_id)

    async def _restart_bot(self, bot: dict, fingerprint: str) -> None:
        bot_id = bot["id"]
        await self._stop_bot(bot_id)
        await self._start_bot(bot, fingerprint)
        logger.info("Restarted Telegram app bot_id=%s", bot_id)

    async def _reconcile(self) -> None:
        active_bots = await self._service.get_active_bots()
        active_by_id = {bot["id"]: bot for bot in active_bots}

        current_ids = set(self._running.keys())
        active_ids = set(active_by_id.keys())

        for bot_id in current_ids - active_ids:
            try:
                await self._stop_bot(bot_id)
            except Exception:
                logger.exception(
                    "Failed to stop Telegram app bot_id=%s", bot_id
                )

        for bot_id, bot in active_by_id.items():
            fingerprint = self._fingerprint_bot(bot)
            running_bot = self._running.get(bot_id)

            if not running_bot:
                try:
                    await self._start_bot(bot, fingerprint)
                except Exception:
                    logger.exception(
                        "Failed to start Telegram app bot_id=%s", bot_id
                    )
                continue

            if running_bot.fingerprint != fingerprint:
                try:
                    await self._restart_bot(bot, fingerprint)
                except Exception:
                    logger.exception(
                        "Failed to restart Telegram app bot_id=%s", bot_id
                    )

    async def run(self) -> None:
        self._active = True
        logger.info(
            "Starting Telegram apps manager interval=%ss",
            self.check_interval,
        )
        try:
            while self._active:
                await self._reconcile()
                await asyncio.sleep(self.check_interval)
        except asyncio.CancelledError:
            logger.info("Telegram apps manager cancelled")
            raise
        finally:
            for bot_id in list(self._running.keys()):
                try:
                    await self._stop_bot(bot_id)
                except Exception:
                    logger.exception(
                        "Failed to stop Telegram app on shutdown bot_id=%s",
                        bot_id,
                    )

    def stop(self) -> None:
        self._active = False


async def telegram_apps_manager_job(check_interval_seconds: int = 60):
    manager = TelegramAppsManager(
        check_interval_seconds=check_interval_seconds,
    )
    await manager.run()
