import json
from database import Database
from service import logger


def fix_escaped_data_in_db():
    """
    Исправляет данные в базе, удаляя лишнее экранирование.
    """
    db = Database()
    # Получаем все записи из таблицы messages
    db.cursor.execute("SELECT id, data FROM messages")
    rows = db.cursor.fetchall()

    for row_id, data in rows:
        try:
            # Проверяем, является ли data строкой
            if isinstance(data, str):
                # Убираем лишнее экранирование
                fixed_data = data.replace('\\"', '"')
                # Преобразуем строку JSON в словарь
                parsed_data = json.loads(fixed_data)
                # Преобразуем обратно в JSON-строку (без лишнего экранирования)
                corrected_data = json.dumps(parsed_data)

                # Обновляем запись в базе
                db.cursor.execute(
                    "UPDATE messages SET data = ? WHERE id = ?",
                    (corrected_data, row_id)
                )
                db.conn.commit()
                logger.info(f"Исправлена запись с id={row_id}")
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка при исправлении данных для записи с id={row_id}: {e}")
        except Exception as e:
            logger.error(f"Неожиданная ошибка для записи с id={row_id}: {e}")

    logger.info("Все данные успешно исправлены.")
