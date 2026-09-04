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
username_to_id = {}

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

SHOP_ITEMS = {
    "shield": {"name": "🛡 Himoya qalqoni", "price_coins": 150, "price_diamonds": 0},
    "vip_status": {"name": "👑 VIP Maqom", "price_coins": 500, "price_diamonds": 5},
    "double_luck": {"name": "🍀 Omad kartasi", "price_coins": 200, "price_diamonds": 0}
}

def get_user_data(user_id):
    if user_id not in user_db:
        user_db[user_id] = {"coins": 100, "diamonds": 0, "cards": [], "referrals": 0, "name": "O'yinchi"}
    return user_db[user_id]

def register_user(user: types.User):
    data = get_user_data(user.id)
    data["name"] = user.full_name
    if user.username:
        username_to_id[user.username.lower()] = user.id

# ==========================================
# 1. BOT SHAXSIY CHATIDA ISHLAYDIGAN BUYRUQLAR
# ==========================================

@dp.message(Command("start"), F.chat.type == "private")
async def start_private(message: types.Message):
    register_user(message.from_user)
    await message.answer(
        "🎭 **MAFIYA: DARK CITY — SHAXSIY BO'LIM**\n\n"
        "👤 /profile — Balans va kartalaringiz\n"
        "💱 /exchange — Valyuta almashtirish (Tanga ↔ Olmos)\n"
        "🛒 /shop — Do'kon va buyumlar",
        parse_mode="Markdown"
    )

@dp.message(Command("profile"), F.chat.type == "private")
async def profile_private(message: types.Message):
    register_user(message.from_user)
    data = get_user_data(message.from_user.id)
    
    await message.answer(
        f"👤 **Sizning Profilingiz**\n"
        f"🆔 ID: `{message.from_user.id}`\n\n"
        f"💰 Tangalar: **{data['coins']}**\n"
        f"💎 Olmoslar: **{data['diamonds']}**\n"
        f"🃏 Kartalar: {', '.join(data['cards']) if data['cards'] else 'Mavjud emas'}",
        parse_mode="Markdown"
    )

@dp.message(Command("shop"), F.chat.type == "private")
async def shop_private(message: types.Message):
    register_user(message.from_user)
    builder = InlineKeyboardBuilder()
    
    for key, item in SHOP_ITEMS.items():
        price_str = f"{item['price_coins']} 💰" if item['price_coins'] > 0 else f"{item['price_diamonds']} 💎"
        builder.button(text=f"{item['name']} - {price_str}", callback_data=f"buy_{key}")
    
    builder.adjust(1)
    await message.answer("🛒 **MAFIYA DO'KONI**\n\nSotib olmoqchi bo'lgan buyumingizni tanlang:", reply_markup=builder.as_markup(), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("buy_"))
