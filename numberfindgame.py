import asyncio
import logging
import random
import sys
import os

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.client.session.aiohttp import AiohttpSession
from aiohttp import web # Render uxlamasligi uchun

# ---------------------------------------------------
# TOKENINGIZNI SHU YERGA QO'YING
API_TOKEN = 'T5688843517:AAEfwhH7PDQeqm2b_dcbh5cAWyl00F3QkvQ'
# ---------------------------------------------------

logging.basicConfig(level=logging.INFO)

# Botni sozlash
# Agar PythonAnywhere bo'lsa Proxy ishlatamiz, bo'lmasa yo'q
if 'PYTHONANYWHERE_DOMAIN' in os.environ:
    session = AiohttpSession(proxy="http://proxy.server:3128")
    bot = Bot(token=API_TOKEN, session=session)
else:
    bot = Bot(token=API_TOKEN)

dp = Dispatcher()
games = {}
scores = {}

# --- TUGMALAR ---
menu_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Men topaman 👤"), KeyboardButton(text="Bot topsin 🤖")],
        [KeyboardButton(text="Hisob 📊")]
    ],
    resize_keyboard=True
)

javob_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Kattaroq ⬆️"), KeyboardButton(text="Kichikroq ⬇️")],
        [KeyboardButton(text="Topdingiz ✅")]
    ],
    resize_keyboard=True
)

# --- YORDAMCHI FUNKSIYA ---
def get_score_text(user_id):
    if user_id not in scores: scores[user_id] = {'user': 0, 'bot': 0}
    u = scores[user_id]['user']
    b = scores[user_id]['bot']
    text = f"📊 JAMI HISOB:\n\n👤 Siz: {u}\n🤖 Bot: {b}\n\n"
    if u > b: text += "Hozircha SIZ yutyapsiz! 🏆"
    elif b > u: text += "Hozircha BOT yutyapti! 😈"
    else: text += "Kuchlar teng! 🤝"
    return text

# --- XANDLERLAR ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Salom! Son topish o'yini.", reply_markup=menu_kb)

@dp.message(F.text == "Hisob 📊")
async def show_score(message: types.Message):
    await message.answer(get_score_text(message.from_user.id), reply_markup=menu_kb)

@dp.message(F.text == "Men topaman 👤")
async def user_guess_mode(message: types.Message):
    user_id = message.from_user.id
    games[user_id] = {'holat': 'user_topadi', 'son': random.randint(1, 100)}
    await message.answer("Men son o'yladim. Topingchi!", reply_markup=types.ReplyKeyboardRemove())

@dp.message(F.text == "Bot topsin 🤖")
async def bot_guess_mode(message: types.Message):
    user_id = message.from_user.id
    games[user_id] = {'holat': 'bot_topadi', 'min': 1, 'max': 100}
    await message.answer("Son o'ylang, men topaman!", reply_markup=javob_kb)
    await bot_tahmin_qilish(message, user_id)

async def bot_tahmin_qilish(message, user_id):
    data = games[user_id]
    tahmin = (data['min'] + data['max']) // 2
    data['tahmin'] = tahmin
    await message.answer(f"Siz o'ylagan son: {tahmin}mi?", reply_markup=javob_kb)

@dp.message(F.text.in_({"Kattaroq ⬆️", "Kichikroq ⬇️", "Topdingiz ✅"}))
async def process_bot_guess(message: types.Message):
    user_id = message.from_user.id
    if user_id not in games: return
    javob = message.text
    data = games[user_id]
    
    if javob == "Topdingiz ✅":
        if user_id not in scores: scores[user_id] = {'user': 0, 'bot': 0}
        scores[user_id]['bot'] += 1
        await message.answer(f"Topdim! 😎 Son: {data['tahmin']}\n\n1 ochko menga!", reply_markup=menu_kb)
        await message.answer(get_score_text(user_id))
        del games[user