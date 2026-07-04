import asyncio
import sqlite3
import time
import random
import logging

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.storage.memory import MemoryStorage

TOKEN = "8233072384:AAHm8Lc62SJDlRDLqnyx0x7Ls1Ikyj3myGk"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

DB_NAME = "rice_empire.db"


# =====================
# DB INIT
# =====================
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        nickname TEXT,
        rice INTEGER DEFAULT 100,
        xp INTEGER DEFAULT 0,
        level INTEGER DEFAULT 1,
        last_work INTEGER DEFAULT 0
    )
    """)

    conn.commit()
    conn.close()


# =====================
# DB HELPERS
# =====================
def get_user(user_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    row = cur.fetchone()

    conn.close()

    if not row:
        return None

    return {
        "user_id": row[0],
        "nickname": row[1],
        "rice": row[2],
        "xp": row[3],
        "level": row[4],
        "last_work": row[5]
    }


def register(user_id, nickname):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
    INSERT OR REPLACE INTO users (user_id, nickname)
    VALUES (?, ?)
    """, (user_id, nickname))

    conn.commit()
    conn.close()


def update(user_id, field, value):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute(f"""
    UPDATE users SET {field}=?
    WHERE user_id=?
    """, (value, user_id))

    conn.commit()
    conn.close()


# =====================
# XP SYSTEM
# =====================
def add_xp(user_id, xp):
    u = get_user(user_id)
    if not u:
        return ""

    new_xp = u["xp"] + xp
    level = u["level"]

    while new_xp >= 50:
        new_xp -= 50
        level += 1

    update(user_id, "xp", new_xp)
    update(user_id, "level", level)

    return f"+{xp} XP"


# =====================
# START
# =====================
@dp.message(CommandStart())
async def start(message: types.Message):
    user = get_user(message.from_user.id)

    if not user:
        register(message.from_user.id, message.from_user.first_name)
        await message.answer("👋 Введи ник /start ещё раз")
        return

    await message.answer("🎮 Добро пожаловать в Rice Empire!")


# =====================
# WORK
# =====================
@dp.message(Command("work"))
async def work(message: types.Message):
    u = get_user(message.from_user.id)

    now = int(time.time())

    if now - u["last_work"] < 3600:
        await message.answer("⏳ Подожди 1 час")
        return

    earn = random.randint(100, 300)

    update(u["user_id"], "rice", u["rice"] + earn)
    update(u["user_id"], "last_work", now)

    xp_msg = add_xp(u["user_id"], random.randint(5, 10))

    await message.answer(f"🌾 +{earn} 🍙 {xp_msg}")


# =====================
# CASINO
# =====================
@dp.message(Command("casino"))
async def casino(message: types.Message):
    u = get_user(message.from_user.id)

    args = message.text.split()
    if len(args) < 2:
        return await message.answer("/casino ставка")

    bet = int(args[1])

    if bet <= 0 or u["rice"] < bet:
        return await message.answer("❌ Нет денег")

    if random.choice([True, False]):
        update(u["user_id"], "rice", u["rice"] + bet)
        await message.answer(f"🎰 WIN +{bet}")
    else:
        update(u["user_id"], "rice", u["rice"] - bet)
        await message.answer(f"💀 LOSE -{bet}")


# =====================
# DICE
# =====================
@dp.message(Command("dice"))
async def dice(message: types.Message):
    u = get_user(message.from_user.id)

    args = message.text.split()
    if len(args) < 3:
        return await message.answer("/dice ставка 1-6")

    bet = int(args[1])
    guess = int(args[2])

    roll = random.randint(1, 6)

    if guess == roll:
        win = bet * 5
        update(u["user_id"], "rice", u["rice"] + win)
        await message.answer(f"🎲 WIN {roll} +{win}")
    else:
        update(u["user_id"], "rice", u["rice"] - bet)
        await message.answer(f"🎲 LOSE {roll}")


# =====================
# TRADE
# =====================
@dp.message(Command("trade"))
async def trade(message: types.Message):
    u = get_user(message.from_user.id)

    args = message.text.split()
    if len(args) < 3:
        return await message.answer("/trade ставка вверх/вниз")

    bet = int(args[1])
    choice = args[2]

    market = random.choice(["вверх", "вниз"])

    if choice == market:
        update(u["user_id"], "rice", u["rice"] + bet)
        await message.answer(f"📈 WIN +{bet}")
    else:
        update(u["user_id"], "rice", u["rice"] - bet)
        await message.answer(f"📉 LOSE -{bet}")


# =====================
# MAIN
# =====================
async def main():
    init_db()
    print("BOT STARTED")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())