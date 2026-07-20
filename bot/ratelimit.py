"""
Простейший rate limiter в памяти процесса: не более N сообщений за период на user_id.
Не переживает перезапуск процесса — это осознанный компромисс: для защиты от флуда
персистентность не нужна, а усложнять БД лишними записями ради rate-лимита незачем.
"""
import time
from collections import defaultdict, deque

from bot.config import Config

_history: dict[int, deque] = defaultdict(deque)


def is_rate_limited(user_id: int) -> bool:
    now = time.monotonic()
    window = _history[user_id]

    while window and now - window[0] > Config.RATE_LIMIT_PERIOD_SECONDS:
        window.popleft()

    if len(window) >= Config.RATE_LIMIT_MAX_MESSAGES:
        return True

    window.append(now)
    return False
