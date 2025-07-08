import requests
from typing import Dict, Optional, Any
from dataclasses import dataclass
from service.logger import logger

# Конфигурационные константы
CBR_API_URL = "https://www.cbr-xml-daily.ru/daily_json.js"
REQUIRED_CURRENCIES = ["USD", "EUR", "CNY", "AED", "THB"]
SPECIAL_NOMINALS = {"THB": 10}  # Валюты с особым номиналом


@dataclass
class CurrencyRate:
    code: str
    name: str
    value: float
    nominal: int


class CBRService:
    """Сервис для работы с API Центробанка России."""

    def __init__(self, base_url: str = CBR_API_URL):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "CurrencyBot/1.0",
            "Accept": "application/json"
        })

    def fetch_currency_data(self) -> Optional[Dict[str, Any]]:
        """Получает актуальные курсы валют."""
        try:
            with self.session.get(self.base_url, timeout=10) as response:
                response.raise_for_status()
                logger.info("Данные ЦБ РФ успешно получены")
                return response.json()
        except requests.RequestException as e:
            logger.error(f"Ошибка запроса к ЦБ РФ: {str(e)}")
            return None

    @staticmethod
    def process_currency_data(data: Dict[str, Any]) -> Dict[str, CurrencyRate]:
        """Обрабатывает сырые данные от ЦБ РФ."""
        if not data or "Valute" not in data:
            logger.error("Неверный формат данных от ЦБ РФ")
            return {}

        result = {}
        for code in REQUIRED_CURRENCIES:
            if code not in data["Valute"]:
                logger.warning(f"Валюта {code} отсутствует в данных ЦБ")
                continue

            currency = data["Valute"][code]
            nominal = SPECIAL_NOMINALS.get(code, 1)
            rate = CurrencyRate(
                code=code,
                name=currency["Name"],
                value=round(currency["Value"] / nominal, 2),
                nominal=nominal
            )
            result[f"{code}-RUB"] = rate

        return result


def get_currency_rates() -> Dict[str, float]:
    """Получает и возвращает актуальные курсы валют."""
    service = CBRService()
    if raw_data := service.fetch_currency_data():
        processed = service.process_currency_data(raw_data)
        return {pair: rate.value for pair, rate in processed.items()}
    return {}


if __name__ == "__main__":
    from pprint import pprint

    rates = get_currency_rates()
    pprint(rates)
