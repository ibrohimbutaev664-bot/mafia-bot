import os
import random
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

# Server sozlamalari (Render yoki boshqa hostinglar avtomatik port ajratadi)
WEBHOOK_HOST = os.getenv("RENDER_EXTERNAL_URL", "https://your-app-name.onrender.com")
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"
PORT = int(os.getenv("PORT", 8080))

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

games = {}
user_db = {}

ROLES = {
    "mafia": {"title": "🕵️‍♂️ Mafiya", "desc": "Tunda yashirincha tinch aholini o'ldiradi."},
    "doctor": {"title": "🩺 Shifokor", "desc": "Tunda 1 kishini o'limdan saqlab qoladi."},
    "detective": {"title": "🔍 Komissar", "desc": "Tunda gumondorning rolini tekshiradi."},
    "hacker": {"title": "💻 Xaker", "desc": "Tunda bir o'yinchining ovoz berishini bloklaydi."},
    "civilian": {"title": "👨‍🌾 Tinch aholi", "desc": "Kunduzi muhokamada qatnashib, mafiyani topadi."},
    "santa": {"title": "🎅 Qor bobo", "desc": "Tunda o'yinchini muzlatadi yoki qalqon beradi."},
    "jester": {"title": "🤡 Masxaraboz", "desc": "Maqsadi — kunduzi o'zini haydatib yutish."},
    "guard": {"title": "🛡 Posbon", "desc": "Tunda bir fuqaroni o'limdan saqlaydi."},
    "witness": {"title": "📜 Guvoh", "desc": "Hujum bo'lsa, qotilning kimligini ko'rib qoladi."},
    "journalist": {"title": "📣 Jurnalist", "desc": "2 kishining jamoasi bir xilligini tekshiradi."}
}

def get_user_data(user_id):
    if user_id not in user_db:
        if user_id == ADMIN_ID:
            user_db[user_id] = {"coins": 999999, "diamonds": 999999, "cards": ["Jekpot", "Xaos"], "referrals": 0}
        else:
            user_db[user_id] = {"coins": 100, "diamonds": 0, "cards": [], "referrals": 0}
    return user_db[user_id]

# --- BUYRUQLAR VA HANDLERLAR ---
@dp.message(Command("start"))
async def start_handler(message: types.Message, command: CommandObject):
    user_id = message.from_user.id
    is_new = user_id not in user_db
    get_user_data(user_id)
    
    args = command.args
    if is_new and args and args.isdigit():
        referrer_id = int(args)
        if referrer_id != user_id and referrer_id in user_db:
            ref_data = get_user_data(referrer_id)
            ref_data["coins"] += 50
            ref_data["diamonds"] += 1
            ref_data["referrals"] += 1
            try:
                await bot.send_message(
                    referrer_id, 
                    f"🎉 **Yangi taklif!** Do'stingiz botga kirdi.\n🎁 Sizga **50 Tanga** va **1 Olmos** berildi!",
                    parse_mode="Markdown"
                )
            except Exception:
                pass

    await message.answer(
        "🎭 **MAFIYA: DARK CITY BOTIGA XUSH KELIBSIZ!**\n\n"
        "📖 /info — Rollar va Do'kon Katalogi\n"
        "👥 /ref — Do'stlarni taklif qilish va mukofot olish\n"
        "👤 /profile — Balans va kartalar\n"
        "🛒 /shop — Do'kon\n"
        "🎲 /game — Guruhda o'yin boshlash",
        parse_mode="Markdown"
    )

