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
BOT_NOTIFY_USER_ID = os.getenv("BOT_NOTIFY_USER_ID", "8105768964")
DEFAULT_NOTIFY_USER_ID = int(BOT_NOTIFY_USER_ID)

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
with open(keyword_file_path, encoding="utf-8") as file:
    keywords = [line.strip().lower() for line in file if line.strip()]

# Бизнес-логика
async def main() -> None:
    notify_user_ids = set()
    if DEFAULT_NOTIFY_USER_ID:
        notify_user_ids.add(DEFAULT_NOTIFY_USER_ID)

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
            notify_user_ids.add(sender_id)
            logging.info(f"Пользователь {sender_id} активировал уведомления")
            await event.respond("Привет!🖐🏻\n\nЭтот бот будет пересылать тебе сообщения о новых вакансиях по маркетингу")

        @client.on(events.NewMessage())
        async def forward_to_bot(event: events.NewMessage.Event):
            text = (event.raw_text or "").lower()
            if text and any(keyword in text for keyword in keywords):
                message_id = event.message.id
                chat = await event.get_chat()
                chat_name = (
                    getattr(chat, "username", None)
                    or getattr(chat, "title", None)
                    or str(event.chat_id)
                )
                logging.info(f"Получено сообщение {message_id} из {chat_name}")
                await event.message.forward_to("me")
                logging.info(f"Сообщение переслано в избранное")
                for notify_user_id in notify_user_ids:
                    await bot.send_message(entity=notify_user_id, message="Получено новое сообщение")


        print("🚀 Forwarder запущен.")
        logging.info("Forwarder запущен")
        await asyncio.gather(
            client.run_until_disconnected(),
            bot.run_until_disconnected(),
        )

# Запуск
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except ForbiddenError:
        logging.info("Нарушение настроек приватности")
    except (KeyboardInterrupt, SystemExit):
        logging.info("Клиент отключен")
