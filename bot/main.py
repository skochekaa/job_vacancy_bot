import os
import sqlite3
import re
import asyncio
from dotenv import load_dotenv
from telethon import TelegramClient, events
import logging

# 📥 Загрузка переменных окружения
load_dotenv()

api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
source_chats = os.getenv("SOURCE_CHATS").split(",")
target_chats = os.getenv("TARGET_CHATS").split(",")

# ✅ Плюс-слова или фразы (регулярки)
KEYWORDS = [
    r'\bpython\b',
    r'\bjunior\b',
    r'удал[её]н\w*',
]

# ❌ Минус-слова или фразы (регулярки)
EXCLUDE_PATTERNS = [
    r'\bsenior\b',
    r'\bmiddle\b',
    r'\bfull[\s-]?stack\b'
    r'не\s+удал[её]н\w*',
    r'без\s+удал[её]н\w*'
]

# 📦 Подключение к SQLite
db_path = os.path.join(os.path.dirname(__file__), 'parser_db.sqlite')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS parsed_messages (
        message_id INTEGER,
        chat_id TEXT,
        PRIMARY KEY (message_id)
    )
''')
conn.commit()

# 📝 Логирование
logging.basicConfig(
    filename='job_bot.log',
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
)

# 🔌 Telegram клиент
client = TelegramClient('session', api_id, api_hash)

@client.on(events.NewMessage(chats=source_chats))
async def handler(event):
    message = event.message
    chat_id = str(event.chat_id)
    message_id = message.id
    text = message.message or ''

    # Уже обработано?
    cursor.execute(
        'SELECT 1 FROM parsed_messages WHERE message_id = ? AND chat_id = ?',
        (message_id, chat_id)
    )
    if cursor.fetchone():
        return

    text_lower = text.lower()

    # ❌ Минус-фразы
    for pattern in EXCLUDE_PATTERNS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            logging.info(f"[СКИП] ❌ Минус-фраза в {message_id}")
            return

    # ✅ Плюс-фразы
    if any(re.search(pattern, text_lower, re.IGNORECASE) for pattern in KEYWORDS):
        for target in target_chats:
            try:
                await client.send_message(target, f"💼 Вакансия:\n\n{text}")
                logging.info(f"[ОТПРАВЛЕНО] ✅ {message_id} -> {target}")
            except Exception as e:
                logging.error(f"[ОШИБКА] {message_id} -> {target}: {e}")
        cursor.execute(
            'INSERT INTO parsed_messages (message_id, chat_id) VALUES (?, ?)',
            (message_id, chat_id)
        )
        conn.commit()
    else:
        logging.info(f"[СКИП] 🚫 Нет ключей в {message_id}")

async def main():
    client.start()
    logging.info("🚀 Бот запущен")
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
