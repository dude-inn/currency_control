from typing import Optional, Dict, Any
from service.logger import logger
import json
from datetime import timedelta
from database import Database

from service.settings import THRESHOLDS, CHANGE_EMOJIS


def calculate_percentage_change(old_value: Optional[float], new_value: Optional[float]) -> Optional[float]:
    logger.debug(f'Old_value: {old_value}, new_value: {new_value}')
    if None in (old_value, new_value) or old_value == 0:
        return None

    change = ((new_value - old_value) / old_value) * 100
    return round(change, 2)


def _get_change_emoji(change: float, is_crypto: bool) -> str:
    emoji_set = CHANGE_EMOJIS["crypto"] if is_crypto else CHANGE_EMOJIS["default"]
    base_emoji = emoji_set["up"] if change > 0 else emoji_set["down"]

    if not is_crypto:
        return base_emoji

    abs_change = abs(change)
    if abs_change > 10:
        return base_emoji + (emoji_set["high_up"] if change > 0 else emoji_set["high_down"])
    if abs_change > 5:
        return base_emoji * 2
    return base_emoji


def format_change(value_now: float, value_then: float) -> Optional[str]:
    try:
        if value_now is None or value_then is None or value_then == 0:
            return None
        change = ((value_now - value_then) / value_then) * 100
        return f"{change:.2f}%"
    except Exception as e:
        logger.warning(f"Ошибка при вычислении изменения: {e}")
        return None


def check_threshold(value: Optional[float], threshold: int, threshold_emoji: str) -> str:
    if value is None or threshold == 0:
        return ""

    lower_bound = (value // threshold) * threshold
    upper_bound = lower_bound + threshold

    return "" if lower_bound < value < upper_bound else threshold_emoji


def _round_crypto_value(value: Optional[float], currency: str) -> Optional[float]:
    if value is None:
        return None

    try:
        return round(float(value), 2 if currency == "BTC" else 4)
    except (TypeError, ValueError) as e:
        logger.error(f"Ошибка округления для {currency}: {e}")
        return value


def get_changes_for_intervals(ticker: str, current_value: float, source_type: str) -> Dict[str, Optional[float]]:
    db = Database()
    return {
        "change_1h": db.get_change(ticker, current_value, source_type, timedelta(hours=1)),
        "change_1d": db.get_change(ticker, current_value, source_type, timedelta(days=1)),
        "change_1w": db.get_change(ticker, current_value, source_type, timedelta(weeks=1)),
    }


def process_data(new_data: Dict[str, Any],
                 old_data: Dict[str, Any],
                 is_crypto: bool = False) -> Dict[str, Dict[str, Any]]:
    processed = {}

    if isinstance(old_data, str):
        try:
            old_data = json.loads(old_data)
        except json.JSONDecodeError:
            old_data = {}

    if not isinstance(old_data, dict):
        old_data = {}

    for currency, new_val_raw in new_data.items():
        try:
            if new_val_raw is None:
                continue

            # если в new_val_raw уже словарь — достаём .get("value")
            if isinstance(new_val_raw, dict):
                new_value = new_val_raw.get("value")
            else:
                new_value = new_val_raw

            if new_value is None:
                continue

            old_value = None
            if isinstance(old_data.get(currency), dict):
                old_value = old_data[currency].get("value")

            change = calculate_percentage_change(old_value, new_value)

            source_type = "crypto" if is_crypto else "finance"
            if currency in ["USD-RUB", "EUR-RUB"]:
                source_type = "cbr"

            processed[currency] = {
                "value": _round_crypto_value(new_value, currency) if is_crypto else new_value,
                "change": format_change(new_value, old_value),
                "threshold_emoji": check_threshold(new_value, *THRESHOLDS.get(currency, (0, ""))),
            }

            interval_changes = get_changes_for_intervals(currency, new_value, source_type)
            processed[currency].update(interval_changes)

        except Exception as e:
            logger.error(f"Ошибка обработки {currency}: {e}")
            continue

    return processed
