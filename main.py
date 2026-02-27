import asyncio
import os
from telethon import TelegramClient, events
from telethon.errors import ForbiddenError
import logging
from dotenv import load_dotenv


load_dotenv()
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")

# Логирование
logging.basicConfig(
    filename="job_bot.log",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

# Задаем путь к файлам для запуска на любой ОС
current_dir = os.path.dirname(os.path.abspath(__file__))
keyword_file_path = os.path.join(current_dir, "keywords.txt")

# Читаем файл с ключевыми словами построчно
with open(keyword_file_path) as file:
    keywords = [line.strip() for line in file]

# Бизнес-логика
async def main() -> None:
    # создаём клиент и логинимся (при первом запуске спросит номер телефона в международном формате + пароль 2FA)
    async with TelegramClient("session", API_ID, API_HASH) as client:
        if client.is_connected():
            print("Connected")
            logging.info("Подключение к клиенту выполнено успешно")

        @client.on(events.NewMessage(chats="ezio_test"))
        async def forward_to_me(event):
            if any(w in event.raw_text for w in keywords):
                message_id = event.message.id
                chat_name = event.chat.username
                message = event.message.message
                logging.info(f"Получено сообщение {message_id} из {chat_name}")
                await event.message.forward_to("me")


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
