import os
import random
import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandObject
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.exceptions import TelegramBadRequest
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

# --- SOZLAMALAR ---
BOT_TOKEN = "8563862094:AAG2lGzaXjVa6qtvfTMBhGUlZ8mroK6bN9Q"
ADMIN_ID = 1022350478  # Admin (God Mode)

WEBHOOK_HOST = os.getenv("RENDER_EXTERNAL_URL", "https://mafia-bot-m8zh.onrender.com")
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"
PORT = int(os.getenv("PORT", 8080))

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

games = {}
user_db = {}

# --- GIF / MEDIA HAVOLALARI ---
GIFS = {
    "night": "https://media.giphy.com/media/l2Jhv955I4MpcMMhe/giphy.gif",      # Tun gif
    "day": "https://media.giphy.com/media/3o6Zt8A83pVR3M6A4U/giphy.gif",        # Kun gif
    "mafia_shot": "https://media.giphy.com/media/xT1R9LUBvA7R89q0eA/giphy.gif", # Otish gif
    "doctor_heal": "https://media.giphy.com/media/3o7TKSx0g7d3072224/giphy.gif",# Davolash gif
    "detective_check": "https://media.giphy.com/media/l41lFw05vM4S8d31C/giphy.gif" # Tekshirish gif
}

ROLES = {
    "mafia": {"title": "🕵️‍♂️ Mafiya", "desc": "Tunda yashirincha tinch aholini o'ldiradi."},
    "doctor": {"title": "🩺 Shifokor", "desc": "Tunda 1 kishini o'limdan saqlab qoladi."},
    "detective": {"title": "🔍 Komissar", "desc": "Tunda gumondorning rolini tekshiradi."},
    "civilian": {"title": "👨‍🌾 Tinch aholi", "desc": "Kunduzi muhokamada qatnashib, mafiyani topadi."}
}

def get_user_data(user_id):
    if user_id not in user_db:
        if user_id == ADMIN_ID:
            user_db[user_id] = {"coins": 999999, "diamonds": 999999, "cards": ["Jekpot", "Xaos"], "referrals": 0}
        else:
            user_db[user_id] = {"coins": 100, "diamonds": 0, "cards": [], "referrals": 0}
    return user_db[user_id]

# --- FOYDALANUVCHILARGA TANGA VA OLMOS BERISH (ADMIN ADMIN PANEL) ---
@dp.message(Command("addcoins"))
async def add_coins_handler(message: types.Message, command: CommandObject):
    if message.from_user.id != ADMIN_ID:
        return

    if not command.args:
        await message.answer("⚠️ Qanday ishlatish: `/addcoins ID_RAQAM SUMMA`\n*Misol:* `/addcoins 123456789 500`", parse_mode="Markdown")
        return

    try:
        args = command.args.split()
        target_id = int(args[0])
        amount = int(args[1])

        target_data = get_user_data(target_id)
        target_data["coins"] += amount

        await message.answer(f"✅ **Muvaffaqiyatli!**\nFoydalanuvchi (`{target_id}`) hisobiga **{amount} Tanga** qo'shildi!\nHozirgi balansi: **{target_data['coins']} 💰**", parse_mode="Markdown")
        
        try:
            await bot.send_message(target_id, f"🎁 **ADMIN TOMONIDAN HADIYA!**\nSizning hisobingizga **{amount} Tanga 💰** qo'shildi!")
        except Exception:
            pass
    except Exception:
        await message.answer("❌ Xatolik! ID va summani to'g'ri kiriting.\n*Misol:* `/addcoins 123456789 500`", parse_mode="Markdown")

