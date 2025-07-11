from service.logger import logger
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Tuple, Optional

TICKER_NAMES = {
    "GOLD": "Золото",
    "BZ=F": "Нефть Brent",
    "^GSPC": "S&P 500",
    "^IXIC": "NASDAQ",
    "IMOEX.ME": "Индекс МосБиржи",
    "EURUSD=X": "EUR-USD",
    "USDBYN=X": "USD-BYN",
    "USDKZT=X": "USD-KZT",
    "USDUAH=X": "USD-UAH"
}

CURRENCY_FLAGS = {
    "USD-RUB": "🇺🇸",
    "EUR-RUB": "🇪🇺",
    "CNY-RUB": "🇨🇳",
    "AED-RUB": "🇦🇪",
    "THB-RUB": "🇹🇭"
}

FINANCE_EMOJIS = {
    "Золото": "👑",
    "Нефть Brent": "🛢️",
    "S&P 500": "📈",
    "NASDAQ": "📊",
    "Индекс МосБиржи": "🇷🇺",
    "EUR-USD": "🇺🇸",
    "USD-BYN": "🇧🇾",
    "USD-KZT": "🇰🇿",
    "USD-UAH": "🇺🇦"
}

CRYPTO_EMOJIS = {
    "BTC": "₿",
    "ETH": "⧫",
    "XRP": "✕",
    "BNB": "Ƀ",
    "SOL": "☀️",
    "DOGE": "🐶",
    "TRX": "🎭",
    "USDC": "💵",
    "ADA": "₳",
    "TONCOIN": "💎",
    "SHIB": "柴",
    "PEPE": "🐸",
    "MATIC": "🟪",
    "LINK": "🔗",
    "LTC": "⚡",
    "AVAX": "🏔️",
    "DOT": "🌐"
}

DEFAULT_EMOJIS = {
    'currency': '💱',
    'finance': '🌐',
    'crypto': '🪙'
}


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
            return f"{label}:    0.00%"  # Статичная ширина

        if is_crypto:
            arrow = "🟢" if number > 0 else "🔻"
        else:
            arrow = "▲" if number > 0 else "▼"

        formatted_number = f"{abs(number):5.2f}%"
        return f"{label}: {arrow} {formatted_number}"

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
        logger.debug(f"Formatting line for {name} with value={value}, 1h={change_1h}, 1d={change_1d}, 1w={change_1w}")

        changes = []
        for label, change in [("h", change_1h), ("d", change_1d), ("w", change_1w)]:
            formatted = self._format_change(label, change, is_crypto)
            if formatted:
                changes.append(formatted)

        # Горизонтальное выравнивание с фиксированными пробелами
        changes_str = "     " + "   ".join(changes) if changes else ""

        return f"{emoji} {name}: <code>{value}</code>\n{changes_str}\n"

    def format_currency_block(self, rates: Dict[str, Dict[str, Any]]) -> str:
        if not rates:
            logger.warning("Нет данных для блока валют")
            return "❌ Нет данных о курсах ЦБ РФ.\n"

        lines = ["<b>💰 Курсы ЦБ РФ:</b>\n"]
        for pair, data in rates.items():
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
        return "".join(lines) + "\n" if len(lines) > 1 else ""

    def format_financial_block(self, data: Dict[str, Dict[str, Any]]) -> str:
        if not data:
            logger.warning("Нет данных для финансовых инструментов")
            return "❌ Нет данных о финансовых инструментах.\n"

        lines = ["<b>📊 Финансовые инструменты:</b>\n"]
        for ticker, entry in data.items():
            value = entry.get("value")
            if value is None:
                continue
            name = TICKER_NAMES.get(ticker, ticker)
            lines.append(self._format_line(
                name=name,
                value=self._format_number(value),
                change_1h=entry.get("change_1h"),
                change_1d=entry.get("change_1d"),
                change_1w=entry.get("change_1w"),
                emoji=EmojiResolver.get_finance_emoji(name),
                is_crypto=False
            ))
        return "".join(lines) + "\n" if len(lines) > 1 else ""

    def format_crypto_block(self, data: Dict[str, Dict[str, Any]]) -> str:
        if not data:
            logger.warning("Нет данных для криптовалют")
            return "❌ Нет данных о криптовалютах.\n"

        lines = ["<b>💎 Криптовалюты к $:</b>\n"]
        for code, entry in data.items():
            value = entry.get("value")
            if value is None:
                continue
            precision = 2 if code == "BTC" else 4
            rounded = self._round(value, precision)
            formatted_value = self._format_number(rounded)
            lines.append(self._format_line(
                name=code,
                value=formatted_value,
                change_1h=entry.get("change_1h"),
                change_1d=entry.get("change_1d"),
                change_1w=entry.get("change_1w"),
                emoji=EmojiResolver.get_crypto_emoji(code),
                is_crypto=True
            ))
        return "".join(lines)


def create_telegram_message(
    cbr_rates: Dict[str, Dict[str, Any]],
    finance_data: Dict[str, Dict[str, Any]],
    crypto_data: Dict[str, Dict[str, Any]]
) -> str:
    logger.info("Создание Telegram-сообщения")
    date_str, time_str = TimeUtils.get_moscow_time()
    header = f"<b>🚓 {date_str}</b> 🕒 Upd: <code>{time_str} МСК</code>\n\n"

    formatter = Formatter()
    blocks = [
        formatter.format_currency_block(cbr_rates),
        formatter.format_financial_block(finance_data),
        formatter.format_crypto_block(crypto_data)
    ]

    footer = '🚓 <a href="https://t.me/currency_patrol">ФинПатруль</a> | #USD #BTC #курс_рубля'
    message = header + "".join(block for block in blocks if block.strip()) + "\n" + footer
    logger.info("Сообщение Telegram сформировано")
    return message

