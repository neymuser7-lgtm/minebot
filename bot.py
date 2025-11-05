import asyncio
import json
import random
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import (
    Message,
    CallbackQuery,  # ✅ To'g'ri import qilindi
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

# Sozlamalar
BOT_TOKEN = ""
ADMINS = [8218691188]  # O'zingizning Telegram IDingizni qo'ying

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
USER_DATA_FILE = "users.json"

# ——— Yordamchi funksiyalar ———
def load_users():
    try:
        with open(USER_DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_users(data):
    with open(USER_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def generate_referral_code(user_id):
    return f"mini{str(user_id)[-6:]}"

def get_weapon_damage(weapon_name):
    return {
        "None": 5,
        "Oddiy qilich": 15,
        "Kuchli qilich": 25
    }.get(weapon_name, 5)

def get_league_by_coins(coins):
    if coins >= 50000:
        return "👑 Afsonaviy"
    elif coins >= 20000:
        return "🥇 Katta Coin"
    elif coins >= 5000:
        return "🥈 O‘rtacha Coin"
    else:
        return "🥉 Kichik Coin"

def add_exp(user, exp):
    user["exp"] += exp
    exp_needed = user["level"] * 100
    if user["exp"] >= exp_needed:
        user["level"] += 1
        user["exp"] = user["exp"] - exp_needed
        return True
    return False

# ——— Ma'lumotlarni yuklash va migratsiya ———
users = load_users()

for user_id_str, data in list(users.items()):
    defaults = {
        "coins": 0,
        "level": 1,
        "exp": 0,
        "weapon": "None",
        "last_bonus": "2000-01-01 00:00:00",
        "daily_streak": 0,
        "last_login": "2000-01-01",
        "wins": 0,
        "losses": 0,
        "referral_code": generate_referral_code(int(user_id_str)),
        "referrals": [],
        "inventory": []
    }
    for key, default_val in defaults.items():
        if key not in data:
            data[key] = default_val

save_users(users)

# ——— Foydalanuvchini ro'yxatdan o'tkazish ———
def register_user(user_id, ref_by=None):
    user_id_str = str(user_id)
    if user_id_str not in users:
        users[user_id_str] = {
            "coins": 0,
            "level": 1,
            "exp": 0,
            "weapon": "None",
            "last_bonus": "2000-01-01 00:00:00",
            "daily_streak": 0,
            "last_login": datetime.now().strftime("%Y-%m-%d"),
            "wins": 0,
            "losses": 0,
            "referral_code": generate_referral_code(user_id),
            "referrals": [],
            "inventory": []
        }
        save_users(users)

        if ref_by and ref_by != user_id_str and ref_by in users:
            users[ref_by]["coins"] += 1000
            users[user_id_str]["coins"] += 500
            if user_id_str not in users[ref_by]["referrals"]:
                users[ref_by]["referrals"].append(user_id_str)
            save_users(users)

# ——— Menyu ———
def get_main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 Profil", callback_data="profile")],
        [InlineKeyboardButton(text="🏆 Ligam", callback_data="leagues")],
        [InlineKeyboardButton(text="🎁 Kunlik bonus", callback_data="bonus")],
        [InlineKeyboardButton(text="⚔️ Jang qilish", callback_data="battle")],
        [InlineKeyboardButton(text="🗡 Qurollar", callback_data="weapons")]
    ])

# ——— START ———
@dp.message(Command("start"))
async def start_handler(message: Message):
    user_id = message.from_user.id
    args = message.text.split()
    ref_by = args[1] if len(args) > 1 else None
    register_user(user_id, ref_by)

    ref_code = users[str(user_id)]["referral_code"]
    await message.answer(
        f"💰 **MiniCoin Pro** botiga xush kelibsiz!\n\n"
        f"🔗 Sizning taklif kodingiz: `{ref_code}`\n"
        f"📤 Do'stingiz bu kod orqali kirsa, siz **1000 coin**, u esa **500 coin** oladi!\n\n"
        f"🔽 Menyuni tanlang:",
        parse_mode="Markdown",
        reply_markup=get_main_menu()
    )

# ——— PROFIL ———
@dp.callback_query(lambda c: c.data == "profile")
async def profile_callback(callback: CallbackQuery):  # ✅ To'g'ri tur
    user = users[str(callback.from_user.id)]
    league = get_league_by_coins(user["coins"])
    text = (
        f"👤 **Sizning profilingiz:**\n\n"
        f"💸 Coinlar: {user['coins']}\n"
        f"📊 Daraja: {user['level']} (Exp: {user['exp']}/{user['level'] * 100})\n"
        f"🏆 Liga: {league}\n"
        f"⚔️ Janglar: {user['wins']} Gʻalaba / {user['losses']} Magʻlubiyat\n"
        f"🎁 Kunlik streak: {user['daily_streak']} kun\n"
        f"🗡 Qurol: {user['weapon']}\n"
        f"👥 Taklif qilinganlar: {len(user['referrals'])}"
    )
    await callback.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Asosiy menyu", callback_data="back_to_menu")]
        ])
    )

# ——— LIGALAR ———
@dp.callback_query(lambda c: c.data == "leagues")
async def leagues_callback(callback: CallbackQuery):
    user = users[str(callback.from_user.id)]
    league = get_league_by_coins(user["coins"])
    await callback.message.edit_text(
        f"🏆 Sizning ligangiz: **{league}**\n\n"
        "Ligangiz coinlaringizga qarab avtomatik yangilanadi!",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Asosiy menyu", callback_data="back_to_menu")]
        ])
    )