@dp.message(Command("adddiamonds"))
async def add_diamonds_handler(message: types.Message, command: CommandObject):
    if message.from_user.id != ADMIN_ID:
        return

    if not command.args:
        await message.answer("⚠️ Qanday ishlatish: `/adddiamonds ID_RAQAM SUMMA`\n*Misol:* `/adddiamonds 123456789 5`", parse_mode="Markdown")
        return

    try:
        args = command.args.split()
        target_id = int(args[0])
        amount = int(args[1])

        target_data = get_user_data(target_id)
        target_data["diamonds"] += amount

        await message.answer(f"✅ **Muvaffaqiyatli!**\nFoydalanuvchi (`{target_id}`) hisobiga **{amount} Olmos** qo'shildi!\nHozirgi balansi: **{target_data['diamonds']} 💎**", parse_mode="Markdown")
        
        try:
            await bot.send_message(target_id, f"🎁 **ADMIN TOMONIDAN HADIYA!**\nSizning hisobingizga **{amount} Olmos 💎** qo'shildi!")
        except Exception:
            pass
    except Exception:
        await message.answer("❌ Xatolik! ID va summani to'g'ri kiriting.\n*Misol:* `/adddiamonds 123456789 5`", parse_mode="Markdown")

# --- HANDLERLAR ---
@dp.message(Command("start"))
async def start_handler(message: types.Message, command: CommandObject):
    user_id = message.from_user.id
    get_user_data(user_id)
    await message.answer(
        "🎭 **MAFIYA: DARK CITY BOTIGA XUSH KELIBSIZ!**\n\n"
        "📖 /info — Rollar katalogi\n"
        "👥 /ref — Do'stlarni taklif qilish\n"
        "👤 /profile — Balans va profil\n"
        "🛒 /shop — Do'kon\n"
        "🎲 /game — Guruhda o'yin boshlash",
        parse_mode="Markdown"
    )

@dp.message(Command("profile"))
async def profile_handler(message: types.Message):
    data = get_user_data(message.from_user.id)
    status = "👑 XO'JAYIN (God Mode)" if message.from_user.id == ADMIN_ID else "🎮 O'yinchi"
    
    await message.answer(
        f"👤 **Foydalanuvchi Profili** ({status})\n"
        f"🆔 ID: `{message.from_user.id}`\n\n"
        f"💰 Tangalar: **{data['coins']}**\n"
        f"💎 Olmoslar: **{data['diamonds']}**\n"
        f"👥 Taklif qilganlar: **{data['referrals']} kishi**\n"
        f"🃏 Kartalar: {', '.join(data['cards']) if data['cards'] else 'Mavjud emas'}",
        parse_mode="Markdown"
    )

@dp.message(Command("game"))
async def start_game(message: types.Message):
    if message.chat.type == "private":
        await message.answer("⚠️ O'yinni faqat guruhda boshlash mumkin!")
        return

    chat_id = message.chat.id
    
    if chat_id in games and games[chat_id].get("is_active"):
        await message.answer("⚠️ Hozir o'yin ketmoqda! Qayta boshlash uchun tugashini kuting.")
        return

    member = await bot.get_chat_member(chat_id, message.from_user.id)
    if member.status not in ["administrator", "creator"] and message.from_user.id != ADMIN_ID:
        await message.answer("⛔ **O'yinni faqat Bosh Admin yoki guruh adminlari boshlay oladi!**", parse_mode="Markdown")
        return

    games[chat_id] = {
        "is_active": False, 
        "players": {}, 
        "night_target": None, 
        "doctor_target": None
    }

    builder = InlineKeyboardBuilder()
    builder.button(text="🎭 O'yinga qo'shilish", callback_data=f"join_{chat_id}")
    builder.button(text="🚀 Darhol boshlash", callback_data=f"startgame_{chat_id}")
    builder.adjust(1)

    await message.answer(
        "🏙 **MAFIYA: DARK CITY — QABUL BOSHLANDI!**\n\n"
        "⏰ O'yin 60 soniyadan keyin avtomatik boshlanadi...\n"
        "Qatnashish uchun tugmani bosing:", 
        reply_markup=builder.as_markup(), 
        parse_mode="Markdown"
    )

    await asyncio.sleep(60)
    if chat_id in games and not games[chat_id]["is_active"]:
        if len(games[chat_id]["players"]) >= 3:
            await run_game_logic(chat_id)
        else:
            await bot.send_message(chat_id, "❌ **O'yinchilar soni yetarli emas (kamida 3 kishi kerak).**")
            del games[chat_id]

