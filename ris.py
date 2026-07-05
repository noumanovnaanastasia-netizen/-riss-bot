import asyncio
import logging
import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import ReplyKeyboardBuilder

# Токен вашего бота
BOT_TOKEN = "8962500881:AAFDttMSkEzQcSGUjljScWX6VpSbew67g58"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# === РАБОТА С БАЗОЙ ДАННЫХ ===
def init_db():
    conn = sqlite3.connect("lifecycle.db")
    cursor = conn.cursor()
    # Создаем таблицу пользователей, если её нет
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            level INTEGER DEFAULT 1,
            xp INTEGER DEFAULT 0,
            bucks INTEGER DEFAULT 100,
            has_house INTEGER DEFAULT 0,
            has_business INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = sqlite3.connect("lifecycle.db")
    cursor = conn.cursor()
    cursor.execute("SELECT level, xp, bucks FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user

def register_user(user_id, username):
    conn = sqlite3.connect("lifecycle.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (user_id, username))
    conn.commit()
    conn.close()

# === ГЛАВНОЕ МЕНЮ (НИЖНЯЯ КЛАВИАТУРА) ===
def get_main_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.row(types.KeyboardButton(text="👤 Мой Профиль"))
    builder.row(types.KeyboardButton(text="💼 Работа / Игры"), types.KeyboardButton(text="🛒 Магазин"))
    builder.row(types.KeyboardButton(text="🎟️ Brawl Pass"))
    return builder.as_markup(resize_keyboard=True, input_field_placeholder="Выберите действие...")

# === ОБРАБОТЧИКИ КОМАНД ===
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    register_user(message.from_user.id, message.from_user.username)
    
    welcome_text = (
        f"👋 *Приветствуем тебя в симуляторе жизни, {message.from_user.first_name}!* \n\n"
        "🌍 Здесь тебе предстоит пройти путь от обычного работяги до владельца корпораций.\n"
        "📈 Зарабатывай *Баксы*, копи *XP* (твои годы жизни), открывай бизнесы и дома!\n\n"
        "👉 Нажимай на кнопки внизу, чтобы управлять своей жизнью!"
    )
    await message.answer(welcome_text, parse_mode="Markdown", reply_markup=get_main_keyboard())

@dp.message(lambda m: m.text == "👤 Мой Профиль")
async def show_profile(message: types.Message):
    user_data = get_user(message.from_user.id)
    if not user_data:
        register_user(message.from_user.id, message.from_user.username)
        user_data = get_user(message.from_user.id)
        
    level, xp, bucks = user_data
    
    profile_text = (
        f"🌟 *Игровой профиль пользователя {message.from_user.first_name}* 🌟\n\n"
         f"⏳ *Возраст (Уровень):* {level} лет\n"
         f"✨ *Опыт (XP):* {xp} / {level * 50}\n"
         f"💵 *Баланс:* {bucks} баксов\n\n"
         f"🏠 *Недвижимость:* Появится с 15 уровня\n"
         f"🏢 *Бизнес:* Появится с 10 уровня"
    )
    await message.answer(profile_text, parse_mode="Markdown")

# === ЗАПУСК БОТА ===
async def main():
    init_db() # Запускаем базу данных при старте
    print("Симулятор жизни успешно запущен в Amvera!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

