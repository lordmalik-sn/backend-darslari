import asyncio
import logging
import random
import sys
import os

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiohttp import web # Render uxlamasligi uchun

# ---------------------------------------------------
# TOKENINGIZNI SHU YERGA QO'YING
API_TOKEN = '5688843517:AAEfwhH7PDQeqm2b_dcbh5cAWyl00F3QkvQ'
# ---------------------------------------------------

logging.basicConfig(level=logging.INFO)

# Botni yaratish
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Ma'lumotlarni saqlash
# games tuzilishi o'zgardi: endi 'urinishlar' degan sanagich ham bor
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

# --- YORDAMCHI FUNKSIYA (HISOB) ---
def get_score_text(user_id):
    if user_id not in scores: scores[user_id] = {'user': 0, 'bot': 0}
    u = scores[user_id]['user']
    b = scores[user_id]['bot']
    
    text = f"📊 JAMI G'ALABALAR:\n\n👤 Siz: {u} marta yutdingiz\n🤖 Bot: {b} marta yutdi\n\n"
    if u > b: text += "Hozircha SIZ oldindasiz! 🏆"
    elif b > u: text += "Hozircha BOT oldinda! 😈"
    else: text += "Kuchlar teng! 🤝"
    return text

# --- BOT BUYRUQLARI ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Salom! Son topish o'yini.\nKim kam urinishda toparkan?", reply_markup=menu_kb)

@dp.message(F.text == "Hisob 📊")
async def show_score(message: types.Message):
    await message.answer(get_score_text(message.from_user.id), reply_markup=menu_kb)

# ---------------------------------------------------------
# 1. USER TOPADI (Foydalanuvchi son topadi)
# ---------------------------------------------------------
@dp.message(F.text == "Men topaman 👤")
async def user_guess_mode(message: types.Message):
    user_id = message.from_user.id
    # 'urinishlar': 0 dan boshlaymiz
    games[user_id] = {
        'holat': 'user_topadi', 
        'son': random.randint(1, 100),
        'urinishlar': 0 
    }
    await message.answer("Men 1 dan 100 gacha son o'yladim.\nQani, nechtada toparkinsiz? (Son yozing)", reply_markup=types.ReplyKeyboardRemove())

@dp.message()
async def process_user_guess(message: types.Message):
    user_id = message.from_user.id
    
    # Tekshiruvlar
    if user_id not in games or games[user_id]['holat'] == 'bot_topadi': return
    if not message.text.isdigit(): return

    son = int(message.text)
    yashirin = games[user_id]['son']
    
    # Har safar son yozganda urinishni bittaga oshiramiz
    games[user_id]['urinishlar'] += 1
    urinish = games[user_id]['urinishlar']
    
    if son < yashirin:
        await message.answer(f"Mening sonim KATTAROQ ⬆️\n(Urinish: {urinish})")
    elif son > yashirin:
        await message.answer(f"Mening sonim KICHIKROQ ⬇️\n(Urinish: {urinish})")
    else:
        # Yutdi
        if user_id not in scores: scores[user_id] = {'user': 0, 'bot': 0}
        scores[user_id]['user'] += 1
        
        await message.answer(
            f"TOPDINGIZ! 🥳\n"
            f"Siz {yashirin} sonini **{urinish} ta** urinishda topdingiz!\n\n"
            f"1 ochko sizga!", 
            reply_markup=menu_kb,
            parse_mode="Markdown"
        )
        del games[user_id]

# ---------------------------------------------------------
# 2. BOT TOPADI (Bot son topadi)
# ---------------------------------------------------------
@dp.message(F.text == "Bot topsin 🤖")
async def bot_guess_mode(message: types.Message):
    user_id = message.from_user.id
    games[user_id] = {
        'holat': 'bot_topadi', 
        'min': 1, 
        'max': 100,
        'urinishlar': 0
    }
    await message.answer("Siz 1 dan 100 gacha son o'ylang.\nMen uni eng kam urinishda topishga harakat qilaman!", reply_markup=javob_kb)
    await bot_tahmin_qilish(message, user_id)

async def bot_tahmin_qilish(message, user_id):
    data = games[user_id]
    
    # Binary Search
    tahmin = (data['min'] + data['max']) // 2
    data['tahmin'] = tahmin
    
    # Botning urinishini sanaymiz
    data['urinishlar'] += 1
    
    await message.answer(
        f"Mening {data['urinishlar']}-taxminim: **{tahmin}**\nTo'g'rimi?", 
        reply_markup=javob_kb,
        parse_mode="Markdown"
    )

@dp.message(F.text.in_({"Kattaroq ⬆️", "Kichikroq ⬇️", "Topdingiz ✅"}))
async def process_bot_guess(message: types.Message):
    user_id = message.from_user.id
    if user_id not in games: return
    
    javob = message.text
    data = games[user_id]
    
    if javob == "Topdingiz ✅":
        if user_id not in scores: scores[user_id] = {'user': 0, 'bot': 0}
        scores[user_id]['bot'] += 1
        
        await message.answer(
            f"Yess! Men topdim! 😎\n"
            f"Son: {data['tahmin']}\n"
            f"Men buni **{data['urinishlar']} ta** urinishda topdim!\n\n"
            f"1 ochko menga!", 
            reply_markup=menu_kb,
            parse_mode="Markdown"
        )
        del games[user_id]
        
    elif javob == "Kattaroq ⬆️":
        data['min'] = data['tahmin'] + 1
        if data['min'] > data['max']: await message.answer("Aldamang! 🤔", reply_markup=menu_kb)
        else: await bot_tahmin_qilish(message, user_id)
        
    elif javob == "Kichikroq ⬇️":
        data['max'] = data['tahmin'] - 1
        if data['min'] > data['max']: await message.answer("Aldamang! 🤔", reply_markup=menu_kb)
        else: await bot_tahmin_qilish(message, user_id)

# --- SERVER UCHUN ---
async def health_check(request):
    return web.Response(text="Bot ishlab turibdi!")

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