import asyncio
import sqlite3
import time
import random
import logging

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.storage.memory import MemoryStorage

# =====================
TOKEN
# =====================
TOKEN = "8233072384:AAHm8Lc62SJDlRDLqnyx0x7Ls1Ikyj3myGk"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

DB_NAME = "rice_empire.db"


# =====================
DB INIT
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
        vip_until INTEGER DEFAULT 0,
        last_bonus INTEGER DEFAULT 0,
        last_work INTEGER DEFAULT 0,
        last_rob INTEGER DEFAULT 0,
        energy_until INTEGER DEFAULT 0,
        wins INTEGER DEFAULT 0,
        losses INTEGER DEFAULT 0
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS inventory (
        user_id INTEGER PRIMARY KEY,
        energy_drink INTEGER DEFAULT 0,
        amulet INTEGER DEFAULT 0,
        box1 INTEGER DEFAULT 0,
        box2 INTEGER DEFAULT 0,
        box3 INTEGER DEFAULT 0
    )
    """)

    conn.commit()
    conn.close()


# =====================
UTILS
# =====================
def get_user(user_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    u = cur.fetchone()

    if not u:
        conn.close()
        return None

    cur.execute("SELECT * FROM inventory WHERE user_id=?", (user_id,))
    inv = cur.fetchone()

    conn.close()

    return {
        "user_id": u[0],
        "nickname": u[1],
        "rice": u[2],
        "xp": u[3],
        "level": u[4],
        "vip_until": u[5],
        "last_bonus": u[6],
        "last_work": u[7],
        "last_rob": u[8],
        "energy_until": u[9],
        "wins": u[10],
        "losses": u[11],

        "energy_drink": inv[1],
        "amulet": inv[2],
        "box1": inv[3],
        "box2": inv[4],
        "box3": inv[5],
    }


def update(user_id, table, field, value):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(f"UPDATE {table} SET {field}=? WHERE user_id=?", (value, user_id))
    conn.commit()
    conn.close()


def register(user_id, nickname):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("INSERT OR REPLACE INTO users (user_id, nickname) VALUES (?,?)",
                (user_id, nickname))

    cur.execute("INSERT OR REPLACE INTO inventory (user_id) VALUES (?)",
                (user_id,))

    conn.commit()
    conn.close()


# =====================
XP SYSTEM
# =====================
def add_xp(user_id, xp):
    data = get_user(user_id)
    if not data:
        return ""

    new_xp = data["xp"] + xp
    lvl = data["level"]

    while new_xp >= 50 and lvl < 25:
        new_xp -= 50
        lvl += 1

    update(user_id, "users", "xp", new_xp)
    update(user_id, "users", "level", lvl)

    return f"+{xp} XP"


# =====================
KEYBOARD
# =====================
def menu():
    return types.InlineKeyboardMarkup(inline_keyboard=[
        [
            types.InlineKeyboardButton(text="👤 Профиль", callback_data="profile"),
            types.InlineKeyboardButton(text="🎮 Игры", callback_data="games")
        ],
        [
            types.InlineKeyboardButton(text="🎒 Инвентарь", callback_data="inv")
        ]
    ])


# =====================
START
# =====================
@dp.message(CommandStart())
async def start(message: types.Message):
    user = get_user(message.from_user.id)

    if not user:
        register(message.from_user.id, message.from_user.first_name)
        await message.answer("Введите ник:")
        return

    await message.answer("Добро пожаловать!", reply_markup=menu())


# =====================
PROFILE
# =====================
@dp.callback_query(F.data == "profile")
async def profile(c: types.CallbackQuery):
    u = get_user(c.from_user.id)

    await c.message.edit_text(
        f"👤 {u['nickname']}\n"
        f"🍙 {u['rice']}\n"
        f"⭐ LVL {u['level']}\n"
        f"⚔️ Wins {u['wins']} | Loss {u['losses']}",
        reply_markup=menu()
    )


# =====================
BONUS
# =====================
@dp.callback_query(F.data == "games")
async def games(c: types.CallbackQuery):
    await c.message.edit_text(
        "🎮 Игры:\n/casino\n/dice\n/trade",
        reply_markup=menu()
    )


# =====================
CASINO
# =====================
@dp.message(Command("casino"))
async def casino(message: types.Message):
    u = get_user(message.from_user.id)
    bet = int(message.text.split()[1])

    if u["rice"] < bet:
        return await message.answer("нет денег")

    if random.choice([True, False]):
        update(u["user_id"], "users", "rice", u["rice"] + bet)
        await message.answer(f"WIN +{bet}")
    else:
        update(u["user_id"], "users", "rice", u["rice"] - bet)
        await message.answer(f"LOSE -{bet}")


# =====================
DICE
# =====================
@dp.message(Command("dice"))
async def dice(message: types.Message):
    u = get_user(message.from_user.id)
    args = message.text.split()

    bet = int(args[1])
    guess = int(args[2])

    roll = random.randint(1, 6)

    if guess == roll:
        update(u["user_id"], "users", "rice", u["rice"] + bet * 5)
        await message.answer(f"WIN {roll}")
    else:
        update(u["user_id"], "users", "rice", u["rice"] - bet)
        await message.answer(f"LOSE {roll}")


# =====================
TRADE
# =====================
@dp.message(Command("trade"))
async def trade(message: types.Message):
    u = get_user(message.from_user.id)

    bet = int(message.text.split()[1])
    choice = message.text.split()[2]

    market = random.choice(["up", "down"])

    if choice == market:
        update(u["user_id"], "users", "rice", u["rice"] + bet)
        await message.answer("WIN trade")
    else:
        update(u["user_id"], "users", "rice", u["rice"] - bet)
        await message.answer("LOSE trade")


# =====================
WORK
# =====================
@dp.message(Command("work"))
async def work(message: types.Message):
    u = get_user(message.from_user.id)

    earn = random.randint(100, 300)
    update(u["user_id"], "users", "rice", u["rice"] + earn)

    await message.answer(f"+{earn} 🍙")


# =====================
MAIN
# =====================
async def main():
    init_db()
    print("BOT STARTED")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())