from service.logger import logger
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Tuple, Optional

from service.settings import (
    ALLOWED_CURRENCY_PAIRS,
    YAHOO_FINANCIAL_ASSETS,
    CURRENCY_FLAGS,
    FINANCE_EMOJIS,
    CRYPTO_EMOJIS,
    DEFAULT_EMOJIS,
)


class EmojiResolver:
    @staticmethod
    def get_currency_flag(pair: str) -> str:
        return CURRENCY_FLAGS.get(pair, DEFAULT_EMOJIS['currency'])

    @staticmethod
    def get_finance_emoji(name: str) -> str:
        return FINANCE_EMOJIS.get(name, DEFAULT_EMOJIS['finance'])

    @staticmethod
    def get_crypto_emoji(code: str) -> str:
        return CRYPTO_EMOJIS.get(code, DEFAULT_EMOJIS['crypto'])


class TimeUtils:
    @staticmethod
    def get_moscow_time() -> Tuple[str, str]:
        tz = timezone(timedelta(hours=3))
        now = datetime.now(tz)
        return now.strftime("%d.%m.%Y"), now.strftime("%H:%M")


class Formatter:
    @staticmethod
    def _round(value: float, precision: int) -> float:
        try:
            return round(float(value), precision)
        except (TypeError, ValueError):
            logger.warning(f"Failed to round value: {value}")
            return value

    @staticmethod
    def _format_number(value: Any) -> str:
        try:
            number = float(value)
            return f"{number:,.2f}".replace(",", " ").replace(".", ",")
        except (TypeError, ValueError):
            logger.warning(f"Не удалось отформатировать значение: {value}")
            return str(value)

    @staticmethod
    def _format_change(label: str, change: Any, is_crypto: bool) -> Optional[str]:
        if change is None:
            return None
        try:
            number = float(str(change).replace("%", "").replace(",", ".").replace("−", "-").strip())
        except Exception as e:
            logger.warning(f"Не удалось распарсить изменение '{change}': {e}")
            return None

        if abs(number) <= 0.01:
            return f"{label}➖0.00%"

        arrow = "🟢" if is_crypto and number > 0 else "🔻" if is_crypto else "▲" if number > 0 else "▼"
        formatted_number = f"{abs(number):.2f}%"
        return f"{label}{arrow}{formatted_number}"

    def _format_line(
        self,
        name: str,
        value: Any,
        change_1h: Optional[Any] = None,
        change_1d: Optional[Any] = None,
        change_1w: Optional[Any] = None,
        emoji: str = "",
        is_crypto: bool = False
    ) -> str:
        if name == "Золото":
            value = f"{value} USD/унция"
        elif name == "Нефть Brent":
            value = f"{value} USD/баррель"

        changes = []
        for label, change in [("h", change_1h), ("d", change_1d), ("w", change_1w)]:
            formatted = self._format_change(label, change, is_crypto)
            if formatted:
                changes.append(formatted)

        changes_str = "     " + " ".join(changes) if changes else ""
        return f"{emoji} <b>{name}</b>: <code>{value}</code>\n{changes_str}\n"

    def format_currency_block(self, rates: Dict[str, Dict[str, Any]]) -> str:
        if not rates:
            return "❌ Нет данных о курсах ЦБ РФ."
        lines = ["<b><u>💰 Курсы ЦБ РФ:</u></b>"]
        for pair, data in rates.items():
            if pair not in ALLOWED_CURRENCY_PAIRS:
                continue
            value = data.get("value")
            if value is None:
                continue
            lines.append(self._format_line(
                name=pair,
                value=self._format_number(value),
                change_1h=data.get("change_1h"),
                change_1d=data.get("change_1d"),
                change_1w=data.get("change_1w"),
                emoji=EmojiResolver.get_currency_flag(pair),
                is_crypto=False
            ))
        return "\n".join(lines)

    def format_financial_block(self, data: Dict[str, Dict[str, Any]]) -> str:
        if not data:
            return "❌ Нет данных о финансовых инструментах."
        allowed_names = {asset["name"] for asset in YAHOO_FINANCIAL_ASSETS}
        lines = ["<b><u>📊 Финансовые инструменты:</u></b>"]
        for name, entry in data.items():
            if name not in allowed_names:
                continue
            value = entry.get("value")
            if value is None:
                continue
            lines.append(self._format_line(
                name=name,
                value=self._format_number(value),
                change_1h=entry.get("change_1h"),
                change_1d=entry.get("change_1d"),
                change_1w=entry.get("change_1w"),
                emoji=EmojiResolver.get_finance_emoji(name),
                is_crypto=False
            ))
        return "\n".join(lines)

    def format_crypto_block(self, data: Dict[str, Dict[str, Any]]) -> str:
        if not data:
            return "❌ Нет данных о криптовалютах.\n"

        parts = []

        always = data.get("always", {})
        if always:
            lines = ["<b><u>💎 Криптовалюты к доллару:</u></b>"]
            for code, entry in always.items():
                lines.append(self._format_crypto_line(code, entry))
            parts.append("\n".join(lines))

        daily_spikes = data.get("daily_spikes", {})
        if daily_spikes:
            lines = ["<b><u>🔥 Рывок за день:</u></b>"]
            for code, entry in daily_spikes.items():
                lines.append(self._format_crypto_line(code, entry))
            parts.append("\n".join(lines))

        hourly_spikes = data.get("hourly_spikes", {})
        if hourly_spikes:
            lines = ["<b><u>🚀 Рывок за час:</u></b>"]
            for code, entry in hourly_spikes.items():
                lines.append(self._format_crypto_line(code, entry))
            parts.append("\n".join(lines))

        return "\n\n".join(parts)

    def _format_crypto_line(self, code: str, entry: Dict[str, Any]) -> str:
        value = entry.get("value")
        precision = 2 if code == "BTC" else 4
        rounded = self._round(value, precision)
        formatted_value = self._format_number(rounded)
        return self._format_line(
            name=code,
            value=formatted_value,
            change_1h=entry.get("change_1h"),
            change_1d=entry.get("change_1d"),
            change_1w=entry.get("change_1w"),
            emoji=EmojiResolver.get_crypto_emoji(code),
            is_crypto=True
        )


