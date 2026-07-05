import asyncio
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart

# =========================
# ТОКЕН БОТА
# =========================

TOKEN = "8962500881:AAFDttMSkEzQcSGUjljScWX6VpSbew67g58"

bot = Bot(token=TOKEN)
dp = Dispatcher()

logging.basicConfig(level=logging.INFO)

# =========================
# ПРОСТАЯ "БАЗА" ИГРОКОВ
# =========================

users = {}

def get_user(user_id: int):
    if user_id not in users:
        users[user_id] = {
            "money": 0,
            "xp": 0,
            "level": 1,
            "age": 1
        }
    return users[user_id]

# =========================
# ГЛАВНОЕ МЕНЮ (КНОПКИ ВНИЗУ ЭКРАНА)
# =========================

main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="💼 Работа"), KeyboardButton(text="🎮 Мини-игры")],
        [KeyboardButton(text="🏪 Магазин"), KeyboardButton(text="💰 Бизнес")],
        [KeyboardButton(text="👤 Профиль"), KeyboardButton(text="⚙️ Настройки")]
    ],
    resize_keyboard=True
)

# =========================
# /start
# =========================

@dp.message(CommandStart())
async def start(message: Message):
    user = get_user(message.from_user.id)

    await message.answer(
        "👋 Добро пожаловать в LIFE GAME BOT!\n\n"
        "Ты начинаешь жизнь с нуля...\n"
        "Работай 💼, зарабатывай 💰, покупай бизнесы и развивайся 📈\n\n"
        "Нажми кнопку ниже, чтобы начать 👇",
        reply_markup=main_keyboard
    )

# =========================
# ПРОФИЛЬ
# =========================

@dp.message(F.text == "👤 Профиль")
async def profile(message: Message):
    user = get_user(message.from_user.id)

    await message.answer(
        f"👤 ПРОФИЛЬ\n\n"
        f"💰 Деньги: {user['money']}\n"
        f"⭐ XP: {user['xp']}\n"
        f"📊 Уровень: {user['level']}\n"
        f"🎂 Возраст (Life Pass): {user['age']}"
    )

# =========================
# ЗАГЛУШКИ МЕНЮ
# =========================

@dp.message(F.text == "💼 Работа")
async def work(message: Message):
    await message.answer("💼 Работы будут добавлены в ЧАСТИ 2")

@dp.message(F.text == "🎮 Мини-игры")
async def games(message: Message):
    await message.answer("🎮 Мини-игры будут добавлены в ЧАСТИ 3")

@dp.message(F.text == "💰 Бизнес")
async def business(message: Message):
    await message.answer("💰 Бизнес будет добавлен в ЧАСТИ 4")

@dp.message(F.text == "🏪 Магазин")
async def shop(message: Message):
    await message.answer("🏪 Магазин будет добавлен в ЧАСТИ 5")

@dp.message(F.text == "⚙️ Настройки")
async def settings(message: Message):
    await message.answer("⚙️ Настройки будут добавлены позже")

# =========================
# ЗАПУСК
# =========================

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
    import random
import time

# =========================
# РАБОТЫ
# =========================

jobs = {
    "💼 Склад (упаковка коробок)": {"money": (300, 600), "xp": (5, 10)},
    "🚚 Доставка курьер": {"money": (400, 900), "xp": (8, 15)},
    "🧹 Уборщик": {"money": (250, 500), "xp": (4, 8)},
}

cooldowns = {}

# =========================
# ВЫПОЛНЕНИЕ РАБОТЫ
# =========================

@dp.message(F.text == "💼 Работа")
async def show_jobs(message: Message):
    text = "💼 ДОСТУПНЫЕ РАБОТЫ:\n\n"
    for job in jobs:
        text += f"{job}\n"
    text += "\n👉 Напиши название работы, чтобы начать"
    await message.answer(text)

@dp.message()
async def do_job(message: Message):
    user_id = message.from_user.id
    user = get_user(user_id)

    text = message.text

    if text in jobs:

        # анти-спам (10 секунд)
        now = time.time()
        if user_id in cooldowns and now - cooldowns[user_id] < 10:
            await message.answer("⏳ Подожди немного перед следующей работой!")
            return

        cooldowns[user_id] = now

        job = jobs[text]

        money = random.randint(*job["money"])
        xp = random.randint(*job["xp"])

        user["money"] += money
        user["xp"] += xp

        # уровень
        if user["xp"] >= user["level"] * 50:
            user["xp"] = 0
            user["level"] += 1
            user["age"] += 1

            await message.answer(
                f"🎉 НОВЫЙ УРОВЕНЬ!\n"
                f"📊 Уровень: {user['level']}\n"
                f"🎂 Ты стал старше!"
            )

        await message.answer(
            f"💼 Работа выполнена!\n\n"
            f"+{money} 💰\n"
            f"+{xp} ⭐ XP"
        )
        import random

# =========================
# РУЛЕТКА (2000$)
# =========================

@dp.message(F.text == "🎮 Мини-игры")
async def games_menu(message: Message):
    await message.answer(
        "🎮 МИНИ-ИГРЫ:\n\n"
        "🎰 Рулетка (2000$)\n"
        "🎲 Угадай число\n"
        "📈 Ставка вверх/вниз\n\n"
        "👉 Напиши: рулетка / число / ставка"
    )

