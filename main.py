import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.types import Message
from dotenv import load_dotenv
import openai as openai_lib
from questions import questions

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_KEY")

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Создание бота и диспетчера
bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

# Настройка ключа OpenAI
openai_lib.api_key = OPENAI_KEY

# Словарь для хранения ответов пользователей
user_answers = {}

@dp.message(lambda message: message.text == "/start")
async def start(message: Message):
    user_answers[message.from_user.id] = []
    await message.answer("Привет! Я задам тебе несколько вопросов, чтобы создать твой AI-портрет. Начнем?")
    await ask_question(message.from_user.id, message)

async def ask_question(user_id, message):
    answers = user_answers[user_id]
    if len(answers) < len(questions):
        await message.answer(questions[len(answers)])
    else:
        await message.answer("Генерирую твой AI-портрет…")
        await generate_portrait(user_id, message)

@dp.message()
async def collect_answers(message: Message):
    user_id = message.from_user.id
    if user_id not in user_answers:
        user_answers[user_id] = []
    user_answers[user_id].append(message.text)
    await ask_question(user_id, message)

async def generate_portrait(user_id, message):
    answers = user_answers[user_id]
    prompt = "Создай психологический портрет человека на основе его ответов: " + "; ".join(answers)
    try:
        response = await openai_lib.ChatCompletion.acreate(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        ai_text = response.choices[0].message["content"]
        await message.answer(f"Вот твой AI-портрет:\n\n{ai_text}")
    except Exception as e:
        await message.answer(f"⚠️ Ошибка при создании портрета:\n{e}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(dp.start_polling(bot))
