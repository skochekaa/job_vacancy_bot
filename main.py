import asyncio
import os
import re
from telethon import TelegramClient, events
from telethon.errors import ForbiddenError
import logging
from dotenv import load_dotenv


load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
CLIENT_ID = int(os.getenv("CLIENT_ID"))

# Логирование
logging.basicConfig(
    filename="job_bot.log",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

# Задаем путь к файлам для запуска на любой ОС
current_dir = os.path.dirname(os.path.abspath(__file__))
keyword_file_path = os.path.join(current_dir, "keywords.txt")
spot_keys_file_path = os.path.join(current_dir, "stop_keys.txt")

# Читаем файл с ключевыми словами построчно
with open(keyword_file_path, encoding="utf-8") as file:
    keywords = [line.strip().lower() for line in file if line.strip()]

with open(spot_keys_file_path, encoding="utf-8") as stop_file:
    stop_keys = [line.strip().lower() for line in stop_file if line.strip()]


def compile_keyword_patterns(words: list[str]) -> list[re.Pattern]:
    return [re.compile(rf"(?<!\w){re.escape(word)}(?!\w)") for word in words]


def has_any_keyword(text: str, patterns: list[re.Pattern]) -> bool:
    return any(pattern.search(text) for pattern in patterns)


keyword_patterns = compile_keyword_patterns(keywords)
stop_key_patterns = compile_keyword_patterns(stop_keys)


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
            logging.info(f"Пользователь {sender_id} активировал уведомления")
            await event.respond("Привет!🖐🏻\n\nЭтот бот будет пересылать тебе сообщения о новых вакансиях по маркетингу")

        @client.on(events.NewMessage())
        async def forward_to_bot(event: events.NewMessage.Event):
            text = event.raw_text.lower()
            if has_any_keyword(text, keyword_patterns) and not has_any_keyword(text, stop_key_patterns):
                message_id = event.message.id
                chat_nickname = event.chat.username
                logging.info(f"Получено сообщение {message_id} из {chat_nickname}")
                message = event.message.message or ""
                message_entities = event.message.entities or None
                chat_name = event.sender.title
                await event.message.forward_to("me")
                logging.info(f"Сообщение переслано в избранное")
                await bot.send_message(
                    entity=CLIENT_ID,
                    message=f"{message}\n\nПолучено из: {chat_name}(@{chat_nickname})",
                    formatting_entities=message_entities,
                    link_preview=True
                )
                logging.info(f"Сообщение переслано в бот")


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