@dp.message(Command("info"))
async def info_handler(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.button(text="🎭 Rollar Vazifalari", callback_data="cat_roles")
    builder.button(text="🛒 Do'kon Buyumlari", callback_data="cat_shop")
    builder.adjust(1)

    await message.answer(
        "📖 **DARK CITY — BATAFSIL KATALOG**\n\n"
        "Qaysi bo'lim haqida to'liq ma'lumot olmoqchisiz?",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data.startswith("cat_"))
async def process_catalog(callback: types.CallbackQuery):
    try:
        await callback.answer()
    except TelegramBadRequest:
        pass

    category = callback.data.split("_")[1]
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Orqaga", callback_data="back_to_info")

    if category == "roles":
        text = (
            "🎭 **O'YIN ROLLARI VA VAZIFALARI:**\n\n"
            "🕵️‍♂️ **Mafiya:** Tunda birgalikda shahar fuqarosini o'ldirishni rejalashtiradi.\n"
            "🩺 **Shifokor:** Tunda 1 kishini tanlaydi. Hujum bo'lsa, uni tirik saqlaydi.\n"
            "🔍 **Komissar:** Tunda 1 kishini tekshirib, mafiya yoki yo'qligini biladi.\n"
            "💻 **Xaker:** Tunda o'yinchini bloklaydi, u kunduzi ovoz bera olmaydi.\n"
            "🎅 **Qor bobo:** O'yinchini muzlatadi yoki unga 1 kechalik qalqon beradi.\n"
            "🤡 **Masxaraboz:** Maqsadi — ayyorlik bilan kunduzi o'zini guruhdan chiqarishlariga erishish.\n"
            "🛡 **Posbon:** Fuqaroni tungi hujumlardan himoya qiladi.\n"
            "📜 **Guvoh:** Tunda bitta uyni poylaydi. Hujum bo'lsa, qotilni tanib oladi.\n"
            "📣 **Jurnalist:** 2 o'yinchini solishtiradi: ular bitta jamoadami yoki yo'q.\n"
            "👨‍🌾 **Tinch aholi:** Tunda uxlaydi, kunduzi muhokama qilib mafiyani topadi."
        )
    else:
        text = (
            "🛒 **DO'KON BUYUMLARI VA XUSUSIYATLARI:**\n\n"
            "🛡 **Zirh (300 💰):** Tunda 1 martalik hujumdan avtomatik saqlab qoladi.\n"
            "📜 **Soxta Hujjat (450 💰):** Komissar tekshirganda rolingizni 'Tinch aholi' ko'rsatadi.\n"
            "📣 **Karnay (250 💰):** Kunduzgi ovoz berishda sizning ovozingiz x2 beriladi.\n"
            "🎯 **Snayper (400 💰):** Birovning tungi harakatini 1 kechaga muzlatadi.\n"
            "🔮 **Taqdir Sharigi (350 💰):** O'lganingizdan keyin ham 1 marta ovoz berish imkonini beradi.\n"
            "🧪 **Zahar Zardobi (500 💰):** Sizni o'ldirgan qotilni o'zingiz bilan birga olib ketasiz.\n"
            "🃏 **Jekpot Kartasi (5 💎):** Do'kondagi barcha buyumlardan 1 tadan taqdim etadi.\n"
            "👁 **Rolni Ko'rish (3 💎):** Istalgan o'yinchining haqiqiy rolini ochib beradi.\n"
            "🎭 **Xaos Kartasi (4 💎):** Rolingizni boshqa bir o'yinchi bilan almashtirib qo'yadi.\n"
            "👑 **Ovoz Boshlig'i (6 💎):** Birovning ovoz berish huquqini '0' ga tenglashtiradi.\n"
            "👻 **Ruh Rejimi (7 💎):** O'lgandan keyin ham tiriklarga 1 marta ishora yuboradi.\n"
            "💰 **Oltin Sandiq (3 💎):** 500 dan 1500 gacha tasodifiy tanga beradi."
        )

    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="Markdown")

@dp.callback_query(F.data == "back_to_info")
async def back_to_info(callback: types.CallbackQuery):
    await info_handler(callback.message)

@dp.message(Command("ref"))
async def ref_handler(message: types.Message):
    user_id = message.from_user.id
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={user_id}"
    data = get_user_data(user_id)
    
    await message.answer(
        f"🔗 **SIZNING REFERAL SILKANGIZ:**\n`{ref_link}`\n\n"
        f"👥 Taklif qilgan do'stlaringiz: **{data['referrals']} kishi**\n"
        f"🎁 **Har bir do'stingiz uchun:** 50 Tanga 💰 va 1 Olmos 💎 beriladi!",
        parse_mode="Markdown"
    )

@dp.message(Command("profile"))
async def profile_handler(message: types.Message):
    data = get_user_data(message.from_user.id)
    status = "👑 XO'JAYIN (God Mode)" if message.from_user.id == ADMIN_ID else "🎮 O'yinchi"
    
    await message.answer(
        f"👤 **Foydalanuvchi Profili** ({status})\n\n"
        f"💰 Tangalar: **{data['coins']}**\n"
        f"💎 Olmoslar: **{data['diamonds']}**\n"
        f"👥 Taklif qilganlar: **{data['referrals']} kishi**\n"
        f"🃏 Kartalar: {', '.join(data['cards']) if data['cards'] else 'Mavjud emas'}",
        parse_mode="Markdown"
    )

