import asyncio
import logging  # Добавили логирование, чтобы видеть ошибки
import sqlite3
import time
import random


from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    KeyboardButton,
    ReplyKeyboardMarkup
)

# Включаем логирование в консоль
logging.basicConfig(level=logging.INFO)

# ==========================================================
# НАСТРОЙКИ
# ==========================================================

BOT_TOKEN = "8233072384:AAEd6QXeUxz6M5UV-v_0I3SXhpcDdWagDLY"         # <--- Вставьте сюда токен от @BotFather
ADMIN_ID = 7303801260  # <--- Вставьте сюда свой числовой Telegram ID

# ==========================================================
# БАЗА ДАННЫХ SQLITE
# ==========================================================

# Добавили check_same_thread=False, чтобы база данных не выдавала ошибки при частых запросах
database = sqlite3.connect("database.db", check_same_thread=False)
cursor = database.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    telegram_id INTEGER PRIMARY KEY,
    username TEXT,
    coins INTEGER DEFAULT 0,
    vip INTEGER DEFAULT 0,
    luck INTEGER DEFAULT 0,
    last_farm INTEGER DEFAULT 0
)
""")
database.commit()

# ==========================================================
# BOT
# ==========================================================

bot = Bot(token=BOT_TOKEN)
dispatcher = Dispatcher()

# ==========================================================
# ФУНКЦИИ
# ==========================================================

def register_user(user):
    """
    Автоматическая регистрация пользователя.
    """
    cursor.execute(
        "SELECT telegram_id FROM users WHERE telegram_id = ?",
        (user.id,)
    )
    result = cursor.fetchone()

    if result is None:
        # Если у пользователя нет юзернейма (@name), запишем "Пользователь"
        username = user.username if user.username else "Пользователь"
        
        cursor.execute(
            """
            INSERT INTO users (telegram_id, username, coins, vip, luck, last_farm)
            VALUES (?, ?, 0, 0, 0, 0)
            """,
            (user.id, username)
        )
        database.commit()


def get_main_keyboard(user_id: int) -> ReplyKeyboardMarkup:
    """
    Главное меню в клавиатуре (внизу экрана).
    """
    keyboard = [
        [
            KeyboardButton(text="👤 Профиль"),
            KeyboardButton(text="🛒 Магазин")
        ],
        [
            KeyboardButton(text="🎮 Мини-игры")
        ]
    ]

    # Если это админ, добавляем ему кнопку админки
    if user_id == ADMIN_ID:
        keyboard.append([KeyboardButton(text="👑 Админка")])

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True
    )

# ==========================================================
# КОМАНДА START
# ==========================================================

@dispatcher.message(CommandStart())
async def start_command(message: Message):
    register_user(message.from_user)
    
    await message.answer(
        text=(
            f"👋 Добро пожаловать, {message.from_user.full_name}!\n\n"
            "Вы успешно зарегистрированы.\n"
            "Используйте кнопки меню ниже."
        ),
        reply_markup=get_main_keyboard(message.from_user.id)
    )

# ==========================================================
# ЗАПУСК
# ==========================================================

async def main():
    print("Бот успешно запущен и готов к работе!")
    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
@dispatcher.message(F.text == "👤 Профиль")
async def profile(message: Message):

    user = get_user(message.from_user.id)

    coins = user[2]
    vip = user[3]

    if vip == 1:
        status = "👑 VIP"
    else:
        status = "🙂 Обычный"

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🌾 Фарма")
            ],
            [
                KeyboardButton(text="👤 Профиль"),
                KeyboardButton(text="🛒 Магазин")
            ],
            [
                KeyboardButton(text="🎮 Мини-игры")
            ]
        ],
        resize_keyboard=True
    )

    if message.from_user.id == ADMIN_ID:
        keyboard.keyboard.append(
            [
                KeyboardButton(text="👑 Админка")
            ]
        )

    await message.answer(
        text=(
            "👤 <b>Ваш профиль</b>\n\n"
            f"💰 Монет: <b>{coins}</b>\n"
            f"⭐ Статус: <b>{status}</b>"
        ),
        parse_mode="HTML",
        reply_markup=keyboard
    )
@dispatcher.message(F.text == "🌾 Фарма")
async def farm(message: Message):
    user = get_user(message.from_user.id)

    coins = user[2]
    vip = user[3]
    last_farm = user[5]

    now = int(time.time())

    cooldown = 60

    if now - last_farm < cooldown:

        seconds = cooldown - (now - last_farm)

        await message.answer(
            f"⏳ До следующей фармы осталось {seconds} сек."
        )

        return

    reward = 10

    if vip == 1:
        reward *= 2

    coins += reward

    update_coins(
        message.from_user.id,
        coins
    )

    update_last_farm(
        message.from_user.id,
        now
    )

    await message.answer(
        f"🌾 Вы получили {reward} монет!\n\n"
        f"💰 Теперь у вас {coins} монет."
    )
    # ==========================================================
# ПРОФИЛЬ
# ==========================================================

@dispatcher.message(F.text == "👤 Профиль")
async def profile_handler(message: Message):
    user = get_user(message.from_user.id)

    if user is None:
        register_user(message.from_user)
        user = get_user(message.from_user.id)

    username = message.from_user.full_name
    coins = user[2]
    vip = user[3]

    status = "👑 VIP" if vip == 1 else "Обычный"

    profile_keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🌾 Фарма")
            ],
            [
                KeyboardButton(text="🔙 Назад")
            ]
        ],
        resize_keyboard=True
    )

    await message.answer(
        text=(
            f"👤 <b>Профиль</b>\n\n"
            f"Имя: <b>{username}</b>\n"
            f"💰 Монеты: <b>{coins}</b>\n"
            f"⭐ Статус: <b>{status}</b>"
        ),
        parse_mode="HTML",
        reply_markup=profile_keyboard
    )


# ==========================================================
# ФАРМА
# ==========================================================

@dispatcher.message(F.text == "🌾 Фарма")
async def farm_handler(message: Message):
    user = get_user(message.from_user.id)

    if user is None:
        register_user(message.from_user)
        user = get_user(message.from_user.id)

    coins = user[2]
    vip = user[3]
    last_farm = user[5]

    current_time = int(time.time())

    if current_time - last_farm < 60:
        seconds_left = 60 - (current_time - last_farm)

        await message.answer(
            f"⏳ Фармить можно раз в минуту!\n"
            f"Подожди еще {seconds_left} секунд."
        )
        return

    reward = random.randint(10, 50)

    if vip == 1:
        reward *= 2

        await message.answer(
            "🔥 Благодаря VIP-статусу твоя награда удвоена!"
        )

    coins += reward

    update_coins(
        message.from_user.id,
        coins
    )

    update_last_farm(
        message.from_user.id,
        current_time
    )

    await message.answer(
        f"✅ Вы успешно сфармили {reward} монет!\n"
        f"💰 Теперь у вас {coins} монет."
    )


# ==========================================================
# НАЗАД
# ==========================================================

@dispatcher.message(F.text == "🔙 Назад")
async def back_handler(message: Message):
    await message.answer(
        "Главное меню:",
        reply_markup=get_main_keyboard(message.from_user.id)
    )
    async def main():
    print("Бот успешно запущен...")
    await dispatcher.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
