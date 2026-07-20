"""
Слой доступа к данным (SQLite).

Почему SQLite, а не in-memory dict:
- Переживает перезапуск процесса (важно для бесплатного хостинга, где рестарты обычны).
- Не требует отдельного сервера БД — подходит для пет-проекта такого масштаба.
- WAL-режим даёт достаточно производительности для одного бота с низкой нагрузкой.
"""
import sqlite3
import logging
from datetime import datetime
from contextlib import contextmanager

from bot.config import Config

logger = logging.getLogger(__name__)


@contextmanager
def get_connection():
    conn = sqlite3.connect(Config.DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_connection() as conn:
        # WAL-режим: пишущие и читающие запросы не блокируют друг друга
        conn.execute("PRAGMA journal_mode=WAL")

        conn.execute("""
            CREATE TABLE IF NOT EXISTS horoscope_cache (
                sign TEXT PRIMARY KEY,
                text TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS meta (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS requests_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username TEXT,
                first_name TEXT,
                query_text TEXT,
                timestamp TEXT NOT NULL
            )
        """)
        # Индекс критичен для производительности выборки "за последние 24 часа"
        # при росте таблицы (иначе будет полный скан таблицы каждый день)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_requests_timestamp
            ON requests_log (timestamp)
        """)
    logger.info("База данных инициализирована (WAL-режим, индексы созданы)")


def save_cache(horoscopes: dict):
    with get_connection() as conn:
        conn.execute("DELETE FROM horoscope_cache")
        conn.executemany(
            "INSERT INTO horoscope_cache (sign, text) VALUES (?, ?)",
            list(horoscopes.items())
        )
        conn.execute(
            "INSERT OR REPLACE INTO meta (key, value) VALUES ('updated_at', ?)",
            (datetime.utcnow().isoformat(),)
        )


def load_cache() -> dict:
    with get_connection() as conn:
        rows = conn.execute("SELECT sign, text FROM horoscope_cache").fetchall()
    return {row["sign"]: row["text"] for row in rows}


def get_last_updated() -> str | None:
    with get_connection() as conn:
        row = conn.execute("SELECT value FROM meta WHERE key='updated_at'").fetchone()
    return row["value"] if row else None


def log_request(user_id: int, username: str | None, first_name: str | None, query_text: str):
    # Защита от раздувания БД чрезмерно длинными сообщениями
    safe_text = (query_text or "")[:Config.MAX_LOGGED_MESSAGE_LENGTH]
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO requests_log (user_id, username, first_name, query_text, timestamp)
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, username, first_name, safe_text, datetime.utcnow().isoformat())
        )


def get_requests_last_24h():
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT user_id, username, first_name, query_text, timestamp
            FROM requests_log
            WHERE datetime(timestamp) >= datetime('now', '-1 day')
            ORDER BY timestamp ASC
        """).fetchall()
    return rows


def backup_database(backup_path: str):
    """Резервная копия БД. Вызывать периодически (например, из ежедневной job)."""
    with get_connection() as conn:
        backup_conn = sqlite3.connect(backup_path)
        conn.backup(backup_conn)
        backup_conn.close()
    logger.info(f"Резервная копия БД сохранена: {backup_path}")
