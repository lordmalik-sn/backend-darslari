import asyncio
import logging
import random
import sys
import os

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiohttp import web

# ---------------------------------------------------
# SIZNING TOKENINGIZ
API_TOKEN = '8390998199:AAHnym6ikj7oLn2jICxIC4y2wjgnb-04HOc'
# ---------------------------------------------------

logging.basicConfig(level=logging.INFO)

# Botni sozlash
if 'PYTHONANYWHERE_DOMAIN' in os.environ:
    from aiogram.client.session.aiohttp import AiohttpSession
    session = AiohttpSession(proxy="http://proxy.server:3128")
    bot = Bot(token=API_TOKEN, session=session)
else:
    bot = Bot(token=API_TOKEN)

dp = Dispatcher()

# Xotira
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

# --- YORDAMCHI FUNKSIYALAR ---
def get_score_text(user_id):
    if user_id not in scores: scores[user_id] = {'user': 0, 'bot': 0}
    u = scores[user_id]['user']
    b = scores[user_id]['bot']
    return f"📊 JAMI G'ALABALAR:\n👤 Siz: {u}\n🤖 Bot: {b}"

# --- ASOSIY MENYU ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "Salom! Yangi qoidalar bo'yicha o'ynaymiz:\n"
        "❗️ **Faqat 4 ta urinishda topsangizgina ochko beriladi!**\n"
        "Boshlaymizmi? 👇", 
        reply_markup=menu_kb,
        parse_mode="Markdown"
    )

@dp.message(F.text.startswith("Hisob"))
async def show_score(message: types.Message):
    await message.answer(get_score_text(message.from_user.id), reply_markup=menu_kb)

# ---------------------------------------------------------
# 1. USER TOPADI (Siz topasiz)
# ---------------------------------------------------------
@dp.message(F.text.startswith("Men topaman"))
async def user_guess_mode(message: types.Message):
    user_id = message.from_user.id
    games[user_id] = {
        'holat': 'user_topadi', 
        'son': random.randint(1, 100),
        'urinishlar': 0 
    }
    await message.answer("Men 1 dan 100 gacha son o'yladim.\n4 ta urinishda topa olasizmi?", reply_markup=types.ReplyKeyboardRemove())

@dp.message()
async def process_user_guess(message: types.Message):
    user_id = message.from_user.id
    
    # Generic tekshiruvlar
    if "Bot topsin" in message.text:
         await bot_guess_mode(message)
         return

    if user_id not in games:
        if message.text.isdigit():
            await message.answer("O'yin faol emas. Menyudan tanlang 👇", reply_markup=menu_kb)
        return

    if games[user_id]['holat'] == 'bot_topadi':
        await message.answer("Hozir men topyapman, tugmalarni bosing!", reply_markup=javob_kb)
        return

    if not message.text.isdigit():
        await message.answer("Iltimos, faqat raqam yozing!")
        return

    son = int(message.text)
    yashirin = games[user_id]['son']
    games[user_id]['urinishlar'] += 1
    urinish = games[user_id]['urinishlar']
    
    if son < yashirin:
        await message.answer(f"Mening sonim KATTAROQ ⬆️\n(Urinish: {urinish})")
    elif son > yashirin:
        await message.answer(f"Mening sonim KICHIKROQ ⬇️\n(Urinish: {urinish})")
    else:
        # TOPDI! Endi ochko berishni tekshiramiz
        if urinish <= 4:
            if user_id not in scores: scores[user_id] = {'user': 0, 'bot': 0}
            scores[user_id]['user'] += 1
            xabar = f"TOPDINGIZ! 🥳\nSon: {yashirin}\nUrinish: {urinish} ta\n\n✅ **+1 OCHKO!** (4 tadan kam)"
        else:
            xabar = f"TOPDINGIZ! 🥳\nSon: {yashirin}\nUrinish: {urinish} ta\n\n❌ **OCHKO YO'Q** (4 tadan ko'p urinish)"

        await message.answer(xabar, reply_markup=menu_kb, parse_mode="Markdown")
        await message.answer(get_score_text(user_id))
        del games[user_id]

# ---------------------------------------------------------
# 2. BOT TOPADI (Bot topadi)
# ---------------------------------------------------------
@dp.message(F.text.startswith("Bot topsin"))
async def bot_guess_mode(message: types.Message):
    user_id = message.from_user.id
    games[user_id] = {
        'holat': 'bot_topadi', 
        'min': 1, 
        'max': 100,
        'urinishlar': 0
    }
    await message.answer("Siz 1 dan 100 gacha son o'ylang.\nMen 4 ta urinishda topishga harakat qilaman!", reply_markup=javob_kb)
    await bot_tahmin_qilish(message, user_id)

async def bot_tahmin_qilish(message, user_id):
    if user_id not in games:
        await message.answer("Xatolik bo'ldi. Boshqatdan boshlaylik.", reply_markup=menu_kb)
        return

    data = games[user_id]
    tahmin = (data['min'] + data['max']) // 2
    data['tahmin'] = tahmin
    data['urinishlar'] += 1
    
    await message.answer(
        f"Mening {data['urinishlar']}-taxminim: **{tahmin}**\nTo'g'rimi?", 
        reply_markup=javob_kb,
        parse_mode="Markdown"
    )

@dp.message(F.text.in_({"Kattaroq ⬆️", "Kichikroq ⬇️", "Topdingiz ✅"}))
async def process_bot_guess(message: types.Message):
    user_id = message.from_user.id
    
    if user_id not in games:
        await message.answer("⚠️ O'yin to'xtagan. Qaytadan 'Bot topsin' ni bosing.", reply_markup=menu_kb)
        return
    
    if games[user_id]['holat'] != 'bot_topadi':
        await message.answer("Hozir siz topishingiz kerak! Son yozing.", reply_markup=types.ReplyKeyboardRemove())
        return

    javob = message.text
    data = games[user_id]
    
    if javob == "Topdingiz ✅":
        # Bot topdi. Ochko beramizmi?
        if data['urinishlar'] <= 4:
            if user_id not in scores: scores[user_id] = {'user': 0, 'bot': 0}
            scores[user_id]['bot'] += 1
            xabar = f"Yess! Men topdim! 😎\nSon: {data['tahmin']}\nUrinish: {data['urinishlar']} ta\n\n✅ **+1 OCHKO MENGA!**"
        else:
            xabar = f"Yess! Men topdim! 😎\nSon: {data['tahmin']}\nUrinish: {data['urinishlar']} ta\n\n❌ **OCHKO OLOLMADIM** (4 tadan ko'p)"
        
        await message.answer(xabar, reply_markup=menu_kb, parse_mode="Markdown")
        await message.answer(get_score_text(user_id))
        del games[user_id]
        
    elif javob == "Kattaroq ⬆️":
        data['min'] = data['tahmin'] + 1
        if data['min'] > data['max']:
            await message.answer("Aldamang! 🤔 Qaytadan o'ynaymiz.", reply_markup=menu_kb)
            del games[user_id]
        else:
            await bot_tahmin_qilish(message, user_id)
            
    elif javob == "Kichikroq ⬇️":
        data['max'] = data['tahmin'] - 1
        if data['min'] > data['max']:
            await message.answer("Aldamang! 🤔 Qaytadan o'ynaymiz.", reply_markup=menu_kb)
            del games[user_id]
        else:
            await bot_tahmin_qilish(message, user_id)

# --- SERVER ---
async def health_check(request): return web.Response(text="OK")
async def start_web_server():
    app = web.Application()
    app.router.add_get('/', health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

async def main():
    await start_web_server()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    if sys.platform == "win32": asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())