@dp.callback_query(F.data.startswith("join_"))
async def join_game(callback: types.CallbackQuery):
    chat_id = int(callback.data.split("_")[1])
    user_id = callback.from_user.id
    get_user_data(user_id)
    game = games.get(chat_id)

    if not game or game["is_active"]:
        await callback.answer("O'yin allaqachon boshlangan!", show_alert=True)
        return

    if user_id not in game["players"]:
        game["players"][user_id] = {"name": callback.from_user.full_name, "role": None, "is_alive": True}
        await callback.answer("Siz o'yinga qo'shildingiz!")

    player_list = "\n".join([f"👤 **{p['name']}**" for p in game["players"].values()])
    try:
        await callback.message.edit_text(
            f"🏙 **MAFIYA: DARK CITY**\n\n👥 **Qatnashchilar ({len(game['players'])} kishi):**\n{player_list}", 
            reply_markup=callback.message.reply_markup, 
            parse_mode="Markdown"
        )
    except TelegramBadRequest:
        pass

@dp.callback_query(F.data.startswith("startgame_"))
async def manual_start(callback: types.CallbackQuery):
    chat_id = int(callback.data.split("_")[1])
    member = await bot.get_chat_member(chat_id, callback.from_user.id)
    
    if member.status not in ["administrator", "creator"] and callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ O'yinni faqat admin boshlay oladi!", show_alert=True)
        return

    if chat_id in games and not games[chat_id]["is_active"]:
        if len(games[chat_id]["players"]) >= 3:
            await callback.answer()
            await run_game_logic(chat_id)
        else:
            await callback.answer("Kamida 3 ta o'yinchi kerak!", show_alert=True)

# --- AVTOMATIK O'YIN SIKLI VA ANIMATSIYALAR ---
async def run_game_logic(chat_id):
    game = games[chat_id]
    game["is_active"] = True

    player_ids = list(game["players"].keys())
    random.shuffle(player_ids)

    roles_list = ["mafia", "doctor", "detective"] + ["civilian"] * (len(player_ids) - 3)
    random.shuffle(roles_list)

    for idx, pid in enumerate(player_ids):
        game["players"][pid]["role"] = roles_list[idx]
        role_info = ROLES[roles_list[idx]]
        try:
            await bot.send_message(pid, f"🤫 **Sizning rolingiz:** {role_info['title']}\n📜 {role_info['desc']}")
        except Exception:
            pass

    # --- 🌃 TUN BOSHQARUVI ---
    await bot.send_animation(
        chat_id=chat_id, 
        animation=GIFS["night"], 
        caption="🌃 **TUN TUSHDI!**\n\nShahar uyquga ketdi. Aktiv rollar o'z yurishlarini shaxsiy chatda amalga oshirmoqda...\n⏰ Tun davomiyligi: 30 soniya"
    )

    await asyncio.sleep(30)

    # --- ☀️ KUN VA NATIJALAR ---
    await bot.send_animation(
        chat_id=chat_id, 
        animation=GIFS["day"], 
        caption="☀️ **KUN BOTDI, SHAHAR UYG'ONDI!**\n\nTungi hodisalar hisoblanmoqda..."
    )

    await asyncio.sleep(3)

    await bot.send_animation(
        chat_id=chat_id, 
        animation=GIFS["mafia_shot"], 
        caption="💥 **Tunda Mafiya qurolini ishga soldi va otishma sodir bo'ldi!**"
    )
    
    await asyncio.sleep(2)

    await bot.send_animation(
        chat_id=chat_id, 
        animation=GIFS["doctor_heal"], 
        caption="🩺 **Shifokor tun bo'yi o'z yordamini ko'rsatdi!**"
    )

    await asyncio.sleep(3)

    await bot.send_message(chat_id, "🏆 **O'yin muvaffaqiyatli yakunlandi!**\nYangi o'yin boshlash uchun qayta /game buyrug'ini bosing.")
    
    if chat_id in games:
        del games[chat_id]

# --- WEBHOOK SETUP ---
async def on_startup(bot: Bot) -> None:
    await bot.set_webhook(WEBHOOK_URL)

def main():
    dp.startup.register(on_startup)
    app = web.Application()

    webhook_requests_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    webhook_requests_handler.register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)

    web.run_app(app, host="0.0.0.0", port=PORT)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
