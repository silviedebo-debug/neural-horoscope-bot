"""
Конфигурация приложения.

Все чувствительные значения (токены) приходят ТОЛЬКО из переменных окружения.
Ни один секрет никогда не должен быть захардкожен в коде или попасть в Git.
"""
import os
import sys
import logging
from datetime import time as dtime

logger = logging.getLogger(__name__)


def _get_required(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        logger.critical(f"Переменная окружения {name} не задана. Останавливаю запуск.")
        sys.exit(1)
    return value


def _mask(secret: str) -> str:
    """Маскирует секрет для случайного вывода в лог/консоль (никогда не логировать токен целиком)."""
    if not secret or len(secret) < 8:
        return "***"
    return f"{secret[:4]}...{secret[-4:]}"


class Config:
    TELEGRAM_TOKEN: str = _get_required("TELEGRAM_TOKEN")
    APIFY_API_TOKEN: str = _get_required("APIFY_API_TOKEN")

    # Необязательно: если не задан — ежедневная сводка просто не отправляется (не роняем бота)
    ADMIN_CHAT_ID: str | None = os.environ.get("ADMIN_CHAT_ID")

    APIFY_ACTOR_ID: str = "alex_claw/telegram-channel-scraper"
    TELEGRAM_CHANNEL_URL: str = "https://t.me/neural_horo"

    DB_PATH: str = os.environ.get("DB_PATH", "bot_data.db")

    # Время задач указано в UTC
    HOROSCOPE_REFRESH_TIME = dtime(hour=6, minute=0)
    DAILY_REPORT_TIME = dtime(hour=9, minute=0)

    # Простая защита от флуда: не более N сообщений от одного пользователя за период (сек)
    RATE_LIMIT_MAX_MESSAGES = 10
    RATE_LIMIT_PERIOD_SECONDS = 60

    # Максимальная длина сообщения, которую сохраняем в БД (защита от раздувания базы мусором)
    MAX_LOGGED_MESSAGE_LENGTH = 200

    @classmethod
    def log_startup_summary(cls):
        logger.info("Конфигурация загружена:")
        logger.info(f"  TELEGRAM_TOKEN: {_mask(cls.TELEGRAM_TOKEN)}")
        logger.info(f"  APIFY_API_TOKEN: {_mask(cls.APIFY_API_TOKEN)}")
        logger.info(f"  ADMIN_CHAT_ID задан: {'да' if cls.ADMIN_CHAT_ID else 'нет'}")
        logger.info(f"  DB_PATH: {cls.DB_PATH}")
