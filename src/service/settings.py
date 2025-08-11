import os
from dotenv import load_dotenv
import pytz

load_dotenv()

DEBUG = False

SERVICE_DIR = os.getcwd()
BASE_DIR = os.path.dirname(SERVICE_DIR)
STATICFILES_DIRS = BASE_DIR + '/static'
LOGO_DIRS = STATICFILES_DIRS + '/logo'

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')
TINKOFF_TOKEN = os.getenv('TINKOFF_TOKEN')
ACCOUNT_ID = os.getenv('ACCOUNT_ID')
LIVECOINWATCH_API = os.getenv('LIVECOINWATCH_API')
API_KEY = os.getenv('API_KEY')
API_SECRET = os.getenv('API_SECRET')
CRYPTOPANIC_TOKEN = os.getenv('CRYPTOPANIC_TOKEN')
YANDEX_TRANSLATE_API_KEY = os.getenv('YANDEX_TRANSLATE_API_KEY')
YANDEX_FOLDER_ID = os.getenv('YANDEX_FOLDER_ID')


TELEGRAM_CHANNEL_ID = "@currency_patrol" if not DEBUG else "@test_mix38"

moscow_tz = pytz.timezone('Europe/Moscow')
DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'

# 📊 Yahoo Finance тикеры
YAHOO_FINANCIAL_ASSETS = [
    {"ticker": "GC=F",      "name": "Золото"},
    {"ticker": "BZ=F",      "name": "Нефть Brent"},
    {"ticker": "EURUSD=X",  "name": "EUR-USD"}
]

ALLOWED_FINANCIAL_TICKERS = {asset["ticker"] for asset in YAHOO_FINANCIAL_ASSETS}

# 💎 Криптовалюты
CRYPTO_DISPLAY = {
    'always_show': ['BTC', 'ETH', 'TONCOIN', 'BNB', 'SOL'],
    'on_move_show': ['XRP', 'DOGE', 'ADA', 'MATIC', 'LINK', 'LTC', 'AVAX', 'DOT'],
    'threshold_percent': 5.0
}

CRYPTO_API = {
    "base_url": "https://api.livecoinwatch.com",
    "request_delay": 0.5,
    "default_currency": "USD",
    "max_coins": 100
}

CRYPTO_SETTINGS = {
    "default_currency": "USD",
    "max_coins": 200,
    "top_n": 5,
    "always_show": ["BTC", "ETH", "USDT", "BNB", "TONCOIN", "SOL"],
    "threshold_daily": 1.0,   # % — порог изменения за день для попадания в "🔥 Рывок за день"
    "threshold_hourly": 1.0   # % — порог изменения за час для попадания в "🚀 Рывок за час"
}

# Обязательные монеты для публикации (всегда)
CRYPTO_ALWAYS_SHOW = ["BTC", "ETH", "TONCOIN", "SOL", "BNB"]

# Монеты, которые показываются только при значительном движении
CRYPTO_ON_MOVE_SHOW = ["XRP", "DOGE", "ADA", "MATIC", "LINK", "LTC", "AVAX", "DOT"]

# Порог для "значительного движения" (в %)
CRYPTO_MOVE_THRESHOLD = 5.0

# 📅 Планировщик
SCHEDULER_SETTINGS = {
    "first_message_delay_seconds": 10,
    "edit_interval_minutes": 3,
    "daily_post_time": {"hour": 0, "minute": 0},
    "stop_edit_time": {"hour": 23, "minute": 59},
    "last_edit_time": {"hour": 23, "minute": 57},
    "debug": {
        "first_run_delay_seconds": 10,
        "edit_interval_seconds": 30,
        "stop_edit_after_minutes": 5
    }
}

DATABASE_SETTINGS = {
    "db_path": "data.db",
    "cleanup_days_threshold": 8,
    "min_valid_length": 50
}

# 📈 Пороговые значения
THRESHOLDS = {
    "USD-RUB": (5, "🏅"),
    "BTC": (1000, "🏅")
}

# 🔼/🔻 эмодзи
CHANGE_EMOJIS = {
    "crypto": {
        "up": "🔼",
        "down": "🔻",
        "high_up": "🚀",
        "high_down": "💥"
    },
    "default": {
        "up": "▲",
        "down": "▼"
    }
}

# 🌐 Центробанк РФ
CBR_API_URL = "https://www.cbr-xml-daily.ru/daily_json.js"

# 💲 Фиатные валюты
FIAT_CURRENCIES = [
    "USD", "EUR", "CNY", "BYN", "CHF", "AED", "THB", "KZT"
]

SPECIAL_NOMINALS = {
    "THB": 10
}

# 📆 Локализация
LOCALE_SETTINGS = {
    'locale': 'ru_RU.UTF-8',
    'decimal_places': 2,
    'date_format': '%d.%m.%Y',
    'time_format': '%H:%M %d.%m.%Y',
    'datetime_format': '%Y-%m-%dT%H:%M:%S%z'
}

# 🪙 Названия тикеров
TICKER_NAMES = {
    "GOLD": "Золото",
    "BZ=F": "Нефть Brent",
    "IMOEX.ME": "Индекс МосБиржи",
    "EURUSD=X": "EUR-USD",
    "USDBYN=X": "USD-BYN",
    "USDKZT=X": "USD-KZT",
    "USDUAH=X": "USD-UAH"
}

# 🇺🇸 Флаги валют
CURRENCY_FLAGS = {
    "USD-RUB": "🇺🇸",
    "EUR-RUB": "🇪🇺",
    "CNY-RUB": "🇨🇳"
}

# 💰 Эмодзи инструментов
FINANCE_EMOJIS = {
    "Золото": "👑",
    "Нефть Brent": "🛢️",
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
    "ADA": "₳",
    "TONCOIN": "💎",
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

# Разрешённые пары валют
ALLOWED_CURRENCY_PAIRS = {"USD-RUB", "EUR-RUB", "CNY-RUB"}

# 📲 API Endpoints
API_ENDPOINTS = {
    'alpha_vantage': {
        'oil': "https://www.alphavantage.co/query?function=BRENT&interval=daily&apikey={api_key}",
        'stocks': "https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={api_key}"
    },
    'cbr': CBR_API_URL,
    'livecoinwatch': {
        'coins_list': "https://api.livecoinwatch.com/coins/list"
    }
}

REQUIRED_CURRENCIES = [
    "USD", "EUR", "CNY"
]
