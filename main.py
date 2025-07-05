import asyncio
import os
from telethon import TelegramClient, events
from telethon.errors import ForbiddenError
from telethon.sessions import StringSession
import logging
from dotenv import load_dotenv
import re
from typing import Iterable

load_dotenv()
STRING_SESSION = os.getenv("STRING_SESSION")
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
# Логирование
logging.basicConfig(
    filename="job_bot.log",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

# Список источников: username, numeric ID
# TODO 1: Не пересылает из групп
TARGET_CHATS = ["me", "https://t.me/+2FhJUyyxdjA3Mjky"]

# Задаем путь к файлам для запуска на любой ОС
current_dir = os.path.dirname(os.path.abspath(__file__))
print(current_dir)
keyword_file_path = os.path.join(current_dir, "keywords.txt")
source_file_path = os.path.join(current_dir, "source_chats.txt")
target_file_path = os.path.join(current_dir, "target_chats.txt")

# Читаем файл с ключевыми словами построчно
with open(keyword_file_path) as file:
    keywords = [line.strip() for line in file]

# Читаем файл с источниками
with open(source_file_path) as source:
    source_chats = [line.strip() for line in source]

with open(target_file_path) as target_file:
    target_chats = [line.strip() for line in target_file]

def search_key_in_text(text: str, key_list: Iterable[str]) -> bool:
    """
    Проверяет, содержит ли `text` хотя бы одно слово из `keywords`.
    Если да — печатает весь текст и возвращает True.
    Если нет — ничего не выводит и возвращает False.

    text – произвольная строка (может быть многострочной).
    key_list – список/кортеж/любой итерируемый объект с ключевыми словами.

    Поиск нечувствителен к регистру и учитывает только полные слова.
    """
    # Готовим регулярное выражение вида r"\b(?:слово1|слово2|...)\b"
    # экранируем спецсимволы
    escaped = map(re.escape, key_list)
    # объединяем через «или»
    pattern = r"\b(?:{})\b".format("|".join(escaped))
    if re.search(pattern, text, flags=re.IGNORECASE):
        print(text)
        return True
    return False


# Бизнес-логика
async def main() -> None:
    # создаём клиент и логинимся (при первом запуске спросит код + пароль 2FA)
    async with TelegramClient(StringSession(os.getenv("STRING_SESSION")), API_ID, API_HASH) as client:
        if client.is_connected():
            print("Connected")
            logging.info("Подключение к клиенту выполнено успешно")

        @client.on(events.NewMessage(chats=source_chats))
        async def forward_to_me(event: events.NewMessage.Event) -> None:
            """
            Обработчик: любое новое сообщение → «Saved Messages» владельца бота.
            Сервисные сообщения (join/leave и т. п.) Telethon сюда не шлёт по умолчанию.
            """
            message_id = event.message.id
            chat_name = event.chat.username
            message = event.message.message
            if search_key_in_text(message, keywords):
                print(message)
                for target in target_chats:
                    await event.message.forward_to(target)
                    # TODO 2: Разобраться с дублированием логов
                    logging.info(f"Получено сообщение {message_id} из {chat_name}")

        print("🚀 Forwarder запущен.")
        logging.info("Forwarder запущен")
        await client.run_until_disconnected()

# Запуск
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except ForbiddenError:
        logging.info("Нарушение настроек приватности")
    except (KeyboardInterrupt, SystemExit):
        print("👋 До встречи!")
        logging.info("Клиент отключен")
