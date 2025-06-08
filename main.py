import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.types import Message
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from openai import AsyncOpenAI
from dotenv import load_dotenv
from questions import questions

from fastapi import FastAPI, Request
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

# --- Загрузка переменных ---
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_KEY")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # например: https://your-app-name.onrender.com

# --- Настройка логов ---
logging.basicConfig(level=logging.INFO)

# --- Создание бота и диспетчера ---
bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())
openai = AsyncOpenAI(api_key=OPENAI_KEY)

user_answers = {}

# --- FastAPI приложение ---
app = FastAPI()

# --- Вебхук FastAPI обработчик ---
@app.on_event("startup")
async def on_startup():
    await bot.set_webhook(WEBHOOK_URL)
    logging.info(f"Webhook set to {WEBHOOK_URL}")

@app.on_event("shutdown")
async def on_shutdown():
    await bot.delete_webhook()
    logging.info("Webhook deleted")

# --- Webhook обработчик запросов от Telegram ---
async def handler(request: Request):
    return await SimpleRequestHandler(dispatcher=dp, bot=bot).handle(request)

app.post("/")(handler)  # POST-запросы от Telegram приходят сюда

# --- Логика бота ---

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
        response = await openai.chat.completions.create(
            model="gpt-4-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        ai_text = response.choices[0].message.content
        await message.answer(f"Вот твой AI-портрет:\n\n{ai_text}")
    except Exception as e:
        await message.answer(f"⚠️ Ошибка при создании портрета:\n{e}")