async def buy_item_handler(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    register_user(callback.from_user)
    item_key = callback.data.split("_")[1]
    item = SHOP_ITEMS.get(item_key)

    if not item:
        await callback.answer("Buyum topilmadi!", show_alert=True)
        return

    user_data = get_user_data(user_id)

    # Admin bo'lsangiz balansingiz kamaymaydi
    if user_id == ADMIN_ID:
        user_data["cards"].append(item["name"])
        await callback.answer(f"✅ Xarid qilindi: {item['name']}! (Balansingiz kamaymadi 👑)", show_alert=True)
        return

    if item["price_coins"] > 0:
        if user_data["coins"] < item["price_coins"]:
            await callback.answer("❌ Tangalaringiz yetarli emas!", show_alert=True)
            return
        user_data["coins"] -= item["price_coins"]

    if item["price_diamonds"] > 0:
        if user_data["diamonds"] < item["price_diamonds"]:
            await callback.answer("❌ Olmoslaringiz yetarli emas!", show_alert=True)
            return
        user_data["diamonds"] -= item["price_diamonds"]

    user_data["cards"].append(item["name"])
    await callback.answer(f"🎉 Muvaffaqiyatli xarid qilindi: {item['name']}!", show_alert=True)

# --- VALYUTA ALMASHTIRISH (VALYUTA EK Exchange) ---
@dp.message(Command("exchange"), F.chat.type == "private")
async def exchange_private(message: types.Message):
    register_user(message.from_user)
    builder = InlineKeyboardBuilder()
    
    builder.button(text="💰 100 Tanga ➡️ 1 💎 Olmos", callback_data="ex_c2d")
    builder.button(text="💎 1 Olmos ➡️ 80 💰 Tanga", callback_data="ex_d2c")
    builder.adjust(1)
    
    await message.answer("💱 **VALYUTA ALMASHTIRISH BO'LIMI**\n\nNimani nimaga almashtirmoqchisiz?", reply_markup=builder.as_markup(), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("ex_"))
async def process_exchange(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user_data = get_user_data(user_id)
    action = callback.data

    if action == "ex_c2d":
        if user_id != ADMIN_ID and user_data["coins"] < 100:
            await callback.answer("❌ Kamida 100 tanga kerak!", show_alert=True)
            return
        if user_id != ADMIN_ID:
            user_data["coins"] -= 100
        user_data["diamonds"] += 1
        await callback.answer("✅ 100 Tanga 1 Olmosga almashtirildi!", show_alert=True)

    elif action == "ex_d2c":
        if user_id != ADMIN_ID and user_data["diamonds"] < 1:
            await callback.answer("❌ Kamida 1 ta olmos kerak!", show_alert=True)
            return
        if user_id != ADMIN_ID:
            user_data["diamonds"] -= 1
        user_data["coins"] += 80
        await callback.answer("✅ 1 Olmos 80 Tangaga almashtirildi!", show_alert=True)

    # Profil tekstini shaxsiyda yangilash
    await callback.message.edit_text(
        f"💱 **Muvaffaqiyatli bajarildi!**\n\n💰 Hozirgi tangalaringiz: **{user_data['coins']}**\n💎 Hozirgi olmoslaringiz: **{user_data['diamonds']}**"
    )

# ==========================================
# 2. GURUHDA ISHLAYDIGAN BUYRUQLAR
# ==========================================

# --- GURUHDA REYTING (TOP O'YINCHILAR) ---
@dp.message(Command("top"), F.chat.type.in_(["group", "supergroup"]))
async def top_rating_group(message: types.Message):
    if not user_db:
        await message.answer("📊 Hozircha reyting ma'lumotlari yo'q.")
        return

    sorted_users = sorted(user_db.values(), key=lambda x: x["coins"], reverse=True)[:10]
    rating_text = "🏆 **GURUHNING TOP-10 BOY O'YINCHILARI**\n\n"
    
    for idx, u in enumerate(sorted_users, 1):
        rating_text += f"{idx}. **{u['name']}** — {u['coins']} 💰 | {u['diamonds']} 💎\n"

    await message.answer(rating_text, parse_mode="Markdown")

# --- GURUHDA BİR-BIRIGA PUL OTKAZISH ---
@dp.message(Command("pay"), F.chat.type.in_(["group", "supergroup"]))
async def pay_coins_group(message: types.Message, command: CommandObject):
    sender_id = message.from_user.id
    register_user(message.from_user)

    if not message.reply_to_message:
        await message.answer("⚠️ Pul o'tkazish uchun biror kishining xabariga **Reply** qilib: `/pay SUMMA` yozing!", parse_mode="Markdown")
        return

    receiver = message.reply_to_message.from_user
    if receiver.id == sender_id:
        await message.answer("❌ O'zingizga pul o'tkaza olmaysiz!")
        return

    if not command.args or not command.args.isdigit():
        await message.answer("⚠️ Summani to'g'ri kiriting! *Misol:* `/pay 50`", parse_mode="Markdown")
        return

    amount = int(command.args)
    sender_data = get_user_data(sender_id)

    if sender_id != ADMIN_ID and sender_data["coins"] < amount:
        await message.answer("❌ Balansingizda yetarli tanga yo'q!")
        return

    receiver_data = get_user_data(receiver.id)

    # Admin o'tkazsa uniki ayrilmaydi
    if sender_id != ADMIN_ID:
        sender_data["coins"] -= amount

    receiver_data["coins"] += amount

    await message.answer(
        f"💸 **PUL O'TKAZMASI!**\n\n"
        f"👤 **{message.from_user.full_name}** ➡️ **{receiver.full_name}** ga **{amount} 💰 Tanga** yubordi!",
        parse_mode="Markdown"
    )

# --- ADMIN BUYRUQLARI (YASHIRIN) ---
@dp.message(Command("addcoins"))
async def add_coins_handler(message: types.Message, command: CommandObject):
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
        target_data["coins"] += amount
        await message.answer(f"🤫 Balansga {amount} tanga qo'shildi. Hozirgi balans: {target_data['coins']}", parse_mode="Markdown")

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

# --- GURUHDA O'YINNI BOSHLASH VA TUGATISH ---
@dp.message(Command("game"), F.chat.type.in_(["group", "supergroup"]))
async def start_game(message: types.Message):
    register_user(message.from_user)
    chat_id = message.chat.id
    
    if chat_id in games and games[chat_id].get("is_active"):
        await message.answer("⚠️ Hozir o'yin ketmoqda! Qayta boshlash uchun tugashini kuting.")
        return

    member = await bot.get_chat_member(chat_id, message.from_user.id)
    if member.status not in ["administrator", "creator"] and message.from_user.id != ADMIN_ID:
        await message.answer("⛔ **O'yinni faqat Bosh Admin yoki guruh adminlari boshlay oladi!**", parse_mode="Markdown")
        return

    games[chat_id] = {"is_active": False, "players": {}}

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

    await bot.send_animation(chat_id=chat_id, animation=GIFS["night"], caption="🌃 **TUN TUSHDI!**\n\nShahar uyquga ketdi...")
    await asyncio.sleep(30)

    await bot.send_animation(chat_id=chat_id, animation=GIFS["day"], caption="☀️ **KUN BOTDI, SHAHAR UYG'ONDI!**")
    await asyncio.sleep(3)

    await bot.send_animation(chat_id=chat_id, animation=GIFS["mafia_shot"], caption="💥 **Tunda Mafiya otishma sodir etdi!**")
    await asyncio.sleep(2)

    await bot.send_animation(chat_id=chat_id, animation=GIFS["doctor_heal"], caption="🩺 **Shifokor yordam berdi!**")
    await asyncio.sleep(3)

    await bot.send_message(chat_id, "🏆 **O'yin muvaffaqiyatli yakunlandi!**\nYangi o'yin boshlash uchun qayta /game bosing.")
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
