import logging

from telegram import Update
from telegram.ext import ContextTypes

from bot.config import Config
from bot.db import load_cache, log_request
from bot.parser import format_horoscope_answer
from bot.ratelimit import is_rate_limited

logger = logging.getLogger(__name__)

SIGNS_HELP_TEXT = (
    "Овен, Телец, Близнецы, Рак, Лев, Дева, Весы, Скорпион, Стрелец, Козерог, Водолей, Рыбы"
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    logger.info(f"СТАРТ от user_id={user.id} (@{user.username}, {user.first_name or 'без имени'})")
    log_request(user.id, user.username, user.first_name, "/start")

    await update.message.reply_text(
        "🌟 Привет! Я — бот Нейрогороскоп с баяном.\n\n"
        "Просто напиши название своего знака зодиака:\n"
        "Овен, Телец, Близнецы, Рак, Лев, Дева, Весы, Скорпион, Стрелец, Козерог, Водолей, Рыбы\n\n"
        "⏳ Настраиваю баян, секунду...
        f"{SIGNS_HELP_TEXT}"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user

    # Защита от флуда — проверяем ДО обращения к БД, чтобы не тратить ресурсы на явный спам
    if is_rate_limited(user.id):
        logger.warning(f"Rate limit сработал для user_id={user.id}")
        return  # молча игнорируем — не даём боту участвовать в диалоге со спамером

    user_input = update.message.text.strip()
    sign_name = user_input.capitalize()

    logger.info(f"ЗАПРОС от user_id={user.id} (@{user.username}) | текст: '{user_input[:50]}'")
    log_request(user.id, user.username, user.first_name, user_input)

    cache_data = load_cache()

    if not cache_data:
        await update.message.reply_text("😔 Гороскоп ещё не забаянен, попробуй чуть позже.")
        return

    if sign_name in cache_data:
        await update.message.reply_text(format_horoscope_answer(sign_name, cache_data[sign_name]))
        return

    for name, text in cache_data.items():
        if user_input.lower() == name.lower():
            await update.message.reply_text(format_horoscope_answer(name, text))
            return

    await update.message.reply_text(
        f"❌ Не знаю такого знака. Попробуй один из этих:\n\n{SIGNS_HELP_TEXT}"
    )


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    # Никогда не логируем полный update целиком — там есть данные пользователя;
    # для дебага достаточно факта ошибки и её текста.
    logger.error(f"Ошибка в обработчике: {context.error}", exc_info=context.error)
