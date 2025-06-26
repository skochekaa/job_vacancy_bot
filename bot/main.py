import os
import sqlite3
import re
import asyncio
import logging
from pathlib import Path
from dotenv import load_dotenv
from telethon import TelegramClient, events

# ──────────────────────────────────────────────────────────────────────────────
# 1. Загрузка переменных окружения (.env) – только API-ключи
# ──────────────────────────────────────────────────────────────────────────────
load_dotenv()
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")

# ──────────────────────────────────────────────────────────────────────────────
# 2. Функция чтения файлов-списков из корня проекта
#    • пропускает пустые строки и строки-комментарии (# …)
# ──────────────────────────────────────────────────────────────────────────────
ROOT_DIR = Path(__file__).resolve().parent.parent     # корневая папка проекта


def read_list_file(filename: str) -> list[str]:
    filepath = ROOT_DIR / filename
    with open(filepath, encoding="utf-8") as f:
        return [
            line.strip()
            for line in f
            if line.strip() and not line.strip().startswith("#")
        ]


# 3. Подгружаем списки из файлов
SOURCE_CHATS = read_list_file("source_chats.txt")          # каналы-источники
TARGET_CHATS = read_list_file("target_chats.txt")          # чаты-получатели
KEYWORDS = read_list_file("keywords.txt")                  # «плюс»-фразы/regex
EXCLUDE_PATTERNS = read_list_file("exclude_patterns.txt")  # «минус»-фразы/regex

# ──────────────────────────────────────────────────────────────────────────────
# 4. Настройка базы SQLite (храним обработанные message_id)
# ──────────────────────────────────────────────────────────────────────────────
DB_PATH = ROOT_DIR / "parser_db.sqlite"
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS parsed_messages (
        message_id INTEGER,
        chat_id TEXT,
        PRIMARY KEY (message_id)
    )
    """
)
conn.commit()

# ──────────────────────────────────────────────────────────────────────────────
# 5. Логирование
# ──────────────────────────────────────────────────────────────────────────────
logging.basicConfig(
    filename=ROOT_DIR / "job_bot.log",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

# ──────────────────────────────────────────────────────────────────────────────
# 6. Telegram-клиент
# ──────────────────────────────────────────────────────────────────────────────
client = TelegramClient("session", API_ID, API_HASH)


@client.on(events.NewMessage(chats=SOURCE_CHATS))
async def handler(event):
    """
    Обрабатываем новые сообщения из SOURCE_CHATS:
      • игнорируем, если уже в БД
      • отбрасываем, если содержит любую «минус»-фразу
      • пересылаем, если содержит хотя бы одну «плюс»-фразу
    """
    msg_id = event.message.id
    chat_id = str(event.chat_id)
    text = event.message.message or ""

    # Уже обработано?
    cursor.execute(
        "SELECT 1 FROM parsed_messages WHERE message_id = ? AND chat_id = ?",
        (msg_id, chat_id),
    )
    if cursor.fetchone():
        return

    text_lower = text.lower()

    # Минус-фразы
    if any(re.search(pat, text_lower, re.IGNORECASE) for pat in EXCLUDE_PATTERNS):
        logging.info(f"[СКИП] ❌ минус-фраза в {msg_id}")
        return

    # Плюс-фразы
    if any(re.search(pat, text_lower, re.IGNORECASE) for pat in KEYWORDS):
        for target in TARGET_CHATS:
            try:
                await client.send_message(target, f"💼 Вакансия:\n\n{text}")
                logging.info(f"[OK] {msg_id} → {target}")
            except Exception as exc:
                logging.error(f"[ОШИБКА] {msg_id} → {target}: {exc}")
        cursor.execute(
            "INSERT INTO parsed_messages (message_id, chat_id) VALUES (?, ?)",
            (msg_id, chat_id),
        )
        conn.commit()
    else:
        logging.info(f"[СКИП] 🚫 нет ключей в {msg_id}")


async def main():
    client.start()                       # без await – start() не coroutine
    logging.info("🚀 Бот запущен")
    await client.run_until_disconnected()


if __name__ == "__main__":
    asyncio.run(main())
