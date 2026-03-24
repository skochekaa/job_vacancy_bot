import asyncio
import os
from telethon import TelegramClient, events
from telethon.errors import ForbiddenError
import logging
from dotenv import load_dotenv


load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

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

sender = ""
# Бизнес-логика
async def main() -> None:
    # создаём клиент и логинимся (при первом запуске спросит номер телефона в международном формате + пароль 2FA)
    async with (
        TelegramClient("session", API_ID, API_HASH) as client,
        TelegramClient("bot_session", API_ID, API_HASH) as bot,
                ):
        await bot.start(bot_token=BOT_TOKEN)
        if client.is_connected() and bot.is_connected():
            logging.info("Подключение к клиенту и боту выполнено успешно")

        @bot.on(events.NewMessage(pattern=r"/start"))
        async def start(event: events.NewMessage.Event):
            sender_id = event.sender_id
            print(sender_id)
            await event.respond("Привет!🖐🏻\n\nЭтот бот будет пересылать тебе сообщения о новых вакансиях по маркетингу")

        @client.on(events.NewMessage())
        async def forward_to_bot(event):
            if any(w in event.raw_text.lower() for w in keywords):
                message_id = event.message.id
                chat_name = event.chat.username
                message = event.message
                logging.info(f"Получено сообщение {message_id} из {chat_name}")
                await event.message.forward_to("me")
                logging.info(f"Сообщение переслано в избранное")
                await bot.send_message(entity=8105768964, message="Получено новое сообщение")


        print("🚀 Forwarder запущен.")
        logging.info("Forwarder запущен")
        await client.run_until_disconnected()
        await bot.run_until_disconnected()

# Запуск
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except ForbiddenError:
        logging.info("Нарушение настроек приватности")
    except (KeyboardInterrupt, SystemExit):
        logging.info("Клиент отключен")