# =========================
# РУЛЕТКА
# =========================

@dp.message(F.text.lower() == "рулетка")
async def roulette(message: Message):
    user = get_user(message.from_user.id)

    if user["money"] < 2000:
        await message.answer("❌ Нужно 2000$ для игры!")
        return

    user["money"] -= 2000

    roll = random.randint(1, 100)

    if roll == 1:
        reward = 5000
        text = "🎉 JACKPOT! VIP на 3 дня (условно) + деньги"
    elif roll < 10:
        reward = 3000
        text = "🔥 КРУПНЫЙ ВЫИГРЫШ!"
    elif roll < 40:
        reward = 1000
        text = "🙂 Небольшой выигрыш"
    else:
        reward = 0
        text = "💀 Не повезло"

    user["money"] += reward
    user["xp"] += 10

    await message.answer(f"🎰 РУЛЕТКА\n\n{text}\n+{reward}$\n+10 XP")

# =========================
# УГАДАЙ ЧИСЛО
# =========================

guess_games = {}

@dp.message(F.text.lower().startswith("число"))
async def guess_number(message: Message):
    user_id = message.from_user.id
    user = get_user(user_id)

    try:
        guess = int(message.text.split()[1])
    except:
        await message.answer("👉 Напиши так: число 5")
        return

    secret = random.randint(1, 10)

    if guess == secret:
        reward = 1500
        user["money"] += reward
        user["xp"] += 15
        await message.answer(f"🎉 Угадал! +{reward}$ +15 XP")
    else:
        await message.answer(f"❌ Не угадал! Было число {secret}")

# =========================
# СТАВКА ВВЕРХ / ВНИЗ
# =========================

@dp.message(F.text.lower().startswith("ставка"))
async def bet_game(message: Message):
    user = get_user(message.from_user.id)

    parts = message.text.lower().split()

    if len(parts) < 3:
        await message.answer("👉 Пример: ставка вверх 1000")
        return

    direction = parts[1]
    amount = int(parts[2])

    if user["money"] < amount:
        await message.answer("❌ Недостаточно денег")
        return

    user["money"] -= amount

    result = random.choice(["вверх", "вниз"])

    if direction == result:
        win = amount * 2
        user["money"] += win
        user["xp"] += 20
        await message.answer(f"📈 Победа! +{win}$ +20 XP")
    else:
        await message.answer(f"📉 Проигрыш! Было: {result}")
        import asyncio

# =========================
# БИЗНЕС СИСТЕМА
# =========================

businesses = {}

business_list = {
    "☕ Кофейня": 200,
    "🍔 Фастфуд": 350,
    "🚕 Мини-такси": 500,
    "🏪 Киоск": 700,
    "🏢 Офис": 1200
}

# =========================
# ПОКУПКА БИЗНЕСА
# =========================