# ——— BONUS ———
@dp.callback_query(lambda c: c.data == "bonus")
async def bonus_callback(callback: CallbackQuery):
    user_id = str(callback.from_user.id)
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    user = users[user_id]

    if user.get("last_login", "") == today:
        await callback.message.answer("✅ Siz bugun bonus oldingiz!")
        return

    last_bonus_str = user.get("last_bonus", "2000-01-01 00:00:00")
    try:
        last_bonus = datetime.strptime(last_bonus_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        # Agar format noto'g'ri bo'lsa, yangilash
        last_bonus = datetime(2000, 1, 1)
        user["last_bonus"] = "2000-01-01 00:00:00"

    if now - last_bonus >= timedelta(hours=24):
        if now - last_bonus < timedelta(hours=48):
            user["daily_streak"] = user.get("daily_streak", 0) + 1
        else:
            user["daily_streak"] = 1

        base_bonus = 1000
        streak_bonus = min(user["daily_streak"] * 100, 500)
        total_bonus = base_bonus + streak_bonus

        user["coins"] += total_bonus
        user["last_bonus"] = now.strftime("%Y-%m-%d %H:%M:%S")
        user["last_login"] = today
        save_users(users)

        await callback.message.answer(
            f"🎉 Kunlik bonus!\n"
            f"💰 Asosiy: 1000 coin\n"
            f"🔥 Streak bonus: +{streak_bonus} coin\n"
            f"💎 Jami: **{total_bonus}** coin!"
        )
    else:
        next_bonus = last_bonus + timedelta(hours=24)
        time_left = next_bonus - now
        hours, remainder = divmod(time_left.seconds, 3600)
        minutes = remainder // 60
        await callback.message.answer(f"⏳ Keyingi bonus: {hours} soat {minutes} daqiqa")

# ——— JANG ———
@dp.callback_query(lambda c: c.data == "battle")
async def battle_callback(callback: CallbackQuery):
    user_id = str(callback.from_user.id)
    user = users[user_id]

    if user["weapon"] == "None":
        await callback.message.edit_text(
            "⚠️ Jang qilish uchun qurol sotib oling!",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🗡 Qurollar", callback_data="weapons")],
                [InlineKeyboardButton(text="⬅️ Asosiy menyu", callback_data="back_to_menu")]
            ])
        )
        return

    user_dmg = get_weapon_damage(user["weapon"])
    win_prob = min(95, max(20, 30 + (user_dmg - 5) * 2))
    if random.randint(1, 100) <= win_prob:
        reward = random.randint(300, 600)
        user["coins"] += reward
        user["wins"] += 1
        leveled_up = add_exp(user, 75)
        save_users(users)

        msg = f"🔥 G‘alaba qozondingiz!\n+{reward} 💰 coin va 75 ⚡ exp!"
        if leveled_up:
            msg += f"\n\n🎉 **Daraja {user['level']} ga ko‘tarildingiz!**"
    else:
        user["losses"] += 1
        save_users(users)
        msg = "💀 Mag‘lub bo‘ldingiz. Qurolingizni kuchaytiring!"

    await callback.message.edit_text(
        msg,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Qayta jang", callback_data="battle")],
            [InlineKeyboardButton(text="⬅️ Asosiy menyu", callback_data="back_to_menu")]
        ])
    )

# ——— QUROLLAR ———
@dp.callback_query(lambda c: c.data == "weapons")
async def weapons_callback(callback: CallbackQuery):
    user = users[str(callback.from_user.id)]
    await callback.message.edit_text(
        f"🛒 **Qurollar do‘koni**\nJoriy qurolingiz: `{user['weapon']}`\n\n"
        "Sotib olish:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🗡 Oddiy qilich - 5,000 coin", callback_data="buy_basic")],
            [InlineKeyboardButton(text="⚔️ Kuchli qilich - 15,000 coin", callback_data="buy_strong")],
            [InlineKeyboardButton(text="⬅️ Asosiy menyu", callback_data="back_to_menu")]
        ])
    )

@dp.callback_query(lambda c: c.data.startswith("buy_"))
async def buy_weapon(callback: CallbackQuery):
    user_id = str(callback.from_user.id)
    user = users[user_id]
    mapping = {"buy_basic": ("Oddiy qilich", 5000), "buy_strong": ("Kuchli qilich", 15000)}
    if callback.data not in mapping:
        await callback.answer("Noma'lum qurol!", show_alert=True)
        return

    name, price = mapping[callback.data]
    if user["coins"] >= price:
        user["coins"] -= price
        user["weapon"] = name
        save_users(users)
        await callback.message.edit_text(
            f"✅ **{name}** sotib olindi!",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⚔️ Jang qilish", callback_data="battle")],
                [InlineKeyboardButton(text="⬅️ Asosiy menyu", callback_data="back_to_menu")]
            ])
        )
    else:
        await callback.answer("❌ Mablag‘ yetarli emas!", show_alert=True)

# ——— ORQAGA ———
@dp.callback_query(lambda c: c.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery):
    await callback.message.edit_text("🔽 Menyuni tanlang:", reply_markup=get_main_menu())

# ——— ADMIN ———
@dp.message(Command("stats"))
async def stats_handler(message: Message):
    if message.from_user.id in ADMINS:
        total = len(users)
        coins = sum(u.get("coins", 0) for u in users.values())
        await message.answer(f"👥 Foydalanuvchilar: {total}\n💰 Jami coin: {coins}")

# ——— ISHGA TUSHIRISH ———
async def main():
    print("✅ MiniCoin Pro bot ishga tushdi (xavfsiz migratsiya bilan)...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
