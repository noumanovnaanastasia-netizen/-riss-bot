import asyncio
import sqlite3
import time
import random
import logging

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage

TOKEN = "8233072384:AAHm8Lc62SJDlRDLqnyx0x7Ls1Ikyj3myGk"

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

DB = "rice_rpg.db"

logging.basicConfig(level=logging.INFO)


# =========================
# DATABASE
# =========================
def conn():
    return sqlite3.connect(DB)


def init_db():
    c = conn().cursor()

    c.execute("""
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
        losses INTEGER DEFAULT 0,
        title TEXT DEFAULT 'Нет'
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS inventory (
        user_id INTEGER PRIMARY KEY,
        energy_drink INTEGER DEFAULT 0,
        amulet INTEGER DEFAULT 0,
        box1 INTEGER DEFAULT 0,
        box2 INTEGER DEFAULT 0,
        box3 INTEGER DEFAULT 0
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS business (
        user_id INTEGER PRIMARY KEY,
        b1 INTEGER DEFAULT 0,
        b2 INTEGER DEFAULT 0,
        b3 INTEGER DEFAULT 0,
        last_collect INTEGER DEFAULT 0
    )
    """)

    conn().commit()


# =========================
# CONFIG
# =========================
BUSINESS = {
    "b1": ("🌱 Грядка", 500, 5),
    "b2": ("🧺 Теплица", 2500, 30),
    "b3": ("🏭 Фабрика", 10000, 130)
}

TITLES = {
    2000: "🌱 Росток",
    5000: "🌾 Рабочий",
    15000: "🚜 Мастер",
    50000: "🏯 Лорд",
    100000: "👑 Бог риса"
}


# =========================
# DB HELPERS
# =========================
def get(uid):
    c = conn().cursor()

    u = c.execute("SELECT * FROM users WHERE user_id=?", (uid,)).fetchone()
    if not u:
        return None

    i = c.execute("SELECT * FROM inventory WHERE user_id=?", (uid,)).fetchone()
    b = c.execute("SELECT * FROM business WHERE user_id=?", (uid,)).fetchone()

    return u, i, b


def create(uid, nick):
    c = conn().cursor()
    c.execute("INSERT OR IGNORE INTO users(user_id,nickname) VALUES(?,?)", (uid, nick))
    c.execute("INSERT OR IGNORE INTO inventory(user_id) VALUES(?)", (uid,))
    c.execute("INSERT OR IGNORE INTO business(user_id) VALUES(?)", (uid,))
    conn().commit()


def upd(table, field, value, uid):
    c = conn().cursor()
    c.execute(f"UPDATE {table} SET {field}=? WHERE user_id=?", (value, uid))
    conn().commit()


# =========================
# FSM
# =========================
class Reg(StatesGroup):
    nick = State()


# =========================
# MENU
# =========================
def kb():
    return types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton("👤 Профиль", callback_data="profile")],
        [types.InlineKeyboardButton("🏪 Магазин", callback_data="shop")],
        [types.InlineKeyboardButton("🎮 Игры", callback_data="games")],
        [types.InlineKeyboardButton("🎒 Инвентарь", callback_data="inv")]
    ])


# =========================
# START
# =========================
@dp.message(CommandStart())
async def start(m: types.Message, state: FSMContext):
    if not get(m.from_user.id):
        create(m.from_user.id, m.from_user.first_name)
        await m.answer("Введи ник:")
        await state.set_state(Reg.nick)
        return

    await m.answer("🏠 Меню", reply_markup=kb())


@dp.message(Reg.nick)
async def nick(m: types.Message, state: FSMContext):
    create(m.from_user.id, m.text)
    await state.clear()
    await m.answer("Готово!", reply_markup=kb())


# =========================
# XP SYSTEM
# =========================
def add_xp(uid, amount):
    u, i, b = get(uid)

    xp = u[3] + amount
    level = u[4]

    leveled = False

    while xp >= level * 50:
        xp -= level * 50
        level += 1
        leveled = True

        if level in TITLES:
            upd("users", "title", TITLES[level], uid)

    upd("users", "xp", xp, uid)
    upd("users", "level", level, uid)

    return leveled


# =========================
# PROFILE
# =========================
@dp.callback_query(F.data == "profile")
async def profile(c: types.CallbackQuery):
    u, i, b = get(c.from_user.id)

    text = (
        f"👤 {u[1]}\n"
        f"🍙 {u[2]}\n"
        f"⭐ XP {u[3]}\n"
        f"📊 LVL {u[4]}\n"
        f"🏅 {u[12]}\n"
        f"👑 VIP {'YES' if u[5] > int(time.time()) else 'NO'}"
    )

    await c.message.edit_text(text, reply_markup=kb())


# =========================
# BONUS
# =========================
@dp.callback_query(F.data == "bonus")
async def bonus(c: types.CallbackQuery):
    u, _, _ = get(c.from_user.id)
    now = int(time.time())

    if now - u[6] < 3600:
        return await c.answer("КД", show_alert=True)

    reward = random.randint(200, 1200)

    upd("users", "rice", u[2] + reward, u[0])
    upd("users", "last_bonus", now, u[0])

    add_xp(u[0], random.randint(5, 20))

    await c.message.edit_text(f"+{reward} 🍙", reply_markup=kb())


# =========================
# WORK
# =========================
@dp.message(Command("work"))
async def work(m: types.Message):
    u, _,