@dp.message(F.text.lower().startswith("купить"))
async def buy_business(message: Message):
    user = get_user(message.from_user.id)
    name = message.text.replace("купить", "").strip()

    if name not in business_list:
        await message.answer("❌ Нет такого бизнеса")
        return

    price = business_list[name]

    if user["money"] < price:
        await message.answer("❌ Недостаточно денег")
        return

    user["money"] -= price

    if message.from_user.id not in businesses:
        businesses[message.from_user.id] = []

    businesses[message.from_user.id].append({
        "name": name,
        "income": max(10, price // 10)
    })

    await message.answer(f"🏢 Куплен бизнес: {name}\n💰 Доход: +{price // 10}/мин")

# =========================
# ПАССИВНЫЙ ДОХОД
# =========================

async def income_loop():
    while True:
        await asyncio.sleep(60)

        for user_id in list(businesses.keys()):
            user = users.get(user_id)
            if not user:
                continue

            for b in businesses[user_id]:
                user["money"] += b["income"]
                user["xp"] += 2

# =========================
# ЖИЛЬЁ
# =========================

houses = {
    "🏠 Квартира": 3000,
    "🏡 Дом": 8000,
    "🏰 Особняк": 20000
}

realty = {}

@dp.message(F.text.lower().startswith("жилье"))
async def buy_house(message: Message):
    user = get_user(message.from_user.id)
    name = message.text.replace("жилье", "").strip()

    if name not in houses:
        await message.answer("❌ Нет такого жилья")
        return

    price = houses[name]

    if user["money"] < price:
        await message.answer("❌ Недостаточно денег")
        return

    user["money"] -= price
    realty[message.from_user.id] = name

    await message.answer(f"🏠 Куплено жильё: {name}")
    import asyncio
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message

TOKEN = "YOUR_TOKEN_HERE"
ADMIN_ID = 123456789

bot = Bot(token=TOKEN)
dp = Dispatcher()

# =========================
# БАЗОВЫЕ ДАННЫЕ
# =========================

users = {}

def get_user(user_id: int):
    if user_id not in users:
        users[user_id] = {
            "money": 0,
            "xp": 0,
            "level": 1
        }
    return users[user_id]

# =========================
# VIP + ИНВЕНТАРЬ
# =========================

vip_users = {}
inventory = {}
daily_claim = {}

# =========================
# МАГАЗИН
# =========================

shop = {
    "vip_1": 5000,
    "vip_5": 10000,
    "vip_10": 15000,
    "energy": 2000,
    "x2_income": 4000
}

# =========================
# МАГАЗИН КОМАНДА
# =========================

@dp.message(F.text.lower() == "магазин")
async def shop_menu(message: Message):
    await message.answer(
        "🏪 МАГАЗИН:\n\n"
        "vip_1 - 5000$\n"
        "vip_5 - 10000$\n"
        "vip_10 - 15000$\n"
        "energy - 2000$\n"
        "x2_income - 4000$\n\n"
        "Напиши: купить <предмет>"
    )

# =========================
# ПОКУПКА
# =========================

@dp.message(F.text.lower().startswith("купить"))
async def buy_item(message: Message):
    user = get_user(message.from_user.id)

    name = message.text.replace("купить", "").strip().lower()

    if name not in shop:
        return

    price = shop[name]

    if user["money"] < price:
        await message.answer("❌ Нет денег")
        return

    user["money"] -= price

    inventory.setdefault(message.from_user.id, []).append(name)

    if "vip" in name:
        vip_users[message.from_user.id] = name

    await message.answer(f"✅ Куплено: {name}")

# =========================
# ЕЖЕДНЕВНЫЙ БОНУС
# =========================

@dp.message(F.text.lower() == "бонус")
async def daily_bonus(message: Message):
    user = get_user(message.from_user.id)

    now = datetime.now()

    if message.from_user.id in daily_claim:
        if now - daily_claim[message.from_user.id] < timedelta(hours=24):
            await message.answer("⏳ Уже получал бонус")
            return

    user["money"] += 5000
    user["xp"] += 20

    daily_claim[message.from_user.id] = now

    await message.answer("🎁 +5000$ +20 XP")

# =========================
# VIP БОНУС
# =========================

def vip_bonus(user_id: int):
    if user_id not in vip_users:
        return 1

    vip = vip_users[user_id]

    if vip == "vip_1":
        return 1.2
    if vip == "vip_5":
        return 1.5
    if vip == "vip_10":
        return 2

    return 1

# =========================
# ИНВЕНТАРЬ
# =========================

@dp.message(F.text.lower() == "инвентарь")
async def show_inventory(message: Message):
    items = inventory.get(message.from_user.id, [])

    if not items:
        await message.answer("🎒 пусто")
        return

    await message.answer("🎒:\n" + "\n".join(items))

# =========================
# АДМИНКА
# =========================

@dp.message(F.text.lower().startswith("админ деньги"))
async def admin_money(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    _, _, uid, amount = message.text.split()
    users[int(uid)]["money"] += int(amount)

    await message.answer("💰 готово")

@dp.message(F.text.lower().startswith("админ xp"))
async def admin_xp(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    _, _, uid, amount = message.text.split()
    users[int(uid)]["xp"] += int(amount)

    await message.answer("⭐ готово")
    import random
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# =========================
# МЕНЮ (КНОПКИ ВНИЗ)
# =========================

menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="профиль"), KeyboardButton(text="магазин")],
        [KeyboardButton(text="работа"), KeyboardButton(text="бизнес")],
        [KeyboardButton(text="мини-игры"), KeyboardButton(text="топ деньги")],
        [KeyboardButton(text="топ xp"), KeyboardButton(text="рулетка")],
    ],
    resize_keyboard=True
)

@dp.message(F.text.lower() == "start")
async def start(message: Message):
    await message.answer(
        "👋 Добро пожаловать в Life Game!\n\n"
        "Развивайся, работай, покупай бизнес и становись богатым 💰",
        reply_markup=menu
    )

# =========================
# ПРОФИЛЬ
# =========================

@dp.message(F.text.lower() == "профиль")
async def profile(message: Message):
    user = get_user(message.from_user.id)

    await message.answer(
        f"👤 ПРОФИЛЬ\n\n"
        f"💰 Деньги: {user['money']}$\n"
        f"⭐ XP: {user['xp']}\n"
        f"📊 Level: {user['level']}"
    )

# =========================
# LEVEL SYSTEM (LIFE PASS)
# =========================

def update_level(user):
    user["level"] = user["xp"] // 50 + 1

async def level_loop():
    while True:
        await asyncio.sleep(10)

        for user in users.values():
            update_level(user)

# =========================
# ТОП ДЕНЬГИ
# =========================

@dp.message(F.text.lower() == "топ деньги")
async def top_money(message: Message):
    top = sorted(users.items(), key=lambda x: x[1]["money"], reverse=True)[:3]

    text = "🏆 ТОП БОГАТЫХ:\n\n"

    for i, (uid, data) in enumerate(top, 1):
        text += f"{i}. ID {uid} — {data['money']}$\n"

    await message.answer(text)

# =========================
# ТОП XP
# =========================

@dp.message(F.text.lower() == "топ xp")
async def top_xp(message: Message):
    top = sorted(users.items(), key=lambda x: x[1]["xp"], reverse=True)[:3]

    text = "🏆 ТОП XP:\n\n"

    for i, (uid, data) in enumerate(top, 1):
        text += f"{i}. ID {uid} — {data['xp']} XP\n"

    await message.answer(text)

# =========================
# МИНИ-ИГРА: УГАДАЙ ЧИСЛО
# =========================

@dp.message(F.text.lower() == "угадай число")
async def guess_start(message: Message):
    user = get_user(message.from_user.id)

    user["guess"] = random.randint(1, 6)

    await message.answer("🎲 Угадай число от 1 до 6")

