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
ADMIN_ID = 1022350478  # Bosh Admin (Xo'jayin)

WEBHOOK_HOST = os.getenv("RENDER_EXTERNAL_URL", "https://mafia-bot-m8zh.onrender.com")
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"
PORT = int(os.getenv("PORT", 8080))

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

games = {}
user_db = {}
username_to_id = {}  # Usernamelarni ID ga bog'lash uchun bazacha

# --- GIF / MEDIA HAVOLALARI ---
GIFS = {
    "night": "https://media.giphy.com/media/l2Jhv955I4MpcMMhe/giphy.gif",
    "day": "https://media.giphy.com/media/3o6Zt8A83pVR3M6A4U/giphy.gif",
    "mafia_shot": "https://media.giphy.com/media/xT1R9LUBvA7R89q0eA/giphy.gif",
    "doctor_heal": "https://media.giphy.com/media/3o7TKSx0g7d3072224/giphy.gif",
    "detective_check": "https://media.giphy.com/media/l41lFw05vM4S8d31C/giphy.gif"
}

ROLES = {
    "mafia": {"title": "🕵️‍♂️ Mafiya", "desc": "Tunda yashirincha tinch aholini o'ldiradi."},
    "doctor": {"title": "🩺 Shifokor", "desc": "Tunda 1 kishini o'limdan saqlab qoladi."},
    "detective": {"title": "🔍 Komissar", "desc": "Tunda gumondorning rolini tekshiradi."},
    "civilian": {"title": "👨‍🌾 Tinch aholi", "desc": "Kunduzi muhokamada qatnashib, mafiyani topadi."}
}

# --- BALANS TIZIMI ---
def get_user_data(user_id):
    if user_id not in user_db:
        user_db[user_id] = {"coins": 100, "diamonds": 0, "cards": [], "referrals": 0}
    return user_db[user_id]

def register_user(user: types.User):
    get_user_data(user.id)
    if user.username:
        username_to_id[user.username.lower()] = user.id

# --- YASHIRIN BALANS TO'LDIRISH (USERNAME, REPLY YOKI ID ORQALI) ---
@dp.message(Command("addcoins"))
async def add_coins_handler(message: types.Message, command: CommandObject):
    if message.from_user.id != ADMIN_ID:
        return

    target_id = None
    amount = 0

    # 1-usul: Reply orqali
    if message.reply_to_message:
        target_id = message.reply_to_message.from_user.id
        if command.args and command.args.isdigit():
            amount = int(command.args)
    # 2-usul: Username yoki ID va Summa orqali (/addcoins @username 500)
    elif command.args:
        args = command.args.split()
        if len(args) >= 2:
            target_arg = args[0].replace("@", "").lower()
            if target_arg.isdigit():
                target_id = int(target_arg)
            elif target_arg in username_to_id:
                target_id = username_to_id[target_arg]
            
            if args[1].isdigit():
                amount = int(args[1])

    if target_id and amount > 0:
        target_data = get_user_data(target_id)
        target_data["coins"] += amount
        await message.answer(f"🤫 Balansga {amount} tanga qo'shildi. Hozirgi balans: {target_data['coins']}", parse_mode="Markdown")
    else:
        await message.answer("⚠️ Qanday ishlatish:\n• `/addcoins @username 500`\n• Xabarga reply qilib: `/addcoins 500`\n• `/addcoins ID 500`", parse_mode="Markdown")

@dp.message(Command("adddiamonds"))
async def add_diamonds_handler(message: types.Message, command: CommandObject):
    if message.from_user.id != ADMIN_ID:
        return

    target_id = None
    amount = 0

    if message.reply_to_message:
        target_id = message.reply_to_message.from_user.id
        if command.args and command.args.isdigit():
            amount = int(command.args)
    elif command.args:
        args = command.args.split()
        if len(args) >= 2:
            target_arg = args[0].replace("@", "").lower()
            if target_arg.isdigit():
                target_id = int(target_arg)
            elif target_arg in username_to_id:
                target_id = username_to_id[target_arg]
            
            if args[1].isdigit():
                amount = int(args[1])

    if target_id and amount > 0:
        target_data = get_user_data(target_id)
        target_data["diamonds"] += amount
        await message.answer(f"🤫 Balansga {amount} olmos qo'shildi. Hozirgi balans: {target_data['diamonds']}", parse_mode="Markdown")
    else:
        await message.answer("⚠️ Qanday ishlatish:\n• `/adddiamonds @username 5`\n• Xabarga reply qilib: `/adddiamonds 5`\n• `/adddiamonds ID 5`", parse_mode="Markdown")

# --- ASOSIY BUYRUQLAR ---
@dp.message(Command("start"))
async def start_handler(message: types.Message, command: CommandObject):
    register_user(message.from_user)
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
    register_user(message.from_user)
    data = get_user_data(message.from_user.id)
    
    await message.answer(
        f"👤 **Foydalanuvchi Profili**\n"
        f"🆔 ID: `{message.from_user.id}`\n\n"
        f"💰 Tangalar: **{data['coins']}**\n"
        f"💎 Olmoslar: **{data['diamonds']}**\n"
        f"👥 Taklif qilganlar: **{data['referrals']} kishi**\n"
        f"🃏 Kartalar: {', '.join(data['cards']) if data['cards'] else 'Mavjud emas'}",
        parse_mode="Markdown"
    )

@dp.message(Command("game"))
async def start_game(message: types.Message):
    register_user(message.from_user)
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
    user = callback.from_user
    register_user(user)
    game = games.get(chat_id)

    if not game or game["is_active"]:
        await callback.answer("O'yin allaqachon boshlangan!", show_alert=True)
        return

    if user.id not in game["players"]:
        game["players"][user.id] = {"name": user.full_name, "role": None, "is_alive": True}
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
