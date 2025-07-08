import telegram
from telegram.constants import ParseMode
from service.logger import logger
from service.settings import TELEGRAM_TOKEN

# Инициализация бота
bot = telegram.Bot(token=TELEGRAM_TOKEN)


async def send_telegram_message(message, chat_id):
    """
    Отправляет сообщение в Telegram чат.
    :return: message_id отправленного сообщения.
    """
    try:
        result = await bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True  # 🔇 Отключаем превью ссылок
        )
        return result.message_id
    except telegram.error.TelegramError as error:
        logger.error(f"Ошибка при отправке сообщения: {error}")
        return None


async def edit_telegram_message(message, chat_id, message_id):
    """
    Редактирует текстовое сообщение в Telegram чате.
    """
    try:
        result = await bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=message,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True  # 🔇 Отключаем превью ссылок
        )
        return result
    except telegram.error.TelegramError as error:
        logger.error(f"Ошибка при редактировании сообщения: {error}")
        return None


async def send_image(chat_id, image_path, caption=None):
    """
    Отправляет изображение в Telegram чат.
    :return: message_id отправленного сообщения.
    """
    try:
        with open(image_path, 'rb') as photo:
            result = await bot.send_photo(
                chat_id=chat_id,
                photo=photo,
                caption=caption,
                parse_mode=ParseMode.HTML
            )
        return result.message_id
    except telegram.error.TelegramError as error:
        logger.error(f"Ошибка при отправке изображения: {error}")
        return None


async def delete_message(chat_id, message_id):
    """
    Удаляет сообщение из Telegram чата.
    """
    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
        logger.info(f"Сообщение с ID {message_id} успешно удалено.")
    except telegram.error.TelegramError as error:
        logger.error(f"Ошибка при удалении сообщения: {error}")


async def edit_image_message(chat_id, old_message_id, new_image_path, new_caption=None):
    """
    Заменяет сообщение с изображением на новое.
    :return: message_id нового сообщения.
    """
    # Удаляем старое сообщение
    await delete_message(chat_id, old_message_id)

    # Отправляем новое сообщение
    new_message_id = await send_image(chat_id, new_image_path, new_caption)
    return new_message_id
