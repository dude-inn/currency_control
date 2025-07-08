import logging
from logging.handlers import RotatingFileHandler
from service.settings import BASE_DIR


# Очищаем файл all_logs.log при старте программы
all_logs_path = f'{BASE_DIR}/service/logs/all_logs.log'
with open(all_logs_path, 'w'):
    pass  # Просто открываем файл в режиме записи, чтобы очистить его

# Формат логов
log_format = '%(asctime)s - %(levelname)s - %(name)s - %(message)s'

# Создаем форматтер с заданным форматом
formatter = logging.Formatter(log_format)

# Создаем обработчик для всех логов
all_logs_handler = RotatingFileHandler(all_logs_path, maxBytes=10000000, backupCount=3)
all_logs_handler.setLevel(logging.DEBUG)
all_logs_handler.setFormatter(formatter)  # Применяем форматтер к обработчику

# Создаем обработчик только для логов уровня INFO
info_logs_handler = RotatingFileHandler(f'{BASE_DIR}/service/logs/info_logs.log', maxBytes=10000000, backupCount=3)
info_logs_handler.setLevel(logging.INFO)
info_logs_handler.setFormatter(formatter)  # Применяем форматтер к обработчику

# Создаем логгер
logger = logging.getLogger('my_logger')
logger.setLevel(logging.DEBUG)

# Добавляем оба обработчика к логгеру
logger.addHandler(all_logs_handler)
logger.addHandler(info_logs_handler)


class InfoFilter(logging.Filter):
    def filter(self, record):
        return record.levelno == logging.INFO


# Применяем фильтр к обработчику info_logs_handler
info_logs_handler.addFilter(InfoFilter())
