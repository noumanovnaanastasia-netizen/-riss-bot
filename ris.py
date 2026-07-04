import asyncio
import sqlite3
import random
import time
import logging

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command

# ======================
TOKEN = "8233072384:AAEd6QXeUxz6M5UV-v_0I3SXhpcDdWagDLY"
# ======================

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher()

DB = "game.db"


# ======================
# DB
# ======================
def db():
    return sqlite3.connect(DB)


def init_db():
    conn = db()
    c = conn.cursor()

    c.execute("""
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


def get_user(uid):
    conn = db()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id=?", (uid,))
    row = c.fetchone()
    conn.close()
    return row


def create_user(uid, name):
    conn = db()
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users(user_id,nickname) VALUES(?,?)", (uid, name))
    conn.commit()
    conn.close()


def update(uid, field, value):
    conn = db()
    c = conn.cursor()
    c.execute(f"UPDATE users SET {field}=? WHERE user_id=?", (value, uid))
    conn.commit()
    conn.close()


# ======================
# XP SYSTEM
# ======================
def add_xp(uid, amount):
    conn = db()
    c = conn.cursor()

    c.execute("SELECT xp, level FROM users WHERE user_id=?", (uid,))
    xp, lvl = c.fetchone()

    xp += amount
    leveled = False

    while xp >= lvl * 100:
        xp -= lvl * 100
        lvl += 1
        leveled = True

    c.execute("UPDATE users SET xp=?, level=? WHERE user_id=?", (xp, lvl, uid))
    conn.commit()
    conn.close()

    return leveled, lvl


# ======================
# START
# ======================
@dp.message(CommandStart())
async def start(msg: types.Message):
    uid = msg.from_user.id

    if not get_user(uid):
        create_user(uid, msg.from_user.first_name)

    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🎮 Меню", callback_data="menu")]
    ])

    await msg.answer("🌾 Rice Empire v3", reply_markup=kb)


# ======================
# MENU
# ======================
@dp.callback_query(F.data == "menu")
async def menu(cb: types.CallbackQuery):
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🌾 Работа", callback_data="work")],
        [types.InlineKeyboardButton(text="🎰 Казино", callback_data="casino")],
        [types.InlineKeyboardButton(text="🎲 Кубик", callback_data="dice")],
        [types.InlineKeyboardButton(text="🏪 Магазин", callback_data="shop")],
        [types.InlineKeyboardButton(text="👤 Профиль", callback_data="profile")]
    ])

    await cb.message.edit_text("📌 Главное меню", reply_markup=kb)
    await cb.answer()


# ======================
# PROFILE
# ======================
@dp.callback_query(F.data == "profile")
async def profile(cb: types.CallbackQuery):
    u = get_user(cb.from_user.id)

    await cb.message.edit_text(
        f"👤 {u[1]}\n🍙 Rice: {u[2]}\n⭐ LVL: {u[4]}\nXP: {u[3]}"
    )


# ======================
# WORK
# ======================
@dp.callback_query(F.data == "work")
async def work(cb: types.CallbackQuery):
    uid = cb.from_user.id
    u = get_user(uid)

    now = int(time.time())
    if now - u[5] < 5:
        return await cb.answer("⏳ Подожди")

    earn = random.randint(50, 200)

    update(uid, "rice", u[2] + earn)
    update(uid, "last_work", now)

    add_xp(uid, 10)

    await cb.answer(f"+{earn} 🍙", show_alert=True)


# ======================
# CASINO
# ======================
@dp.callback_query(F.data == "casino")
async def casino_menu(cb: types.CallbackQuery):
    await cb.message.answer("Используй: /casino 100")
    await cb.answer()


@dp.message(Command("casino"))
async def casino(msg: types.Message):
    uid = msg.from_user.id
    u = get_user(uid)

    args = msg.text.split()
    if len(args) < 2:return await msg.answer("casino 100")

    bet = int(args[1])

    if bet > u[2]:
        return await msg.answer("❌ нет денег")

    if random.random() < 0.5:
        update(uid, "rice", u[2] + bet)
        add_xp(uid, 5)
        await msg.answer(f"🎰 WIN +{bet}")
    else:
        update(uid, "rice", u[2] - bet)
        await msg.answer(f"💀 LOSE -{bet}")


# ======================
# DICE
# ======================
@dp.callback_query(F.data == "dice")
async def dice_menu(cb: types.CallbackQuery):
    await cb.message.answer("Используй: /dice 100 3")
    await cb.answer()


@dp.message(Command("dice"))
async def dice(msg: types.Message):
    uid = msg.from_user.id
    u = get_user(uid)

    args = msg.text.split()
    if len(args) < 3:
        return await msg.answer("dice 100 3")

    bet = int(args[1])
    guess = int(args[2])

    roll = random.randint(1, 6)

    if guess == roll:
        win = bet * 5
        update(uid, "rice", u[2] + win)
        await msg.answer(f"🎲 WIN {roll} +{win}")
    else:
        update(uid, "rice", u[2] - bet)
        await msg.answer(f"🎲 LOSE {roll}")


# ======================
# SHOP (simple)
# ======================
@dp.callback_query(F.data == "shop")
async def shop(cb: types.CallbackQuery):
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🥤 Энергетик (1000)", callback_data="buy_drink")],
        [types.InlineKeyboardButton(text="🛡 Амулет (2000)", callback_data="buy_amulet")],
        [types.InlineKeyboardButton(text="🔙 Назад", callback_data="menu")]
    ])

    await cb.message.edit_text("🏪 Магазин", reply_markup=kb)


@dp.callback_query(F.data == "buy_drink")
async def buy_drink(cb: types.CallbackQuery):
    u = get_user(cb.from_user.id)

    if u[2] < 1000:
        return await cb.answer("❌ нет денег", show_alert=True)

    update(cb.from_user.id, "rice", u[2] - 1000)
    await cb.answer("🥤 куплено")


@dp.callback_query(F.data == "buy_amulet")
async def buy_amulet(cb: types.CallbackQuery):
    u = get_user(cb.from_user.id)

    if u[2] < 2000:
        return await cb.answer("❌ нет денег", show_alert=True)

    update(cb.from_user.id, "rice", u[2] - 2000)
    await cb.answer("🛡 куплено")


# ======================
# RUN
# ======================
async def main():
    init_db()
    print("BOT STARTED")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())