@dp.message(F.text.isdigit())
async def guess_play(message: Message):
    user = get_user(message.from_user.id)

    if "guess" not in user:
        return

    if int(message.text) == user["guess"]:
        user["money"] += 1000
        user["xp"] += 10
        await message.answer("✅ Победа +1000$ +10 XP")
    else:
        await message.answer("❌ Не угадал")

    del user["guess"]

# =========================
# РУЛЕТКА
# =========================

@dp.message(F.text.lower() == "рулетка")
async def roulette(message: Message):
    user = get_user(message.from_user.id)

    if user["money"] < 2000:
        await message.answer("❌ Нужно 2000$")
        return

    user["money"] -= 2000

    reward = random.choice([
        0,
        1000,
        3000,
        5000,
        "vip_1",
        "vip_5"
    ])

    if reward == 0:
        await message.answer("💀 проигрыш")
        return

    if isinstance(reward, str):
        vip_users[message.from_user.id] = reward
        await message.answer(f"🎰 VIP получен: {reward}")
    else:
        user["money"] += reward
        await message.answer(f"🎰 выигрыш +{reward}$")

# =========================
# ЗАПУСК LEVEL LOOP
# =========================

asyncio.create_task(level_loop())
import sqlite3

# =========================
# БАЗА ДАННЫХ (СОХРАНЕНИЕ)
# =========================

