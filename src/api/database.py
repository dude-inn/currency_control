import sqlite3
from datetime import datetime, timedelta
import json
from typing import Optional, Tuple, Any, Dict
from contextlib import contextmanager
import pytz

from service.logger import logger


class Database:
    def __init__(self, db_path: str = "data.db") -> None:
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()
        logger.debug("Инициализация базы данных завершена")

    def _create_tables(self) -> None:
        with self._transaction() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS history_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticker TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    value REAL NOT NULL,
                    type TEXT NOT NULL,
                    UNIQUE(ticker, timestamp, type)
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL UNIQUE,
                    data TEXT NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL UNIQUE,
                    message_id INTEGER NOT NULL,
                    data TEXT NOT NULL
                )
            """)
        logger.debug("Таблицы успешно созданы или уже существуют")

    @contextmanager
    def _transaction(self):
        cursor = self.conn.cursor()
        try:
            yield cursor
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Ошибка в транзакции: {e}")
            raise

    def save_data(self, message_id: int, data: Dict[str, Any]) -> None:
        current_date = self._current_date()
        with self._transaction() as cursor:
            cursor.execute("""
                INSERT OR REPLACE INTO messages (date, message_id, data)
                VALUES (?, ?, ?)
            """, (current_date, message_id, json.dumps(data, ensure_ascii=False)))
        logger.info(f"Сообщение за {current_date} сохранено (ID: {message_id})")

    def save_daily_data(self, data: Dict[str, Any]) -> None:
        today = self._current_date()
        with self._transaction() as cursor:
            cursor.execute("""
                INSERT OR REPLACE INTO daily_data (date, data)
                VALUES (?, ?)
            """, (today, json.dumps(data, ensure_ascii=False)))
        logger.info(f"Дневные данные за {today} успешно сохранены")

    def save_last_daily_message(self, message_id: int, data: Dict[str, Any]) -> None:
        current_date = self._current_date()
        with self._transaction() as cursor:
            cursor.execute("DELETE FROM messages WHERE date = ?", (current_date,))
            cursor.execute("""
                INSERT INTO messages (date, message_id, data)
                VALUES (?, ?, ?)
            """, (current_date, message_id, json.dumps(data, ensure_ascii=False)))
        logger.info(f"Последнее сообщение дня за {current_date} сохранено (ID: {message_id})")

    def get_today_message(self) -> Optional[Tuple[int, Dict[str, Any]]]:
        today = self._current_date()
        with self._transaction() as cursor:
            cursor.execute("""
                SELECT message_id, data FROM messages 
                WHERE date = ? ORDER BY id DESC LIMIT 1
            """, (today,))
            if result := cursor.fetchone():
                logger.debug(f"Найдено сообщение за сегодня ({today})")
                return result["message_id"], json.loads(result["data"])
        logger.debug("Сообщение за сегодня не найдено")
        return None

    def get_previous_day_message(self) -> Optional[Tuple[int, str]]:
        previous_day = self._current_date(days_ago=1)
        with self._transaction() as cursor:
            cursor.execute("""
                SELECT message_id, data FROM messages 
                WHERE date = ? ORDER BY id DESC LIMIT 1
            """, (previous_day,))
            if result := cursor.fetchone():
                logger.debug(f"Сообщение за предыдущий день ({previous_day}) получено")
                return result["message_id"], result["data"]
        logger.debug("Сообщение за предыдущий день не найдено")
        return None

    def get_last_daily_data(self) -> Dict[str, Any]:
        yesterday = self._current_date(days_ago=1)
        with self._transaction() as cursor:
            cursor.execute("SELECT data FROM daily_data WHERE date = ?", (yesterday,))
            if result := cursor.fetchone():
                logger.debug(f"Дневные данные за {yesterday} получены")
                return json.loads(result["data"])
        logger.debug(f"Дневные данные за {yesterday} отсутствуют")
        return {}

    def get_yesterday_last_data(self) -> Optional[Tuple[int, Dict[str, Any]]]:
        yesterday = self._current_date(days_ago=1)
        with self._transaction() as cursor:
            cursor.execute("""
                SELECT message_id, data FROM messages 
                WHERE date = ? ORDER BY id DESC LIMIT 1
            """, (yesterday,))
            if result := cursor.fetchone():
                logger.debug(f"Последнее сообщение за вчера ({yesterday}) получено")
                return result["message_id"], json.loads(result["data"])
        logger.debug(f"Последнее сообщение за вчера ({yesterday}) не найдено")
        return None

    def save_history_data(self, ticker: str, value: float, data_type: str) -> None:
        timestamp = datetime.now(pytz.timezone('Europe/Moscow')).isoformat()
        with self._transaction() as cursor:
            cursor.execute("""
                INSERT OR IGNORE INTO history_data (ticker, timestamp, value, type)
                VALUES (?, ?, ?, ?)
            """, (ticker, timestamp, value, data_type))
        logger.debug(f"Исторические данные сохранены: {ticker} ({data_type}) = {value} @ {timestamp}")

    def get_change(self, ticker: str, current_value: float, data_type: str, delta: timedelta) -> Optional[float]:
        tz = pytz.timezone('Europe/Moscow')
        target_time = datetime.now(tz) - delta
        target_iso = target_time.isoformat()

        with self._transaction() as cursor:
            # 1. Пробуем найти в history_data
            cursor.execute("""
                SELECT value FROM history_data 
                WHERE ticker = ? AND type = ? AND timestamp <= ?
                ORDER BY timestamp DESC LIMIT 1
            """, (ticker, data_type, target_iso))
            row = cursor.fetchone()

            if row:
                past_value = row["value"]
                if past_value:
                    change = round(((current_value - past_value) / past_value) * 100, 2)
                    logger.debug(f"Изменение {ticker} ({data_type}) за {delta}: {change}% (по history_data)")
                    return change

            # 2. fallback: пробуем из daily_data (только если delta == 1 день)
            if delta == timedelta(days=1):
                date_str = self._current_date(days_ago=1)
                cursor.execute("SELECT data FROM daily_data WHERE date = ?", (date_str,))
                row = cursor.fetchone()
                if row:
                    try:
                        data = json.loads(row["data"])
                        past_value = data.get(ticker, {}).get("value")
                        if past_value:
                            change = round(((current_value - past_value) / past_value) * 100, 2)
                            logger.debug(f"Изменение {ticker} ({data_type}) за {delta}: {change}% (по daily_data)")
                            return change
                    except Exception as e:
                        logger.warning(f"Ошибка при обработке daily_data fallback для {ticker}: {e}")

        logger.debug(f"Недостаточно данных для расчета изменения {ticker} ({data_type}) за {delta}")
        return None

    def clear_old_data(self, days_threshold: int = 8) -> None:
        cutoff_date = self._current_date(days_ago=days_threshold)
        with self._transaction() as cursor:
            cursor.execute("DELETE FROM messages WHERE date < ?", (cutoff_date,))
        logger.info(f"Старые данные до {cutoff_date} удалены")

    def clear_invalid_data(self, min_length: int = 50) -> None:
        with self._transaction() as cursor:
            cursor.execute("DELETE FROM messages WHERE LENGTH(data) < ?", (min_length,))
        logger.info(f"Удалены некорректные записи (длина данных < {min_length})")

    def close(self) -> None:
        self.conn.close()
        logger.debug("Соединение с базой данных закрыто")

    def _current_date(self, days_ago: int = 0) -> str:
        moscow_time = datetime.now(pytz.timezone('Europe/Moscow')) - timedelta(days=days_ago)
        return moscow_time.strftime("%Y-%m-%d")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
