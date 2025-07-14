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
import json
from database import Database
from data_processor import process_data
from service.settings import TELEGRAM_CHANNEL_ID, DEBUG, SCHEDULER_SETTINGS


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
        cbr_rates = get_currency_rates()
        finance_data = await get_yahoo_prices()
        crypto_data = await get_crypto_prices()

        yesterday_data_raw = self.db.get_last_daily_data()
        yesterday_data = {}

        if isinstance(yesterday_data_raw, str):
            try:
                yesterday_data = json.loads(yesterday_data_raw)
            except json.JSONDecodeError as e:
                logger.error(f"Ошибка декодирования yesterday_data: {e}")
        elif isinstance(yesterday_data_raw, dict):
            yesterday_data = yesterday_data_raw

        if not cbr_rates and 'cbr_rates' in yesterday_data:
            logger.warning("📄 Нет свежих данных ЦБ РФ, используем данные из БД")
            cbr_rates = {k: v['value'] for k, v in yesterday_data['cbr_rates'].items()}

        if not finance_data and 'finance_data' in yesterday_data:
            logger.warning("📄 Нет свежих данных фин. инструментов, используем данные из БД")
            finance_data = {k: v['value'] for k, v in yesterday_data['finance_data'].items()}

        # 👇 вот тут меняем работу с crypto_data
        flat_crypto = {}
        if crypto_data:
            # оставляем оригинальные daily_spikes/hourly_spikes
            daily_spikes = crypto_data.get("daily_spikes", {})
            hourly_spikes = crypto_data.get("hourly_spikes", {})
            always = crypto_data.get("always", {})

            # для always — обрабатываем как раньше
            flat_crypto.update(always)

            # для остальных сохраняем отдельно
            self.daily_spikes = daily_spikes
            self.hourly_spikes = hourly_spikes

        logger.debug(f"✅ flat_crypto: {flat_crypto}")

        processed_cbr_rates = process_data(
            cbr_rates, yesterday_data.get("cbr_rates", {})
        )
        processed_finance_data = process_data(
            finance_data, yesterday_data.get("finance_data", {})
        )
        processed_crypto_data = process_data(
            flat_crypto, yesterday_data.get("crypto_data", {}), is_crypto=True
        )

        # добавляем обратно daily_spikes и hourly_spikes (с данными из API)
        processed_crypto_data_full = {
            "always": processed_crypto_data,
            "daily_spikes": self.daily_spikes,
            "hourly_spikes": self.hourly_spikes,
        }

        self.save_history_snapshot(processed_cbr_rates, processed_finance_data, processed_crypto_data)

        return processed_cbr_rates, processed_finance_data, processed_crypto_data_full

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
        self.scheduler.add_job(self.send_daily_message, trigger="date",
                               run_date=now + timedelta(seconds=SCHEDULER_SETTINGS["debug"]["first_run_delay_seconds"]))
        self.scheduler.add_job(self.edit_message, trigger="interval",
                               seconds=SCHEDULER_SETTINGS["debug"]["edit_interval_seconds"])
        self.scheduler.add_job(self.stop_editing, trigger="date",
                               run_date=now + timedelta(minutes=SCHEDULER_SETTINGS["debug"]["stop_edit_after_minutes"]))

    def _setup_production_jobs(self):
        """Настраивает задачи для продакшена."""

        # если за сегодня ещё нет сообщения — отправляем через 10 секунд
        if not self.db.get_today_message():
            delay = timedelta(seconds=SCHEDULER_SETTINGS["first_message_delay_seconds"])
            run_time = datetime.now() + delay
            logger.info(f"Сообщение за сегодня не найдено. Запланирована публикация через {delay.seconds} секунд.")
            self.scheduler.add_job(
                self.send_daily_message,
                trigger="date",
                run_date=run_time
            )

        # основное сообщение по расписанию
        self.scheduler.add_job(
            self.send_daily_message,
            trigger="cron",
            hour=SCHEDULER_SETTINGS["daily_post_time"]["hour"],
            minute=SCHEDULER_SETTINGS["daily_post_time"]["minute"],
            timezone="Europe/Moscow"
        )

        # периодическое редактирование в течение дня
        self.scheduler.add_job(
            self.edit_message,
            trigger="interval",
            minutes=SCHEDULER_SETTINGS["edit_interval_minutes"]
        )

        # последняя правка перед завершением дня
        self.scheduler.add_job(
            self.edit_message,
            trigger="cron",
            hour=SCHEDULER_SETTINGS["last_edit_time"]["hour"],
            minute=SCHEDULER_SETTINGS["last_edit_time"]["minute"],
            timezone="Europe/Moscow"
        )

        # останавливаем редактирование
        self.scheduler.add_job(
            self.stop_editing,
            trigger="cron",
            hour=SCHEDULER_SETTINGS["stop_edit_time"]["hour"],
            minute=SCHEDULER_SETTINGS["stop_edit_time"]["minute"],
            timezone="Europe/Moscow"
        )

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
