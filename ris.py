import asyncio
import logging
import random
import time
import aiosqlite

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command

# =====================
# ⚙️ CONFIG
# =====================

TOKEN = "8962500881:AAFDttMSkEzQcSGUjljScWX6VpSbew67g58"
ADMIN_ID = 810004621  # 👈 ВСТАВЬ СВОЙ ID СЮДА

DB = "game.db"

# =====================
# LOGGING
# =====================

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher()

# =====================
# KEYBOARDS
# =====================

menu_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📊 Профиль"), KeyboardButton(text="💼 Работа")],
        [KeyboardButton(text="🏢 Бизнес"), KeyboardButton(text="🏪 Магазин")],
        [KeyboardButton(text="🎮 Мини-игры"), KeyboardButton(text="👑 Админ")]
    ],
    resize_keyboard=True
)

# =====================
# DB
# =====================

async def init_db():
    async with aiosqlite.connect(DB) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            money INTEGER DEFAULT 0,
            xp INTEGER DEFAULT 0,
            level INTEGER DEFAULT 1,
            job TEXT DEFAULT 'none',
            business_income INTEGER DEFAULT 0,
            last_income INTEGER DEFAULT 0
        )
        """)
        await db.commit()

async def get_user(user_id: int):
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
        user = await cur.fetchone()

        if not user:
            await db.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
            await db.commit()
            return await get_user(user_id)

        return user

async def update_user(user_id: int, field: str, value):
    async with aiosqlite.connect(DB) as db:
        await db.execute(f"UPDATE users SET {field}=? WHERE user_id=?", (value, user_id))
        await db.commit()

# =====================
# LEVEL SYSTEM
# =====================

def xp_to_level(xp):
    return max(1, xp // 100 + 1)

# =====================
# START
# =====================

@dp.message(Command("start"))
async def start(message: Message):
    await get_user(message.from_user.id)
    await message.answer(
        "👋 Добро пожаловать в Life Game 2.0\n\nТы начинаешь с нуля. Развивайся!",
        reply_markup=menu_kb
    )

# =====================
# PROFILE
# =====================

@dp.message(F.text == "📊 Профиль")
async def profile(message: Message):
    user = await get_user(message.from_user.id)

    text = f"""
📊 ТВОЙ ПРОФИЛЬ

💰 Деньги: {user[1]}
⭐ XP: {user[2]}
📈 Уровень: {user[3]}
💼 Работа: {user[4]}
🏢 Доход бизнеса: {user[5]}/мин
"""
    await message.answer(text)

# =====================
# JOBS
# =====================

@dp.message(F.text == "💼 Работа")
async def job_menu(message: Message):
    await message.answer(
        "💼 Работы:\n\n"
        "1️⃣ Склад\n2️⃣ Доставка\n3️⃣ Уборщик\n\n"
        "Напиши: работа 1 / 2 / 3"
    )

@dp.message(F.text.startswith("работа"))
async def set_job(message: Message):
    user_id = message.from_user.id
    user = await get_user(user_id)

    jobs = {
        "1": "Склад",
        "2": "Доставка",
        "3": "Уборщик"
    }

    try:
        choice = message.text.split()[1]
        job = jobs.get(choice)

        if not job:
            return await message.answer("❌ Нет такой работы")

        await update_user(user_id, "job", job)
        await message.answer(f"✅ Ты устроился: {job}")

    except:
        await message.answer("❌ Напиши: работа 1/2/3")

# =====================
# BUSINESS (PASSIVE INCOME)
# =====================

@dp.message(F.text == "🏢 Бизнес")
async def business(message: Message):
    user_id = message.from_user.id
    user = await get_user(user_id)

    income = user[5]

    await message.answer(
        f"🏢 Бизнес система\n\n"
        f"💰 Доход: {income}/мин\n\n"
        f"Пока доступно базовое начисление."
    )

# =====================
# MINI GAME
# =====================

@dp.message(F.text == "🎮 Мини-игры")
async def mini_games(message: Message):
    num = random.randint(1, 5)
    await message.answer("🎮 Угадай число от 1 до 5")

    dp.current_number = num

@dp.message()
async def guess(message: Message):
    if hasattr(dp, "current_number"):
        try:
            if int(message.text) == dp.current_number:
                reward = random.randint(100, 1000)
                await update_user(message.from_user.id, "money",
                                  (await get_user(message.from_user.id))[1] + reward)

                await message.answer(f"🎉 Победа! +{reward}$")
            else:
                await message.answer("❌ Неверно")
        except:
            pass

# =====================
# ADMIN
# =====================

@dp.message(F.text == "👑 Админ")
async def admin_panel(message: Message):
    if message.from_user.id != ADMIN_ID:810004621

    return await message.answer("❌ Нет доступа")

    await message.answer(
        "👑 АДМИН ПАНЕЛЬ\n\n"
        "Команды:\n"
        "/add_money id amount\n"
        "/add_xp id amount"
    )

@dp.message(Command("add_money"))
async def add_money(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    _, uid, amount = message.text.split()
    user = await get_user(int(uid))

    new_money = user[1] + int(amount)
    await update_user(int(uid), "money", new_money)

    await message.answer("✅ Деньги выданы")

@dp.message(Command("add_xp"))
async def add_xp(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    _, uid, amount = message.text.split()
    user = await get_user(int(uid))

    new_xp = user[2] + int(amount)
    await update_user(int(uid), "xp", new_xp)

    await message.answer("✅ XP выдано")

# =====================
# MAIN
# =====================

async def main():
    await init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())