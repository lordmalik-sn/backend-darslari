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
# TOKENINGIZNI SHU YERGA QO'YING
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
        [KeyboardButton(text="Hisob 📊"), KeyboardButton(text="Qoidalar 📜")]
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

# --- YANGI: UNVON ANIQLASH FUNKSIYASI ---
def get_rank(points):
    if points < 5: return "Yangi o'yinchi 👶"
    elif points < 10: return "Havaskor 👦"
    elif points < 20: return "Tajribali 😎"
    elif points < 50: return "Professional 🎯"
    else: return "KIBORG 🤖"

def get_score_text(user_id):
    if user_id not in scores: scores[user_id] = {'user': 0, 'bot': 0}
    u = scores[user_id]['user']
    b = scores[user_id]['bot']
    
    # Unvonni aniqlaymiz
    rank = get_rank(u)
    
    text = (
        f"📊 **NATIJALAR:**\n\n"
        f"👤 Siz: **{u}** ochko\n"
        f"🤖 Bot: **{b}** ochko\n\n"
        f"🎖 Sizning unvoningiz: **{rank}**\n"
    )
    
    # Keyingi darajaga qancha qoldi?
    if u < 5: text += f"Keyingi unvongacha: {5-u} ta g'alaba qoldi!"
    elif u < 10: text += f"Keyingi unvongacha: {10-u} ta g'alaba qoldi!"
    elif u < 20: text += f"Keyingi unvongacha: {20-u} ta g'alaba qoldi!"
    elif u < 50: text += f"Keyingi unvongacha: {50-u} ta g'alaba qoldi!"
    
    return text

# --- ASOSIY MENYU ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "Salom! Son topish o'yiniga xush kelibsiz.\n"
        "Maqsad: 'KIBORG' unvoniga yetish! 🤖\nBoshlaymizmi?", 
        reply_markup=menu_kb
    )

@dp.message(F.text == "Qoidalar 📜")
async def show_rules(message: types.Message):
    text = (
        "📜 **QOIDALAR:**\n\n"
        "1. 👤 **Siz topganda:** Agar 4 ta urinishda topsangiz +1 ochko.\n"
        "2. 🤖 **Bot topganda:** Agar bot 4 ta urinishda topsa, unga +1 ochko.\n\n"
        "🎖 **UNVONLAR:**\n"
        "0-4: Yangi o'yinchi 👶\n"
        "5-9: Havaskor 👦\n"
        "10-19: Tajribali 😎\n"
        "20-49: Professional 🎯\n"
        "50+: KIBORG 🤖"
    )
    await message.answer(text, parse_mode="Markdown", reply_markup=menu_kb)

@dp.message(F.text.startswith("Hisob"))
async def show_score(message: types.Message):
    await message.answer(get_score_text(message.from_user.id), parse_mode="Markdown", reply_markup=menu_kb)

# ---------------------------------------------------------
# 1. USER TOPADI
# ---------------------------------------------------------
@dp.message(F.text.startswith("Men topaman"))
async def user_guess_mode(message: types.Message):
    user_id = message.from_user.id
    games[user_id] = {'holat': 'user_topadi', 'son': random.randint(1, 100), 'urinishlar': 0}
    await message.answer("Men 1 dan 100 gacha son o'yladim.\n4 ta urinishda toping!", reply_markup=types.ReplyKeyboardRemove())

