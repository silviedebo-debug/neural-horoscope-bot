"""
Точка входа. Запуск: python main.py
Все настройки — через переменные окружения (см. .env.example).
"""
import logging
from logging.handlers import RotatingFileHandler

from telegram.ext import Application, CommandHandler, MessageHandler, filters

from bot.config import Config
from bot.db import init_db, load_cache
from bot.apify_service import refresh_horoscope_cache
from bot.handlers import start, handle_message, error_handler
from bot.scheduler import scheduled_refresh_job, scheduled_daily_report_job, scheduled_backup_job


def setup_logging():
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO,
        handlers=[
            logging.StreamHandler(),
            # Ротация: не более 5 МБ на файл, храним 3 последних — лог не растёт бесконечно
            RotatingFileHandler("bot_requests.log", maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"),
        ],
    )
    # httpx (используется внутри python-telegram-bot) логирует каждый HTTP-запрос на уровне INFO —
    # это создаёт большой шум и может случайно засветить токен в URL. Понижаем уровень.
    logging.getLogger("httpx").setLevel(logging.WARNING)


def main():
    setup_logging()
    logger = logging.getLogger(__name__)

    Config.log_startup_summary()
    init_db()

    if not load_cache():
        logger.info("Кэш пуст при старте — выполняем первичное наполнение")
        refresh_horoscope_cache()

    app = Application.builder().token(Config.TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(error_handler)

    app.job_queue.run_daily(scheduled_refresh_job, time=Config.HOROSCOPE_REFRESH_TIME, name="refresh_horoscope")
    app.job_queue.run_daily(scheduled_daily_report_job, time=Config.DAILY_REPORT_TIME, name="daily_report")
    app.job_queue.run_daily(scheduled_backup_job, time=Config.DAILY_REPORT_TIME, name="db_backup")

    logger.info("Бот запущен. Ожидание сообщений...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
