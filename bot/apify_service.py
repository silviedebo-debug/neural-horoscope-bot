"""
Взаимодействие с Apify. Единственное место в проекте, где расходуются платные
запуски актора — вызывается ТОЛЬКО из плановой job раз в сутки, никогда напрямую
из пользовательских хендлеров.
"""
import time
import logging

from apify_client import ApifyClient

from bot.config import Config
from bot.parser import parse_horoscope
from bot.db import save_cache

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = 5  # 5s, 10s, 20s между попытками


def _fetch_last_post() -> str | None:
    client = ApifyClient(Config.APIFY_API_TOKEN)
    run_input = {"channelUrls": [Config.TELEGRAM_CHANNEL_URL]}

    run = client.actor(Config.APIFY_ACTOR_ID).call(run_input=run_input)
    dataset_id = run["defaultDatasetId"] if isinstance(run, dict) else run.default_dataset_id

    posts = list(client.dataset(dataset_id).iterate_items())
    logger.info(f"Всего элементов в датасете: {len(posts)}")

    if not posts:
        logger.warning("Постов в ответе от Apify нет")
        return None

    def safe_post_id(p):
        try:
            return int(p.get("postId", 0))
        except (ValueError, TypeError):
            return 0

    last_post = sorted(posts, key=safe_post_id)[-1]
    logger.info(f"Взят пост #{last_post.get('postId')} от {last_post.get('postDate')}")

    return last_post.get("postText")


def refresh_horoscope_cache() -> bool:
    """
    Обновляет кэш гороскопа. Делает до MAX_RETRIES попыток с экспоненциальной паузой,
    чтобы разовый сетевой сбой Apify не оставил пользователей без обновления на сутки.
    Возвращает True при успехе, False если все попытки провалились (старый кэш сохраняется).
    """
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info(f"Запрос к Apify, попытка {attempt}/{MAX_RETRIES}...")
            post_text = _fetch_last_post()

            if not post_text:
                logger.warning("В посте нет текста")
                return False

            horoscopes = parse_horoscope(post_text)
            if not horoscopes:
                logger.warning("Парсинг не нашёл ни одного знака в тексте поста")
                return False

            save_cache(horoscopes)
            logger.info(f"Кэш обновлён. Знаков: {len(horoscopes)}")
            return True

        except Exception as e:
            logger.error(f"Ошибка при запросе к Apify (попытка {attempt}/{MAX_RETRIES}): {e}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_BACKOFF_SECONDS * attempt)

    logger.error("Все попытки обновить кэш провалились — оставляем предыдущие данные")
    return False