@dp.message()
async def process_user_guess(message: types.Message):
    user_id = message.from_user.id
    
    if "Bot topsin" in message.text: await bot_guess_mode(message); return

    if user_id not in games:
        if message.text.isdigit(): await message.answer("O'yin faol emas. Menyudan tanlang 👇", reply_markup=menu_kb)
        return

    if games[user_id]['holat'] == 'bot_topadi':
        await message.answer("Hozir men topyapman, tugmalarni bosing!", reply_markup=javob_kb)
        return

    if not message.text.isdigit():
        await message.answer("Faqat raqam yozing!")
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
        if urinish <= 4:
            if user_id not in scores: scores[user_id] = {'user': 0, 'bot': 0}
            scores[user_id]['user'] += 1
            xabar = f"TOPDINGIZ! 🥳\nSon: {yashirin}\nUrinish: {urinish} ta\n\n✅ **+1 OCHKO!**"
        else:
            xabar = f"TOPDINGIZ! 🥳\nSon: {yashirin}\nUrinish: {urinish} ta\n\n❌ **OCHKO YO'Q** (Ko'p urinish)"

        await message.answer(xabar, parse_mode="Markdown", reply_markup=menu_kb)
        await message.answer(get_score_text(user_id), parse_mode="Markdown")
        del games[user_id]

# ---------------------------------------------------------
# 2. BOT TOPADI
# ---------------------------------------------------------
@dp.message(F.text.startswith("Bot topsin"))
async def bot_guess_mode(message: types.Message):
    user_id = message.from_user.id
    games[user_id] = {'holat': 'bot_topadi', 'min': 1, 'max': 100, 'urinishlar': 0}
    await message.answer("Siz son o'ylang. Men 4 ta urinishda topishga harakat qilaman!", reply_markup=javob_kb)
    await bot_tahmin_qilish(message, user_id)

async def bot_tahmin_qilish(message, user_id):
    if user_id not in games:
        await message.answer("Xatolik bo'ldi. Boshqatdan boshlaylik.", reply_markup=menu_kb)
        return

    data = games[user_id]
    tahmin = (data['min'] + data['max']) // 2
    data['tahmin'] = tahmin
    data['urinishlar'] += 1
    
    await message.answer(f"Mening {data['urinishlar']}-taxminim: **{tahmin}**\nTo'g'rimi?", reply_markup=javob_kb, parse_mode="Markdown")

@dp.message(F.text.in_({"Kattaroq ⬆️", "Kichikroq ⬇️", "Topdingiz ✅"}))
async def process_bot_guess(message: types.Message):
    user_id = message.from_user.id
    if user_id not in games:
        await message.answer("⚠️ O'yin to'xtagan. Qaytadan 'Bot topsin' ni bosing.", reply_markup=menu_kb)
        return
    if games[user_id]['holat'] != 'bot_topadi':
        await message.answer("Hozir siz topishingiz kerak!", reply_markup=types.ReplyKeyboardRemove())
        return

    javob = message.text
    data = games[user_id]
    
    if javob == "Topdingiz ✅":
        if data['urinishlar'] <= 4:
            if user_id not in scores: scores[user_id] = {'user': 0, 'bot': 0}
            scores[user_id]['bot'] += 1
            xabar = f"Yess! Topdim! 😎\nSon: {data['tahmin']}\nUrinish: {data['urinishlar']} ta\n\n✅ **+1 OCHKO MENGA!**"
        else:
            xabar = f"Yess! Topdim! 😎\nSon: {data['tahmin']}\nUrinish: {data['urinishlar']} ta\n\n❌ **OCHKO YO'Q** (Ko'p urinish)"
        
        await message.answer(xabar, parse_mode="Markdown", reply_markup=menu_kb)
        await message.answer(get_score_text(user_id), parse_mode="Markdown")
        del games[user_id]
        
    elif javob == "Kattaroq ⬆️":
        data['min'] = data['tahmin'] + 1
        if data['min'] > data['max']: await message.answer("Aldamang! 🤔", reply_markup=menu_kb); del games[user_id]
        else: await bot_tahmin_qilish(message, user_id)
            
    elif javob == "Kichikroq ⬇️":
        data['max'] = data['tahmin'] - 1
        if data['min'] > data['max']: await message.answer("Aldamang! 🤔", reply_markup=menu_kb); del games[user_id]
        else: await bot_tahmin_qilish(message, user_id)

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