import asyncio
import aiohttp
from datetime import datetime
from deep_translator import YandexTranslator
from service.settings import (
    CRYPTOPANIC_TOKEN,
    YANDEX_TRANSLATE_API_KEY,
    YANDEX_FOLDER_ID,
)
from telegr.sender import send_telegram_message
from service.logger import logger

CRYPTOPANIC_API_URL = "https://cryptopanic.com/api/v1/posts/"
CHANNEL = "@test_mix38"


async def translate_text(text: str, target_lang="ru") -> str:
    """
    Переводит текст на указанный язык через Yandex Cloud Translate API.
    """
    try:
        translated = await asyncio.to_thread(
            YandexTranslator(
                api_key=YANDEX_TRANSLATE_API_KEY,
                folder_id=YANDEX_FOLDER_ID,
                source="en",
                target=target_lang,
            ).translate,
            text,
        )
        return translated
    except Exception as e:
        logger.error(f"Ошибка перевода Яндекс: {e}")
        return text


async def get_news_digest(when: str) -> str:
    """
    Возвращает текст новостей в формате Telegram-поста (HTML) с англ+рус.
    :param when: 'утро' или 'вечер'
    :return: str — готовый текст
    """
    params = {
        "auth_token": CRYPTOPANIC_TOKEN,
        "filter": "hot",
        "public": "true",
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(CRYPTOPANIC_API_URL, params=params) as resp:
                if resp.status != 200:
                    logger.error(f"CryptoPanic API вернул статус {resp.status}")
                    return ""
                data = await resp.json()
        except Exception as e:
            logger.error(f"Ошибка при запросе к CryptoPanic API: {e}")
            return ""

    posts = data.get("results", [])[:3]
    if not posts:
        logger.warning("Нет новостей из CryptoPanic")
        return ""

    now = datetime.now().strftime("%d.%m.%Y")
    header = f"🚓 <b>Главные новости крипторынка к {when} ({now}):</b>\n"

    lines = []
    total_chars = 0

    for post in posts:
        title_en = post.get("title", "Без заголовка")
        url = post.get("url", "")

        translated_title = await translate_text(title_en)
        total_chars += len(title_en)

        line = (
            f"— <a href=\"{url}\">{title_en}</a>\n"
            f"  ({translated_title})"
        )
        lines.append(line)

    logger.info(f"Переведено символов за запуск: {total_chars}")

    text = (
        header + "\n\n" + "\n\n".join(lines) + "\n\n👉 @currency_patrol"
    )
    return text


async def main():
    news_text = await get_news_digest("утру")  # или "вечер"
    if not news_text:
        print("⚠️ Нет новостей")
        return

    print("\n--- Сформированное сообщение ---\n")
    print(news_text)

    await send_telegram_message(news_text, CHANNEL)
    logger.info(f"✅ Новости опубликованы в {CHANNEL}")


if __name__ == "__main__":
    asyncio.run(main())
