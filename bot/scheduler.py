import logging

from telegram.ext import ContextTypes

from bot.config import Config
from bot.apify_service import refresh_horoscope_cache
from bot.db import get_requests_last_24h, backup_database

logger = logging.getLogger(__name__)


async def scheduled_refresh_job(context: ContextTypes.DEFAULT_TYPE):
    logger.info("Плановая job: обновление гороскопа")
    success = refresh_horoscope_cache()

    if not success and Config.ADMIN_CHAT_ID:
        try:
            await context.bot.send_message(
                chat_id=Config.ADMIN_CHAT_ID,
                text="⚠️ Не удалось обновить гороскоп сегодня. Пользователи получают вчерашние данные. Проверь логи."
            )
        except Exception as e:
            logger.error(f"Не удалось уведомить админа о сбое обновления: {e}")


async def scheduled_daily_report_job(context: ContextTypes.DEFAULT_TYPE):
    logger.info("Плановая job: ежедневная сводка админу")

    if not Config.ADMIN_CHAT_ID:
        logger.warning("ADMIN_CHAT_ID не задан, сводка не отправлена")
        return

    rows = get_requests_last_24h()

    if not rows:
        text = "📊 Сводка за последние 24 часа:\n\nОбращений не было."
    else:
        unique_users = {}
        for r in rows:
            entry = unique_users.setdefault(r["user_id"], {
                "username": r["username"],
                "first_name": r["first_name"],
                "count": 0
            })
            entry["count"] += 1

        lines = [
            "📊 Сводка за последние 24 часа:\n",
            f"Всего обращений: {len(rows)}",
            f"Уникальных пользователей: {len(unique_users)}\n",
        ]
        for uid, info in unique_users.items():
            uname = f"@{info['username']}" if info["username"] else "(без username)"
            name = info["first_name"] or "без имени"
            lines.append(f"• {name} {uname} (id={uid}) — {info['count']} запрос(ов)")
        text = "\n".join(lines)

    try:
        await context.bot.send_message(chat_id=Config.ADMIN_CHAT_ID, text=text)
        logger.info("Сводка отправлена админу")
    except Exception as e:
        logger.error(f"Не удалось отправить сводку админу: {e}")


async def scheduled_backup_job(context: ContextTypes.DEFAULT_TYPE):
    """Ежедневная резервная копия БД — защита от потери данных при пересборке контейнера."""
    try:
        backup_database(f"{Config.DB_PATH}.backup")
    except Exception as e:
        logger.error(f"Не удалось создать резервную копию БД: {e}")
