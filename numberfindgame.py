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
API_TOKEN = '8390998199:AAHnym6ikj7oLn2jICxIC4y2wjgnb-04HOc'
# ---------------------------------------------------

logging.basicConfig(level=logging.INFO)

# Botni yaratish (Proxy tekshiruvi bilan)
if 'PYTHONANYWHERE_DOMAIN' in os.environ:
    from aiogram.client.session.aiohttp import AiohttpSession
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

# --- YORDAMCHI FUNKSIYALAR ---
def get_score_text(user_id):
    if user_id not in scores: scores[user_id] = {'user': 0, 'bot': 0}
    u = scores[user_id]['user']
    b = scores[user_id]['bot']
    return f"📊 JAMI G'ALABALAR:\n👤 Siz: {u}\n🤖 Bot: {b}"

# --- ASOSIY BUYRUQLAR ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Salom! O'yinni boshlash uchun tugmani tanlang 👇", reply_markup=menu_kb)

@dp.message(F.text == "Hisob 📊")
async def show_score(message: types.Message):
    await message.answer(get_score_text(message.from_user.id), reply_markup=menu_kb)

# ---------------------------------------------------------
# 1. USER TOPADI MODE
# ---------------------------------------------------------
@dp.message(F.text == "Men topaman 👤")
async def user_guess_mode(message: types.Message):
    user_id = message.from_user.id
    games[user_id] = {
        'holat': 'user_topadi', 
        'son': random.randint(1, 100),
        'urinishlar': 0 
    }
    await message.answer("Men 1 dan 100 gacha son o'yladim.\nTopishga harakat qiling! (Son yozing)", reply_markup=types.ReplyKeyboardRemove())

@dp.message()
async def process_user_guess(message: types.Message):
    user_id = message.from_user.id
    
    # 1. Agar bot raqam emas, shunchaki so'z eshitsa (va u buyruq bo'lmasa)
    if not message.text.isdigit():
        # Agar o'yin ketayotgan bo'lsa, ogohlantiramiz
        if user_id in games:
             await message.answer("Iltimos, faqat raqam yozing!")
        return

    # 2. Agar o'yin boshlanmagan bo'lsa (yoki bot esidan chiqargan bo'lsa)
    if user_id not in games:
        await message.answer("⚠️ O'yin faol emas. Iltimos, menyudan yangi o'yin tanlang.", reply_markup=menu_kb)
        return

    # 3. Agar bot hozir o'zi topish rejimida bo'lsa
    if games[user_id]['holat'] == 'bot_topadi':
        await message.answer("Hozir men topyapman, siz tugmalarni bosing!", reply_markup=javob_kb)
        return

    # O'yin mantig'i
    son = int(message.text)
    yashirin = games[user_id]['son']
    games[user_id]['urinishlar'] += 1
    urinish = games[user_id]['urinishlar']
    
    if son < yashirin:
        await message.answer(f"Mening sonim KATTAROQ ⬆️\n(Urinish: {urinish})")
    elif son > yashirin:
        await message.answer(f"Mening sonim KICHIKROQ ⬇️\n(Urinish: {urinish})")
    else:
        if user_id not in scores: scores[user_id] = {'user': 0, 'bot': 0}
        scores[user_id]['user'] += 1
        await message.answer(f"TOPDINGIZ! 🥳\nSon: {yashirin}\nUrinishlar: {urinish}\n\n1 ochko sizga!", reply_markup=menu_kb)
        del games[user_id]

# ---------------------------------------------------------
# 2. BOT TOPADI MODE
# ---------------------------------------------------------
@dp.message(F.text == "Bot topsin 🤖")
async def bot_guess_mode(message: types.Message):
    user_id = message.from_user.id
    games[user_id] = {'holat': 'bot_topadi', 'min': 1, 'max': 100, 'urinishlar': 0}
    await message.answer("Siz son o'ylang, men topaman!", reply_markup=javob_kb)
    await bot_tahmin_qilish(message, user_id)

async def bot_tahmin_qilish(message, user_id):
    if user_id not in games: return
    data = games[user_id]
    tahmin = (data['min'] + data['max']) // 2
    data['tahmin'] = tahmin
    data['urinishlar'] += 1
    await message.answer(f"Mening {data['urinishlar']}-taxminim: **{tahmin}**\nTo'g'rimi?", reply_markup=javob_kb, parse_mode="Markdown")

@dp.message(F.text.in_({"Kattaroq ⬆️", "Kichikroq ⬇️", "Topdingiz ✅"}))
async def process_bot_guess(message: types.Message):
    user_id = message.from_user.id
    
    # Agar bot o'yinni yo'qotib qo'ygan bo'lsa, jim turmaydi
    if user_id not in games:
        await message.answer("⚠️ O'yin uzilib qoldi. Qaytadan boshlaymiz.", reply_markup=menu_kb)
        return
    
    javob = message.text
    data = games[user_id]
    
    if javob == "Topdingiz ✅":
        if user_id not in scores: scores[user_id] = {'user': 0, 'bot': 0}
        scores[user_id]['bot'] += 1
        await message.answer(f"Topdim! 😎 Son: {data['tahmin']}\nUrinishlar: {data['urinishlar']}", reply_markup=menu_kb)
        del games[user_id]
    elif javob == "Kattaroq ⬆️":
        data['min'] = data['tahmin'] + 1
        if data['min'] > data['max']: await message.answer("G'alati... Siz son o'yladingizmi?", reply_markup=menu_kb)
        else: await bot_tahmin_qilish(message, user_id)
    elif javob == "Kichikroq ⬇️":
        data['max'] = data['tahmin'] - 1
        if data['min'] > data['max']: await message.answer("G'alati... Siz son o'yladingizmi?", reply_markup=menu_kb)
        else: await bot_tahmin_qilish(message, user_id)

# --- WEB SERVER ---
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