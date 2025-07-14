import aiohttp
import asyncio
from typing import Dict, Optional, List
from service.logger import logger
from service.settings import (
    LIVECOINWATCH_API,
    API_ENDPOINTS,
    CRYPTO_SETTINGS,
    CRYPTO_ALWAYS_SHOW,
)


async def fetch_all_coins() -> List[dict]:
    """Запрашивает все монеты с LiveCoinWatch"""
    url = API_ENDPOINTS['livecoinwatch']['coins_list']
    async with aiohttp.ClientSession(headers={
        "x-api-key": LIVECOINWATCH_API,
        "content-type": "application/json"
    }) as session:
        payload = {
            "currency": CRYPTO_SETTINGS['default_currency'],
            "sort": "rank",
            "order": "ascending",
            "offset": 0,
            "limit": CRYPTO_SETTINGS['max_coins']
        }
        async with session.post(url, json=payload) as resp:
            if resp.status != 200:
                logger.error(f"Ошибка запроса: {resp.status}")
                return []
            data = await resp.json()
            return data


async def get_prices() -> Dict[str, Dict[str, Optional[float]]]:
    logger.debug("Запрашиваем список криптовалют")
    coins = await fetch_all_coins()
    if not coins:
        return {}

    result = {
        "always": {},
        "daily_spikes": {},
        "hourly_spikes": {}
    }

    threshold_daily = CRYPTO_SETTINGS['threshold_daily']
    threshold_hourly = CRYPTO_SETTINGS['threshold_hourly']

    daily_candidates = []
    hourly_candidates = []

    for c in coins:
        code = c.get("code")
        rate = c.get("rate", 0)
        delta = c.get("delta", {})
        change_1h = delta.get("hour")
        change_1d = delta.get("day")
        change_1w = delta.get("week")

        entry = {
            "value": round(rate, 6),
            "change_1h": change_1h,
            "change_1d": change_1d,
            "change_1w": change_1w,
        }

        if code in CRYPTO_ALWAYS_SHOW:
            result["always"][code] = entry

        if change_1d is not None and abs(change_1d) >= threshold_daily:
            daily_candidates.append((abs(change_1d), code, entry))

        if change_1h is not None and abs(change_1h) >= threshold_hourly:
            hourly_candidates.append((abs(change_1h), code, entry))

    # оставить только топ-5 по величине
    daily_candidates.sort(reverse=True)
    hourly_candidates.sort(reverse=True)

    for _, code, entry in daily_candidates[:5]:
        result["daily_spikes"][code] = entry

    for _, code, entry in hourly_candidates[:5]:
        result["hourly_spikes"][code] = entry

    logger.info(
        f"Готовы данные: always={len(result['always'])}, daily_spikes={len(result['daily_spikes'])}, hourly_spikes={len(result['hourly_spikes'])}"
    )
    return result


if __name__ == "__main__":
    async def main():
        data = await get_prices()
        for section, coins in data.items():
            print(f"--- {section} ---")
            for code, entry in coins.items():
                print(f"{code}: {entry}")
    asyncio.run(main())
