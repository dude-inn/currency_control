import aiohttp
import asyncio
from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass
from service.logger import logger
from service.settings import LIVECOINWATCH_API

# Конфигурационные константы
BASE_URL = "https://api.livecoinwatch.com"
REQUEST_DELAY = 0.5  # Задержка между запросами в секундах
CRYPTOCURRENCIES = [
    "BTC", "ETH", "XRP", "BNB", "SOL", "DOGE", "TRX", "ADA",
    "HYPE", "TONCOIN", "PEPE", "MATIC", "LINK", "LTC", "AVAX", "DOT"
]
DEFAULT_CURRENCY = "USD"


@dataclass
class CoinData:
    code: str
    price: Optional[float]
    currency: str = DEFAULT_CURRENCY


class CryptoAPI:
    """Класс для работы с API криптовалют."""

    def __init__(self, api_key: str = LIVECOINWATCH_API):
        self.api_key = api_key
        self.session = None
        self.headers = {
            "content-type": "application/json",
            "x-api-key": self.api_key
        }

    async def __aenter__(self):
        """Инициализация асинхронного контекста."""
        self.session = aiohttp.ClientSession(headers=self.headers)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Завершение асинхронного контекста."""
        if self.session:
            await self.session.close()

    async def fetch_coin_price(self, coin_code: str) -> CoinData:
        """С дополнительной защитой от ошибок"""
        try:
            url = f"{BASE_URL}/coins/single"
            payload = {"code": coin_code.upper(), "currency": DEFAULT_CURRENCY}

            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    rate = data.get("rate")
                    if rate is not None:
                        try:
                            price = round(float(rate), 6)
                            return CoinData(code=coin_code, price=price)
                        except (TypeError, ValueError) as e:
                            logger.error(f"Ошибка округления для {coin_code}: {e}")
        except Exception as e:
            logger.error(f"Ошибка запроса {coin_code}: {str(e)}")

        return CoinData(code=coin_code, price=None)


async def fetch_all_prices(coins: List[str] = CRYPTOCURRENCIES) -> Dict[str, Optional[float]]:
    """Получает цены для списка криптовалют."""
    logger.debug("Запрос цен криптовалют")

    async with CryptoAPI() as api:
        tasks = [api.fetch_coin_price(coin) for coin in coins]
        results = await asyncio.gather(*tasks)
        await asyncio.sleep(REQUEST_DELAY)  # Глобальная задержка вместо индивидуальной

        return {coin.code: coin.price for coin in results if coin.price is not None}


async def get_prices() -> Dict[str, Optional[float]]:
    """Основная функция для получения цен."""
    return await fetch_all_prices()


if __name__ == "__main__":
    async def main():
        prices = await get_prices()
        for coin, price in prices.items():
            print(f"{coin}: {price}")


    asyncio.run(main())
