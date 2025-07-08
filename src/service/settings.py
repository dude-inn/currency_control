import os
from dotenv import load_dotenv
import pytz


DEBUG = False

SERVICE_DIR = os.getcwd()
BASE_DIR = os.path.dirname(SERVICE_DIR)
STATICFILES_DIRS = BASE_DIR + '/static'
LOGO_DIRS = STATICFILES_DIRS + '/logo'

load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')

TINKOFF_TOKEN = os.getenv('TINKOFF_TOKEN')
ACCOUNT_ID = os.getenv('ACCOUNT_ID')
LIVECOINWATCH_API = os.getenv('LIVECOINWATCH_API')

TELEGRAM_CHANNEL_ID = "@currency_patrol"
if DEBUG is True:
    TELEGRAM_CHANNEL_ID = "@test_mix38"

API_KEY = os.getenv('API_KEY')
API_SECRET = os.getenv('API_SECRET')

format_string = '%Y-%m-%d %H:%M:%S'

moscow_tz = pytz.timezone('Europe/Moscow')

# Форматирование и локализация
LOCALE_SETTINGS = {
    'locale': 'ru_RU.UTF-8',
    'decimal_places': 2,
    'date_format': '%d.%m.%Y',
    'time_format': '%H:%M %d.%m.%Y',
    'datetime_format': '%Y-%m-%dT%H:%M:%S%z'
}

# Эмодзи и символы
EMOJI = {
    'flags': {
        'USD': '🇺🇸',
        'EUR': '🇪🇺',
        'GBP': '🇬🇧',
        'CNY': '🇨🇳',
        'BYN': '🇧🇾',
        'CHF': '🇨🇭',  # Швейцарский франк
        'AED': '🇦🇪',  # Дирхам ОАЭ
        'THB': '🇹🇭',  # Тайский бат
        'KZT': '🇰🇿',  # Казахстанский тенге
    },
    'crypto': {
        'BTC': '₿',
        'ETH': '⟠',
        'SOL': '◎',
        'TON': '🔹',
        'USDT': '💵',
        'BNB': 'ⓑ',
        'XRP': '✕',
        'DOGE': '🐶'
    },
    'change': {
        'up': "🟢",
        'down': "🔴",
        'neutral': "➖"
    },
    'sections': {
        'oil': '🛢',
        'indices': '📊',
        'crypto': '🪙',
        'bank': '🏦',
        'clock': '⏱'
    }
}

# Текстовые шаблоны
MESSAGES = {
    'header': "{bank} <b>Актуальные курсы валют и криптовалют на {date}</b>\n\n",
    'sections': {
        'cbr': "{bank} <b>Курсы ЦБ РФ:</b>\n",
        'crypto': "\n{crypto} <b>Криптовалюты (к USD):</b>\n",
        'oil': "\n{oil} <b>Цены на нефть:</b>\n",
        'indices': "\n{indices} <b>Фондовые индексы:</b>\n"
    },
    'rate_lines': {
        'cbr': "{flag} {curr}: <b>{value} RUB</b> ({change}п) {icon}\n",
        'crypto': "{emoji} {crypto}: <b>{price}</b> ({change}%) {icon}\n",
        'oil': "• Brent: <b>{price} USD/барр</b>\n",
        'index': "• {name}: <b>{price}</b> ({change}п, {percent}%) {icon}\n"
    },
    'update_time': "{clock} <i>Обновлено: {time} (МСК)</i>\n",
    'errors': {
        'no_data': "⚠ Не удалось получить данные о курсах",
        'api_error': "⚠ Ошибка при запросе данных из API"
    }
}

# Настройки данных
DATA_SETTINGS = {
    'fiat_currencies': ['USD', 'EUR', 'GBP', 'CNY', 'BYN', 'CHF', 'AED', 'THB', 'KZT'],
    'main_cryptos': ['BTC', 'ETH', 'BNB', 'SOL', 'XRP'],
    'secondary_cryptos': ['USDT', 'TON', 'DOGE'],
    'indices': {
        '^GSPC': 'S&P 500',
        '^IXIC': 'NASDAQ'
    },
    'crypto_base_currency': 'USD'
}

# API Endpoints
API_ENDPOINTS = {
    'alpha_vantage': {
        'oil': "https://www.alphavantage.co/query?function=BRENT&interval=daily&apikey={api_key}",
        'stocks': "https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={api_key}"
    },
    'cbr': "https://www.cbr-xml-daily.ru/daily_json.js",
    'crypto': "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,solana,the-open-network,tether,binancecoin,ripple,dogecoin&vs_currencies={base_currency}&include_24hr_change=true"
}

# Настройки планировщика
SCHEDULER_CONFIG = {
    'main_post': {
        'hour': 8,
        'minute': 0,
        'timezone': 'Europe/Moscow'
    },
    'updates': {
        'interval': 5,  # minutes
        'start': {'hour': 8, 'minute': 5},
        'end': {'hour': 7, 'minute': 57}
    },
    'debug': {
        'first_run_delay': 3,  # seconds
        'update_interval': 1  # minutes
    }
}