@dp.message(Command("shop"))
async def shop_handler(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.button(text="🛡 Zirh (300 💰)", callback_data="buy_armor")
    builder.button(text="📜 Soxta Hujjat (450 💰)", callback_data="buy_fake_doc")
    builder.button(text="📣 Karnay (250 💰)", callback_data="buy_megaphone")
    builder.button(text="🎯 Snayper (400 💰)", callback_data="buy_freeze")
    builder.button(text="🔮 Taqdir Sharigi (350 💰)", callback_data="buy_orb")
    builder.button(text="🧪 Zahar Zardobi (500 💰)", callback_data="buy_poison")
    builder.button(text="🃏 Jekpot (5 💎)", callback_data="buy_jackpot")
    builder.button(text="👁 Rolni Ko'rish (3 💎)", callback_data="buy_reveal")
    builder.button(text="🎭 Xaos Kartasi (4 💎)", callback_data="buy_xaos")
    builder.button(text="👑 Ovoz Boshlig'i (6 💎)", callback_data="buy_boss_vote")
    builder.button(text="👻 Ruh Rejimi (7 💎)", callback_data="buy_ghost")
    builder.button(text="💰 Oltin Sandiq (3 💎)", callback_data="buy_chest")
    builder.adjust(2)
    
    await message.answer("🛒 **DARK CITY SUPER SHOP**\n\nKerakli buyumni xarid qilish uchun bosing:", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("buy_"))
async def process_buy(callback: types.CallbackQuery):
    item = callback.data.split("_")[1]
    data = get_user_data(callback.from_user.id)
    
    if callback.from_user.id == ADMIN_ID:
        data["cards"].append(item.capitalize())
        await callback.answer(f"👑 ADMIN: {item.capitalize()} tekinga berildi!", show_alert=True)
    else:
        await callback.answer("🛍 Xarid muvaffaqiyatli amalga oshirildi!", show_alert=True)

@dp.message(Command("game"))
async def start_game(message: types.Message):
    if message.chat.type == "private":
        await message.answer("⚠️ O'yinni faqat guruhda boshlash mumkin!")
        return

    chat_id = message.chat.id
    games[chat_id] = {"is_active": False, "players": {}, "night_actions": {}}

    builder = InlineKeyboardBuilder()
    builder.button(text="🎭 O'yinga qo'shilish", callback_data=f"join_{chat_id}")
    builder.button(text="🚀 O'yinni boshlash", callback_data=f"startgame_{chat_id}")
    builder.adjust(1)

    await message.answer("🏙 **MAFIYA: DARK CITY**\n\nQatnashish uchun bosing:", reply_markup=builder.as_markup(), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("join_"))
async def join_game(callback: types.CallbackQuery):
    try:
        await callback.answer()
    except TelegramBadRequest:
        pass

    chat_id = int(callback.data.split("_")[1])
    user_id = callback.from_user.id
    get_user_data(user_id)
    game = games.get(chat_id)
    if not game or game["is_active"]:
        return

    if user_id not in game["players"]:
        game["players"][user_id] = {"name": callback.from_user.full_name, "role": None, "is_alive": True}

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
async def run_game(callback: types.CallbackQuery):
    try:
        await callback.answer()
    except TelegramBadRequest:
        pass

    chat_id = int(callback.data.split("_")[1])
    game = games.get(chat_id)
    if not game or len(game["players"]) < 1:
        return

    game["is_active"] = True
    player_ids = list(game["players"].keys())
    random.shuffle(player_ids)

    roles_keys = list(ROLES.keys())
    admin_notify_text = "👑 **GOD MODE: O'yin Rollari Ro'yxati**\n\n"

    for i, pid in enumerate(player_ids):
        assigned_role = roles_keys[i % len(roles_keys)]
        game["players"][pid]["role"] = assigned_role
        role_info = ROLES[assigned_role]
        
        admin_notify_text += f"👤 {game['players'][pid]['name']} ➡️ **{role_info['title']}**\n"
        try:
            await bot.send_message(pid, f"🤫 **Sizning rolingiz:** {role_info['title']}\n📜 {role_info['desc']}", parse_mode="Markdown")
        except Exception:
            pass

    try:
        await bot.send_message(ADMIN_ID, admin_notify_text, parse_mode="Markdown")
    except Exception:
        pass

    await callback.message.edit_text("🎲 Rollar tarqatildi! 🌃 **TUN TUSHDI** NODE\n\nAktiv rollar shaxsiy chatda harakat qilmoqda...", parse_mode="Markdown")

# --- WEBHOOK ISHGA TUSHIRISH ---
async def on_startup(bot: Bot) -> None:
    await bot.set_webhook(WEBHOOK_URL)

def main():
    dp.startup.register(on_startup)
    app = web.Application()

    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
    )
    webhook_requests_handler.register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)

    web.run_app(app, host="0.0.0.0", port=PORT)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