conn = sqlite3.connect("game.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    money INTEGER,
    xp INTEGER,
    level INTEGER
)
""")

conn.commit()

# =========================
# ЗАГРУЗКА / СОЗДАНИЕ ЮЗЕРА
# =========================

def get_user(user_id: int):
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    data = cursor.fetchone()

    if data is None:
        cursor.execute(
            "INSERT INTO users VALUES (?, ?, ?, ?)",
            (user_id, 0, 0, 1)
        )
        conn.commit()

        return {
            "user_id": user_id,
            "money": 0,
            "xp": 0,
            "level": 1
        }

    return {
        "user_id": data[0],
        "money": data[1],
        "xp": data[2],
        "level": data[3]
    }

# =========================
# СОХРАНЕНИЕ ЮЗЕРА
# =========================

def save_user(user):
    cursor.execute("""
        UPDATE users
        SET money=?, xp=?, level=?
        WHERE user_id=?
    """, (user["money"], user["xp"], user["level"], user["user_id"]))

    conn.commit()

# =========================
# АВТО-СОХРАНЕНИЕ (ЧТОБ НЕ ЛОМАЛОСЬ)
# =========================

async def autosave_loop():
    while True:
        await asyncio.sleep(30)

        for user_id, user in users.items():
            save_user({
                "user_id": user_id,
                "money": user["money"],
                "xp": user["xp"],
                "level": user["level"]
            })

# =========================
# ЗАМЕНА USERS (ВАЖНО)
# =========================

users = {}

# =========================
# ПЕРЕХВАТ ПРИ СТАРТЕ
# =========================

asyncio.create_task(autosave_loop())
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# =========================
# ГЛАВНОЕ МЕНЮ (НИЖНЯЯ ПАНЕЛЬ)
# =========================

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="👤 Профиль"),
            KeyboardButton(text="💼 Работа")
        ],
        [
            KeyboardButton(text="🎮 Мини-игры"),
            KeyboardButton(text="🏦 Бизнес")
        ],
        [
            KeyboardButton(text="🛒 Магазин"),
            KeyboardButton(text="⚙️ Настройки")
        ],
        [
            KeyboardButton(text="🏠 Жильё"),
            KeyboardButton(text="📊 Рейтинг")
        ]
    ],
    resize_keyboard=True
)

# =========================
# КНОПКА НАЗАД
# =========================

back_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🔙 Назад")]
    ],
    resize_keyboard=True
)

# =========================
# СТАРТ (ВХОД В ИГРУ)
# =========================

@dp.message_handler(commands=["start"])
async def start(message):
    user = get_user(message.from_user.id)

    await message.answer(
        "👋 Добро пожаловать в Life Game!\n"
        "Ты начинаешь свою жизнь с нуля...\n\n"
        "💡 Зарабатывай, покупай бизнес, развивайся и становись богатым!",
        reply_markup=main_menu
    )
    from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# =========================
# АДМИН МЕНЮ
# =========================

admin_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="💰 Выдать деньги"), KeyboardButton(text="📉 Забрать деньги")],
        [KeyboardButton(text="⭐ Выдать XP"), KeyboardButton(text="📊 Статистика")],
        [KeyboardButton(text="🔙 Назад")]
    ],
    resize_keyboard=True
)

# =========================
# ОТКРЫТИЕ АДМИН ПАНЕЛИ
# =========================

@dp.message_handler(lambda message: message.text == "🔐 Админ панель")
async def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ Нет доступа")
        return

    await message.answer("🔐 Админ панель открыта", reply_markup=admin_menu)


# =========================
# ВЫДАЧА ДЕНЕГ
# =========================

@dp.message_handler(lambda message: message.text.startswith("💰 Выдать деньги"))
async def give_money(message):
    if message.from_user.id != ADMIN_ID:
        return

    try:
        parts = message.text.split()
        user_id = int(parts[3])
        amount = int(parts[4])

        user = get_user(user_id)
        user["money"] += amount
        save_user(user)

        await message.answer("✅ Деньги выданы")

    except:
        await message.answer("❌ Формат: 💰 Выдать деньги ID сумма")


# =========================
# ЗАБРАТЬ ДЕНЬГИ
# =========================

@dp.message_handler(lambda message: message.text.startswith("📉 Забрать деньги"))
async def take_money(message):
    if message.from_user.id != ADMIN_ID:
        return

    try:
        parts = message.text.split()
        user_id = int(parts[3])
        amount = int(parts[4])

        user = get_user(user_id)
        user["money"] -= amount
        save_user(user)

        await message.answer("✅ Деньги забраны")

    except:
        await message.answer("❌ Формат: 📉 Забрать деньги ID сумма")


# =========================
# ВЫДАТЬ XP
# =========================

@dp.message_handler(lambda message: message.text.startswith("⭐ Выдать XP"))
async def give_xp(message):
    if message.from_user.id != ADMIN_ID:
        return

    try:
        parts = message.text.split()
        user_id = int(parts[3])
        amount = int(parts[4])

        user = get_user(user_id)
        user["xp"] += amount
        save_user(user)

        await message.answer("✅ XP выдано")

    except:
        await message.answer("❌ Формат: ⭐ Выдать XP ID сумма")


# =========================
# СТАТИСТИКА
# =========================

@dp.message_handler(lambda message: message.text == "📊 Статистика")
async def stats(message):
    if message.from_user.id != ADMIN_ID:
        return

    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]

    await message.answer(
        f"📊 СТАТИСТИКА\n\n"
        f"👤 Игроков: {count}\n"
        f"💾 База: SQLite\n"
        f"⚙️ Бот активен"
    )


# =========================
# ЗАЩИТА: ТОЛЬКО ДЛЯ АДМИНА
# =========================

def is_admin(user_id: int):
    return user_id == ADMIN_ID
    # =========================
# ЛАЙФ-ПАСС (УРОВНИ)
# =========================

def xp_for_level(level: int):
    # плавное усложнение
    return 50 + (level * 25)


def add_xp(user, amount: int):
    user["xp"] += amount

    # уровень апается
    while user["xp"] >= xp_for_level(user["level"]):
        user["xp"] -= xp_for_level(user["level"])
        user["level"] += 1

    return user


# =========================
# ДЕНЬГИ (БЕЗ УХОДА В ОГРОМНЫЙ МИНУС)
# =========================

def add_money(user, amount: int):
    user["money"] += amount
    return user


def remove_money(user, amount: int):
    user["money"] -= amount

    # ограничение: можно в минус, но с штрафом логики (пока мягко)
    if user["money"] < -5000:
        user["money"] = -5000

    return user


# =========================
# ЕЖЕДНЕВНЫЙ БОНУС
# =========================

import time

DAILY_REWARD_MONEY = 8000
DAILY_REWARD_XP = 20
COOLDOWN = 60 * 60 * 24

# временное хранилище (позже можно в SQLite)
last_daily = {}


async def give_daily_bonus(message):
    user_id = message.from_user.id
    user = get_user(user_id)

    now = time.time()

    if user_id in last_daily:
        if now - last_daily[user_id] < COOLDOWN:
            await message.answer("⏳ Ты уже получил ежедневный бонус")
            return

    user = add_money(user, DAILY_REWARD_MONEY)
    user = add_xp(user, DAILY_REWARD_XP)

    save_user(user)
    last_daily[user_id] = now

    await message.answer(
        f"🎁 ЕЖЕДНЕВНЫЙ БОНУС\n\n"
        f"+{DAILY_REWARD_MONEY} 💰\n"
        f"+{DAILY_REWARD_XP} XP"
    )


# =========================
# БАЗОВЫЙ ПРОФИЛЬ
# =========================

@dp.message_handler(lambda message: message.text == "👤 Профиль")
async def profile(message):
    user = get_user(message.from_user.id)

    await message.answer(
        f"👤 ПРОФИЛЬ\n\n"
        f"💰 Деньги: {user['money']}\n"
        f"⭐ XP: {user['xp']}\n"
        f"📊 Уровень: {user['level']}\n\n"
        f"📈 До следующего уровня: {xp_for_level(user['level']) - user['xp']} XP"
    )
    import random

# =========================
# БАЗОВЫЕ НАГРАДЫ
# =========================

def reward(user, money=0, xp=0):
    user["money"] += money
    user["xp"] += xp
    return user


# =========================
# 🎰 РУЛЕТКА
# =========================

@dp.message_handler(lambda message: message.text == "🎮 Мини-игры")
async def games_menu(message):
    await message.answer(
        "🎮 МИНИ-ИГРЫ\n\n"
        "🎰 рулетка\n"
        "🎲 угадай число\n"
        "📈 ставки вверх/вниз\n\n"
        "Выбери действие (команды ниже):"
    )


@dp.message_handler(lambda message: message.text == "🎰 рулетка")
async def roulette(message):
    user = get_user(message.from_user.id)

    cost = 2000
    if user["money"] < cost:
        await message.answer("❌ Не хватает денег (2000)")
        return

    user["money"] -= cost

    roll = random.randint(1, 100)

    # 🎁 призы
    if roll <= 3:
        user["money"] += 20000
        user["xp"] += 50
        result = "JACKPOT 💥 +20000"
    elif roll <= 10:
        user["money"] += 8000
        user["xp"] += 25
        result = "💰 Большой выигрыш +8000"
    elif roll <= 40:
        user["money"] += 3000
        user["xp"] += 15
        result = "🙂 Выигрыш +3000"
    else:
        result = "💀 Проигрыш"

    save_user(user)

    await message.answer(f"🎰 РУЛЕТКА\n\n{result}")


# =========================
# 🎲 УГАДАЙ ЧИСЛО
# =========================

user_guess_game = {}

@dp.message_handler(lambda message: message.text == "🎲 угадай число")
async def guess_start(message):
    number = random.randint(1, 6)
    user_guess_game[message.from_user.id] = number

    await message.answer("🎲 Угадай число от 1 до 6")


@dp.message_handler(lambda message: message.text.isdigit())
async def guess_check(message):
    user_id = message.from_user.id

    if user_id not in user_guess_game:
        return

    user = get_user(user_id)
    guess = int(message.text)
    target = user_guess_game[user_id]

    if guess == target:
        user = reward(user, money=5000, xp=20)
        result = "✅ Верно! +5000 и +20 XP"
    else:
        result = f"❌ Неверно! Было {target}"

    del user_guess_game[user_id]
    save_user(user)

    await message.answer(result)


# =========================
# 📈 СТАВКИ (UP/DOWN)
# =========================

@dp.message_handler(lambda message: message.text == "📈 ставки вверх/вниз")
async def bet_game(message):
    user = get_user(message.from_user.id)

    if user["money"] < 1000:
        await message.answer("❌ Нужно минимум 1000")
        return

    user["money"] -= 1000

    result = random.choice(["UP", "DOWN"])
    user_choice = random.choice(["UP", "DOWN"])

    if result == user_choice:
        user["money"] += 3000
        user["xp"] += 10
        msg = "🎉 Победа +3000"
    else:
        msg = "💀 Проигрыш"

    save_user(user)

    await message.answer(f"📈 СТАВКА\n\n{msg}")


# =========================
# 🧠 ЛОГИКА (СЛОВО ИЗ БУКВ)
# =========================

word_game = {}

@dp.message_handler(lambda message: message.text == "🧠 логика")
async def logic_start(message):
    words = ["работа", "деньги", "бизнес", "жизнь"]
    word = random.choice(words)

    scrambled = list(word)
    random.shuffle(scrambled)

    scrambled = "".join(scrambled)

    word_game[message.from_user.id] = word

    await message.answer(f"🧠 Собери слово:\n\n{scrambled}")


@dp.message_handler()
async def logic_check(message):
    user_id = message.from_user.id

    if user_id not in word_game:
        return

    user = get_user(user_id)

    if message.text.lower() == word_game[user_id]:
        user = reward(user, money=4000, xp=20)
        result = "✅ Верно! +4000 и +20 XP"
    else:
        result = "❌ Неверно"

    del word_game[user_id]
    save_user(user)

    await message.answer(result)
    import time

# =========================
# РАБОТЫ (СТАРТОВЫЕ И ПРОГРЕСС)
# =========================

jobs = {
    "склад": {"money": 500, "xp": 5, "cooldown": 30},
    "доставка": {"money": 800, "xp": 8, "cooldown": 45},
    "уборщик": {"money": 600, "xp": 6, "cooldown": 40},

    "кассир": {"money": 1200, "xp": 10, "cooldown": 60},
    "офис": {"money": 2000, "xp": 15, "cooldown": 90},
    "стройка": {"money": 2500, "xp": 18, "cooldown": 120},
}

# =========================
# ВЫБОР РАБОТЫ
# =========================

user_jobs = {}
last_job_time = {}


@dp.message_handler(lambda message: message.text == "💼 Работа")
async def job_menu(message):
    await message.answer(
        "💼 РАБОТЫ\n\n"
        "склад\n"
        "доставка\n"
        "уборщик\n"
        "кассир\n"
        "офис\n"
        "стройка\n\n"
        "Напиши название работы"
    )


# =========================
# ВЫПОЛНЕНИЕ РАБОТЫ
# =========================

@dp.message_handler()
async def do_job(message):
    user_id = message.from_user.id
    text = message.text.lower()

    if text not in jobs:
        return

    user = get_user(user_id)

    # cooldown проверка
    if user_id in last_job_time:
        if time.time() - last_job_time[user_id] < jobs[text]["cooldown"]:
            await message.answer("⏳ Подожди перед следующей работой")
            return

    last_job_time[user_id] = time.time()

    reward_money = jobs[text]["money"]
    reward_xp = jobs[text]["xp"]

    user["money"] += reward_money
    user["xp"] += reward_xp

    save_user(user)

    await message.answer(
        f"💼 Работа: {text}\n\n"
        f"+{reward_money} 💰\n"
        f"+{reward_xp} XP"
    )


# =========================
# СМЕНА РАБОТЫ
# =========================

@dp.message_handler(lambda message: message.text == "🔄 сменить работу")
async def reset_job(message):
    user_jobs[message.from_user.id] = None
    await message.answer("🔄 Работа сброшена")
    import time

# =========================
# БИЗНЕСЫ
# =========================

businesses = {
    "киоск": {"price": 10000, "income": 200, "level": 1},
    "кофейня": {"price": 25000, "income": 500, "level": 1},
    "такси": {"price": 40000, "income": 800, "level": 1},

    "фастфуд": {"price": 80000, "income": 1500, "level": 1},
    "сеть киосков": {"price": 120000, "income": 2200, "level": 1},
    "офисный центр": {"price": 300000, "income": 5000, "level": 1},
}

# =========================
# ДАННЫЕ ПОЛЬЗОВАТЕЛЯ
# =========================

user_business = {}
last_business_income = {}

# =========================
# ПОКУПКА БИЗНЕСА
# =========================

@dp.message_handler(lambda message: message.text == "🏦 Бизнес")
async def business_menu(message):
    await message.answer(
        "🏦 БИЗНЕСЫ\n\n"
        "киоск\n"
        "кофейня\n"
        "такси\n"
        "фастфуд\n"
        "сеть киосков\n"
        "офисный центр\n\n"
        "Напиши название бизнеса для покупки"
    )


@dp.message_handler()
async def buy_business(message):
    user_id = message.from_user.id
    text = message.text.lower()

    if text not in businesses:
        return

    user = get_user(user_id)

    if user["money"] < businesses[text]["price"]:
        await message.answer("❌ Не хватает денег")
        return

    user["money"] -= businesses[text]["price"]

    user_business[user_id] = {
        "name": text,
        "level": 1
    }

    save_user(user)

    await message.answer(
        f"🏦 Куплен бизнес: {text}\n"
        f"💰 Доход: {businesses[text]['income']} / мин"
    )

# =========================
# ПАССИВНЫЙ ДОХОД (КАЖДУЮ МИНУТУ)
# =========================

async def business_income_loop():
    while True:
        await asyncio.sleep(60)

        for user_id, biz in user_business.items():

            user = get_user(user_id)

            income = businesses[biz["name"]]["income"]

            # рост дохода от уровня бизнеса
            income = income * biz["level"]

            user["money"] += income

            save_user(user)

# =========================
# ЗАПУСК ПЕТЛИ
# =========================

asyncio.create_task(business_income_loop())

# =========================
# ПРОДАЖА БИЗНЕСА
# =========================

@dp.message_handler(lambda message: message.text == "💸 продать бизнес")
async def sell_business(message):
    user_id = message.from_user.id

    if user_id not in user_business:
        await message.answer("❌ У тебя нет бизнеса")
        return

    biz = user_business[user_id]
    price = businesses[biz["name"]]["price"]

    refund = int(price * 0.65)

    user = get_user(user_id)
    user["money"] += refund

    del user_business[user_id]

    save_user(user)

    await message.answer(f"💸 Бизнес продан за {refund} 💰")
    # =========================
# VIP СИСТЕМА
# =========================

vip_users = {}

vip_prices = {
    1: 5000,   # 1 день
    5: 10000,  # 5 дней
    10: 15000  # 10 дней
}

# =========================
# МАГАЗИН
# =========================

boosts = {
    "x2_income": {"price": 5000, "duration": 3600 * 5},
    "energy": {"price": 2000, "duration": 7200},
}

# =========================
# ЖИЛЬЁ
# =========================

housing = {
    "студия": {"price": 20000, "income_bonus": 1.1},
    "квартира": {"price": 50000, "income_bonus": 1.3},
    "дом": {"price": 120000, "income_bonus": 1.5},
    "особняк": {"price": 300000, "income_bonus": 2.0, "vip_only": True},
}

user_housing = {}

# =========================
# VIP ПОКУПКА
# =========================

@dp.message_handler(lambda message: message.text == "⭐ VIP")
async def vip_menu(message):
    await message.answer(
        "⭐ VIP ПАКЕТЫ\n\n"
        "1 день — 5000 💰\n"
        "5 дней — 10000 💰\n"
        "10 дней — 15000 💰\n\n"
        "Напиши: vip 1 / vip 5 / vip 10"
    )


@dp.message_handler(lambda message: message.text.startswith("vip"))
async def buy_vip(message):
    user_id = message.from_user.id
    user = get_user(user_id)

    try:
        days = int(message.text.split()[1])
    except:
        return

    if days not in vip_prices:
        return

    price = vip_prices[days]

    if user["money"] < price:
        await message.answer("❌ Нет денег")
        return

    user["money"] -= price

    vip_users[user_id] = time.time() + days * 86400

    save_user(user)

    await message.answer(f"⭐ VIP активирован на {days} дней")

# =========================
# ПРОВЕРКА VIP
# =========================

def is_vip(user_id):
    return user_id in vip_users and vip_users[user_id] > time.time()

# =========================
# МАГАЗИН БУСТОВ
# =========================

@dp.message_handler(lambda message: message.text == "🛒 магазин")
async def shop(message):
    await message.answer(
        "🛒 МАГАЗИН\n\n"
        "x2 доход — 5000 💰\n"
        "энергетик — 2000 💰\n\n"
        "Напиши: buy x2 / buy energy"
    )


@dp.message_handler(lambda message: message.text.startswith("buy"))
async def buy_item(message):
    user_id = message.from_user.id
    user = get_user(user_id)

    item = message.text.split()[1]

    if item not in boosts:
        return

    price = boosts[item]["price"]

    if user["money"] < price:
        await message.answer("❌ Нет денег")
        return

    user["money"] -= price
    save_user(user)

    await message.answer(f"✔ Куплено: {item}")

# =========================
# ЖИЛЬЁ
# =========================

@dp.message_handler(lambda message: message.text == "🏠 жильё")
async def housing_menu(message):
    await message.answer(
        "🏠 ЖИЛЬЁ\n\n"
        "студия — 20k\n"
        "квартира — 50k\n"
        "дом — 120k\n"
        "особняк (VIP) — 300k\n\n"
        "Напиши: buyhouse название"
    )


@dp.message_handler(lambda message: message.text.startswith("buyhouse"))
async def buy_house(message):
    user_id = message.from_user.id
    user = get_user(user_id)

    name = message.text.split()[1]

    if name not in housing:
        return

    if housing[name].get("vip_only") and not is_vip(user_id):
        await message.answer("❌ Только для VIP")
        return

    price = housing[name]["price"]

    if user["money"] < price:
        await message.answer("❌ Нет денег")
        return

    user["money"] -= price

    user_housing[user_id] = name

    save_user(user)

    await message.answer(f"🏠 Куплено жильё: {name}")

# =========================
# АДМИН ПАНЕЛЬ (ТОЛЬКО ТЫ)
# =========================

ADMIN_ID = 123456789  # <-- ВСТАВЬ СВОЙ TELEGRAM ID СЮДА

def is_admin(user_id):
    return user_id == ADMIN_ID

@dp.message_handler(lambda message: message.text.startswith("админ"))
async def admin_panel(message):
    if not is_admin(message.from_user.id):
        return

    await message.answer(
        "⚙ АДМИН ПАНЕЛЬ\n\n"
        "админ give money ID 10000\n"
        "админ take money ID 5000\n"
        "админ give xp ID 50\n"
    )


@dp.message_handler(lambda message: message.text.startswith("админ give"))
async def admin_give(message):
    if not is_admin(message.from_user.id):
        return

    parts = message.text.split()

    target_id = int(parts[3])
    amount = int(parts[4])

    user = get_user(target_id)

    if parts[2] == "money":
        user["money"] += amount

    if parts[2] == "xp":
        user["xp"] += amount

    save_user(user)

    await message.answer("✔ Выдано")


@dp.message_handler(lambda message: message.text.startswith("админ take"))
async def admin_take(message):
    if not is_admin(message.from_user.id):
        return

    parts = message.text.split()

    target_id = int(parts[3])
    amount = int(parts[4])

    user = get_user(target_id)

    if parts[2] == "money":
        user["money"] -= amount

    if parts[2] == "xp":
        user["xp"] -= amount

    save_user(user)

    await message.answer("✔ Забрано")

# =========================
# ЕЖЕДНЕВНЫЙ БОНУС
# =========================

daily_bonus = {}

@dp.message_handler(lambda message: message.text == "🎁 бонус")
async def bonus(message):
    user_id = message.from_user.id
    user = get_user(user_id)

    if user_id in daily_bonus and time.time() - daily_bonus[user_id] < 86400:
        await message.answer("⏳ Уже получено сегодня")
        return

    daily_bonus[user_id] = time.time()

    user["money"] += 8000
    user["xp"] += 20

    save_user(user)

    await message.answer("🎁 Бонус получен: 8000 💰 + 20 XP")
    # =========================
# 🔚 ФИНАЛЬНАЯ ЧАСТЬ БОТА
# =========================

# --- ADMIN ID (ТОЛЬКО ТВОЙ ID) ---
ADMIN_ID = 7303801260  # ← сюда вставь свой Telegram ID

# --- ПРОВЕРКА АДМИНА ---
def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID


# =========================
# 🛠 АДМИН-ПАНЕЛЬ
# =========================

@dp.message(Command("admin"))
async def admin_panel(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 Статистика")],
            [KeyboardButton(text="💰 Выдать деньги")],
            [KeyboardButton(text="➖ Забрать деньги")],
            [KeyboardButton(text="⭐ Выдать XP")],
            [KeyboardButton(text="⬅️ Выход")]
        ],
        resize_keyboard=True
    )

    await message.answer("🛠 Админ-панель открыта", reply_markup=kb)


# =========================
# 📊 СТАТИСТИКА БОТА
# =========================

@dp.message(lambda m: m.text == "📊 Статистика")
async def stats(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    # пример (если SQLite)
    cursor.execute("SELECT COUNT(*) FROM users")
    users = cursor.fetchone()[0]

    await message.answer(
        f"📊 Статистика бота:\n\n"
        f"👤 Пользователей: {users}\n"
    )


# =========================
# 💰 ВЫДАЧА ДЕНЕГ
# =========================

@dp.message(lambda m: m.text == "💰 Выдать деньги")
async def give_money(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    await message.answer("Введите: ID сумма")


# =========================
# ➖ ЗАБРАТЬ ДЕНЬГИ
# =========================

@dp.message(lambda m: m.text == "➖ Забрать деньги")
async def take_money(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    await message.answer("Введите: ID сумма")


# =========================
# ⭐ ВЫДАТЬ XP
# =========================

@dp.message(lambda m: m.text == "⭐ Выдать XP")
async def give_xp(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    await message.answer("Введите: ID XP")


# =========================
# 🔁 ЗАПУСК БОТА
# =========================

async def main():
    print("🤖 Бот запущен...")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())