def create_telegram_message(
    cbr_rates: Dict[str, Dict[str, Any]],
    finance_data: Dict[str, Dict[str, Any]],
    crypto_data: Dict[str, Dict[str, Any]]
) -> str:
    logger.info("Создание Telegram-сообщения")
    date_str, time_str = TimeUtils.get_moscow_time()
    header = f"<b>🚓 {date_str}</b> 🕒 Upd: <code>{time_str} МСК</code>"

    PAY_WORLD_REF_LINK = "https://trk.ppdu.ru/click/kmN6RlAR?erid=2SDnjdQghsC"

    formatter = Formatter()
    blocks = [
        formatter.format_currency_block(cbr_rates),
        formatter.format_financial_block(finance_data),
        formatter.format_crypto_block(crypto_data)
    ]

    # Короткое УТП в одну строчку, чтобы не перегружать пост
    pay_world_teaser = (
        '💳 <b>Плати по миру</b> — виртуальная USD-карта для оплат за рубежом: '
        'моментальный выпуск в Telegram (~2 мин), пополнение через СБП 0%, '
        'первый год без абонплаты, приветственный бонус <b>$10</b>. '
        f'<a href="{PAY_WORLD_REF_LINK}">Оформить карту</a>'
    )

    footer = (
        '🚓 <a href="https://t.me/currency_patrol">ФинПатруль</a> | #USD #BTC #курс_рубля\n'
        f'{pay_world_teaser}'
    )

    message = "\n\n".join(block.strip() for block in blocks if block.strip())
    return f"{header}\n\n{message}\n\n{footer}"

