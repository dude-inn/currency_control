import asyncio
from datetime import datetime, timedelta, time

import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from service.logger import logger
from telegr.sender import send_telegram_message, edit_telegram_message
from create_telegram_message import create_telegram_message
from get_cb_data import get_currency_rates
from get_yahoo_data import get_prices as get_yahoo_prices
from get_crypto_data import get_prices as get_crypto_prices
from service.settings import TELEGRAM_CHANNEL_ID, DEBUG
import json
from database import Database
from data_processor import process_data


class TelegramBot:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.db = Database()
        self._init_message_state()

    def _init_message_state(self):
        """Инициализирует состояние сообщения (редактирование и ID)."""
        today_message = self.db.get_today_message()
        if today_message:
            self.message_id, _ = today_message
            self.is_editing_active = True
            logger.info(f"Найдено сообщение за сегодня (ID: {self.message_id}).")
        else:
            self.message_id = None
            self.is_editing_active = False
            logger.info("Сообщение за сегодня отсутствует.")

        self.scheduler.add_job(
            self.clear_old_data,
            trigger="interval",
            hours=24,
            timezone="Europe/Moscow"
        )
        logger.info("Задача на очистку старых данных добавлена (каждые 24ч).")

    async def stop_editing(self):
        """Останавливает редактирование сообщения."""
        self.is_editing_active = False
        logger.info("Редактирование сообщения остановлено.")

    async def fetch_data(self):
        """Получает данные от всех источников и валидирует их."""
        try:
            cbr_rates = get_currency_rates()
            finance_data = await get_yahoo_prices()
            crypto_data = await get_crypto_prices()

            # Валидация нулевых значений
            for name, data in (
                ("ЦБ РФ", cbr_rates),
                ("Yahoo Finance", finance_data),
                ("Криптовалюты", crypto_data)
            ):
                for key, value in data.items():
                    if value == 0:
                        logger.warning(f"Нулевое значение в {name} для {key}")

            return cbr_rates, finance_data, crypto_data
        except Exception as e:
            logger.error(f"Ошибка при получении данных: {e}")
            return {}, {}, {}

    async def clear_old_data(self):
        """Очищает старые данные из базы."""
        logger.info("Очистка старых данных...")
        self.db.clear_old_data()
        logger.info("Очистка завершена.")

    async def fetch_and_process_data(self):
        """Получает и обрабатывает данные, а также сохраняет исторические значения."""
        cbr_rates, finance_data, crypto_data = await self.fetch_data()

        yesterday_data = self.db.get_yesterday_last_data()
        old_data = {}

        if yesterday_data:
            _, old_data_str = yesterday_data
            try:
                if isinstance(old_data_str, str):
                    old_data = json.loads(old_data_str)
                elif isinstance(old_data_str, dict):
                    old_data = old_data_str
            except json.JSONDecodeError as e:
                logger.error(f"Ошибка декодирования old_data: {e}")
                old_data = {}

        processed_cbr_rates = process_data(cbr_rates, old_data.get("cbr_rates", {}))
        processed_finance_data = process_data(finance_data, old_data.get("finance_data", {}))
        processed_crypto_data = process_data(crypto_data, old_data.get("crypto_data", {}), is_crypto=True)

        # 💾 Сохраняем исторические данные
        self.save_history_snapshot(processed_cbr_rates, processed_finance_data, processed_crypto_data)

        return processed_cbr_rates, processed_finance_data, processed_crypto_data

    def save_history_snapshot(self, cbr_rates, finance_data, crypto_data):
        """Сохраняет значения в таблицу истории."""
        for ticker, item in cbr_rates.items():
            self.db.save_history_data(ticker, item["value"], "cbr")
        for ticker, item in finance_data.items():
            self.db.save_history_data(ticker, item["value"], "finance")
        for ticker, item in crypto_data.items():
            self.db.save_history_data(ticker, item["value"], "crypto")

    async def _send_new_message(self, processed_data):
        """Отправляет новое сообщение и сохраняет данные."""
        telegram_message = create_telegram_message(*processed_data)
        self.message_id = await send_telegram_message(telegram_message, TELEGRAM_CHANNEL_ID)

        if not self.message_id:
            logger.error("Ошибка отправки сообщения")
            return

        logger.info(f"Сообщение отправлено (ID: {self.message_id})")
        self.is_editing_active = True

        data_to_save = {
            "cbr_rates": processed_data[0],
            "finance_data": processed_data[1],
            "crypto_data": processed_data[2]
        }
        self.db.save_data(self.message_id, json.dumps(data_to_save))
        self.db.save_daily_data(json.dumps(data_to_save))

    async def send_daily_message(self):
        """Отправляет/редактирует ежедневное сообщение."""
        if self.db.get_today_message():
            logger.info("Редактируем существующее сообщение...")
            await self.edit_message()
            return

        logger.info("Отправляем новое сообщение...")
        await self._send_new_message(await self.fetch_and_process_data())

    async def edit_message(self):
        """Редактирует сообщение и сохраняет в БД только в 23:57."""
        if not (self.is_editing_active and self.message_id):
            return

        processed_data = await self.fetch_and_process_data()
        updated_message = create_telegram_message(*processed_data)

        if await edit_telegram_message(updated_message, TELEGRAM_CHANNEL_ID, self.message_id):
            logger.info("Сообщение отредактировано")

            # Проверка времени (23:57 ±2 минуты)
            moscow_tz = pytz.timezone('Europe/Moscow')
            current_time = datetime.now(moscow_tz).time()
            target_time = time(23, 57)

            if current_time.hour == target_time.hour and target_time.minute - 2 <= current_time.minute <= target_time.minute + 2:
                data_to_save = {
                    "cbr_rates": processed_data[0],
                    "finance_data": processed_data[1],
                    "crypto_data": processed_data[2]
                }
                self.db.save_last_daily_message(self.message_id, data_to_save)
        else:
            logger.error("Ошибка редактирования")

    async def start_scheduler(self):
        """Запускает планировщик задач."""
        self.db.clear_invalid_data()

        if DEBUG:
            logger.info("\n\nРЕЖИМ ОТЛАДКИ")
            self._setup_debug_jobs()
        else:
            self._setup_production_jobs()

        self.scheduler.start()
        logger.info("Планировщик запущен")

    def _setup_debug_jobs(self):
        """Настраивает задачи для режима отладки."""
        now = datetime.now()
        self.scheduler.add_job(self.send_daily_message, trigger="date", run_date=now + timedelta(seconds=10))
        self.scheduler.add_job(self.edit_message, trigger="interval", seconds=30)
        self.scheduler.add_job(self.stop_editing, trigger="date", run_date=now + timedelta(minutes=5))

    def _setup_production_jobs(self):
        """Настраивает задачи для продакшена."""
        if not self.db.get_today_message():
            self.scheduler.add_job(self.send_daily_message, trigger="date", run_date=datetime.now() + timedelta(seconds=10))

        self.scheduler.add_job(self.send_daily_message, trigger="cron", hour=0, minute=0, timezone="Europe/Moscow")
        self.scheduler.add_job(self.edit_message, trigger="interval", minutes=3)
        self.scheduler.add_job(self.edit_message, trigger="cron", hour=23, minute=57, timezone="Europe/Moscow")
        self.scheduler.add_job(self.stop_editing, trigger="cron", hour=23, minute=59, timezone="Europe/Moscow")

    def stop_scheduler(self):
        """Останавливает планировщик."""
        self.scheduler.shutdown()
        logger.info("Планировщик остановлен")


async def main():
    bot = TelegramBot()
    await bot.start_scheduler()
    try:
        while True:
            await asyncio.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        bot.stop_scheduler()


if __name__ == "__main__":
    asyncio.run(main())
