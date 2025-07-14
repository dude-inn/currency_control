import asyncio
from typing import Dict, Optional, List
from dataclasses import dataclass
import yfinance as yf

from service.logger import logger
from service.settings import YAHOO_FINANCIAL_ASSETS

# Константы по умолчанию
DEFAULT_DELAY = 0.5
DEFAULT_PERIOD = "1d"
DEFAULT_INTERVAL = "5m"


@dataclass(frozen=True)
class Asset:
    ticker: str
    name: str


class AssetFetcher:
    def __init__(
        self,
        assets: Optional[List[Asset]] = None,
        period: str = DEFAULT_PERIOD,
        interval: str = DEFAULT_INTERVAL,
        delay: float = DEFAULT_DELAY
    ):
        self.assets = assets or self._load_assets_from_settings()
        self.period = period
        self.interval = interval
        self.delay = delay

    def _load_assets_from_settings(self) -> List[Asset]:
        return [Asset(a["ticker"], a["name"]) for a in YAHOO_FINANCIAL_ASSETS]

    async def get_all_prices(self) -> Dict[str, Optional[float]]:
        logger.info("Запуск получения данных с Yahoo Finance")
        tasks = [self._fetch_price(asset) for asset in self.assets]
        results = await asyncio.gather(*tasks)

        await asyncio.sleep(self.delay)

        return {
            asset.name: price
            for asset, price in results
        }

    async def _fetch_price(self, asset: Asset) -> tuple[Asset, Optional[float]]:
        try:
            ticker_data = yf.Ticker(asset.ticker)
            history = ticker_data.history(period=self.period, interval=self.interval)

            if not history.empty and not history['Close'].empty:
                price = round(float(history['Close'].iloc[-1]), 2)
                return asset, price

            logger.warning(f"Нет данных для {asset.name}")
            return asset, None

        except Exception as e:
            logger.error(f"Ошибка получения {asset.name} ({asset.ticker}): {e}")
            return asset, None


# Публичный интерфейс модуля
async def get_prices() -> Dict[str, Optional[float]]:
    result = {}
    for asset in YAHOO_FINANCIAL_ASSETS:
        ticker = asset['ticker']
        name = asset['name']
        try:
            data = yf.Ticker(ticker).history(period="1d")
            if data.empty:
                logger.warning(f"{ticker}: нет данных от Yahoo")
                result[name] = None
                continue

            last_price = round(data['Close'].iloc[-1], 2)
            result[name] = last_price

        except Exception as e:
            logger.error(f"{ticker}: ошибка запроса — {e}")
            result[name] = None
    return result


# Тестовый запуск
if __name__ == "__main__":
    async def test():
        logger.info("Тестирование модуля get_yahoo_data")
        prices = await get_prices()
        for name, price in prices.items():
            if price is not None:
                print(f"{name}: {price}")
            else:
                logger.warning(f"Нет данных для {name}")

    asyncio.run(test())
