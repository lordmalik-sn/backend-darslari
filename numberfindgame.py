import asyncio
import logging
import random
import sys
import os

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.client.session.aiohttp import AiohttpSession
from aiohttp import web

# ---------------------------------------------------
API_TOKEN = 'TO8390998199:AAHnym6ikj7oLn2jICxIC4y2wjgnb-04HOc'
# ---------------------------------------------------

logging.basicConfig(level=logging.INFO)

# 1. Botni sozlash (Universal)
if 'PYTHONANYWHERE_DOMAIN' in os.environ:
    session = AiohttpSession(proxy="http://proxy.server:3128")
    bot = Bot(token=API_TOKEN, session=session)
else:
    bot = Bot(token=API_TOKEN)

dp = Dispatcher()

# O'yin ma'lumotlari
games = {}

# NATIJALAR JADVALI (Yangi)
# Tuzilishi: {user_id: {'user': 0, 'bot': 0}}
scores = {} 

# --- TUGMALAR ---
menu_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Men topaman 👤"), KeyboardButton(text="Bot topsin 🤖")],
        [KeyboardButton(text="Hisob 📊")] # Yangi tugma
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

# --- YORDAMCHI FUNKSIYA: HISOBNI TEKSHIRISH ---
def get_score_text(user_id):
    if user_id not in scores:
        scores[user_id] = {'user': 0, 'bot': 0}
    
    u = scores[user_id]['user']
    b = scores[user_id]['bot']
    
    text = f"📊 JAMI HISOB:\n\n👤 Siz: {u}\n🤖 Bot: {b}\n\n"
    if u > b:
        text += "Hozircha SIZ yutyapsiz! 🏆"
    elif b > u:
        text += "Hozircha BOT yutyapti! 😈"
    else:
        text += "Kuchlar teng! 🤝"
    return text

# --- XANDLERLAR ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Salom! Son topish o'yini.", reply_markup=menu_kb)

# HISOBNI KO'RISH
@dp.message(F.text == "Hisob 📊")
async def show_score(message: types.Message):
    text = get_score_text(message.from_user.id)
    await message.answer(text, reply_markup=menu_kb)

# 1. USER TOPADI
@dp.message(F.text == "Men topaman 👤")
async def user_guess_mode(message: types.Message):
    user_id = message.from_user.id
    games[user_id] = {'holat': 'user_topadi', 'son': random.randint(1, 100)}
    await message.answer("Men son o'yladim. Topingchi!", reply_markup=types.ReplyKeyboardRemove())

# 2. BOT TOPADI
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

# --- BOT TOPGANDA ---
@dp.message(F.text.in_({"Kattaroq ⬆️", "Kichikroq ⬇️", "Topdingiz ✅"}))
async def process_bot_guess(message: types.Message):
    user_id = message.from_user.id
    if user_id not in games: return
    
    javob = message.text
    data = games[user_id]
    
    if javob == "Topdingiz ✅":
        # Bot yutdi, hisobni yangilaymiz
        if user_id not in scores: scores[user_id] = {'user': 0, 'bot': 0}
        scores[user_id]['bot'] += 1
        
        await message.answer(
            f"Topdim! 😎 Son: {data['tahmin']}\n\n1 ochko menga!", 
            reply_markup=menu_kb
        )
        # Natijani ko'rsatamiz
        await message.answer(get_score_text(user_id))
        del games[user_id]
        
    elif javob == "Kattaroq ⬆️":
        data['min'] = data['tahmin'] + 1
        if data['min'] > data['max']: await message.answer("Aldamang!", reply_markup=menu_kb)
        else: await bot_tahmin_qilish(message, user_id)
    elif javob == "Kichikroq ⬇️":
        data['max'] = data['tahmin'] - 1
        if data['min'] > data['max']: await message.answer("Aldamang!", reply_markup=menu_kb)
        else: await bot_tahmin_qilish(message, user_id)

# --- USER TOPGANDA ---
@dp.message()
async def process_user_guess(message: types.Message):
    user_id = message.from_user.id
    if user_id not in games or games[user_id]['holat'] == 'bot_topadi': return
    if not message.text.isdigit(): return

    son = int(message.text)
    yashirin = games[user_id]['son']
    
    if son < yashirin: await message.answer("Kattaroq ⬆️")
    elif son > yashirin: await message.answer("Kichikroq ⬇️")
    else:
        # User yutdi, hisobni yangilaymiz
        if user_id not in scores: scores[user_id] = {'user': 0, 'bot': 0}
        scores[user_id]['user'] += 1
        
        await message.answer(
            f"TOPDINGIZ! 🥳 Son: {yashirin}\n\n1 ochko sizga!", 
            reply_markup=menu_kb
        )
        # Natijani ko'rsatamiz
        await message.answer(get_score_text(user_id))
        del games[user_id]

# --- SERVERNI USHLAB TURISH ---
async def health_check(request):
    return web.Response(text="Bot ishlmoqda")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

async def main():
    print("Bot ishga tushdi...")
    await start_web_server()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())