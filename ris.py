import asyncio
import logging
import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder

# Настройки
BOT_TOKEN = "8962500881:AAFDttMSkEzQcSGUjljScWX6VpSbew67g58"
ADMIN_ID = 810004621  # Ваш Telegram ID из первого скриншота

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# === БАЗА ДАННЫХ ===
def init_db():
    conn = sqlite3.connect("lifecycle.db")
    cursor = conn.cursor()
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

# Функции изменения баланса для админа
def update_user_value(user_id, column, amount, mode="give"):
    conn = sqlite3.connect("lifecycle.db")
    cursor = conn.cursor()
    if mode == "give":
        cursor.execute(f"UPDATE users SET {column} = {column} + ? WHERE user_id = ?", (amount, user_id))
    elif mode == "take":
        cursor.execute(f"UPDATE users SET {column} = MAX(0, {column} - ?) WHERE user_id = ?", (amount, user_id))
    conn.commit()
    conn.close()

# === КЛАВИАТУРА ===
def get_main_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.row(types.KeyboardButton(text="👤 Мой Профиль"))
    builder.row(types.KeyboardButton(text="💼 Работа / Игры"), types.KeyboardButton(text="🛒 Магазин"))
    builder.row(types.KeyboardButton(text="🎟️ Brawl Pass"))
    return builder.as_markup(resize_keyboard=True, input_field_placeholder="Выберите действие...")

# === ОБРАБОТЧИКИ ===
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    register_user(message.from_user.id, message.from_user.username)
    welcome_text = (
        f"👋 *Приветствуем тебя в симуляторе жизни, {message.from_user.first_name}!* \n\n"
        "🌍 Здесь тебе предстоит пройти путь от обычного работяги до владельца корпораций.\n"
        "📈 Зарабатывай *Баксы*, копи *XP*, открывай бизнесы и дома!\n\n"
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

# === СЕКРЕТНЫЕ АДМИН-КОМАНДЫ ===

# Команда: /give [тип] [количество] (Например: /give bucks 5000 или /give xp 150)
@dp.message(Command("give"))
async def admin_give(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return # Обычные игроки просто проигнорируются ботом

    try:
        # Разбираем параметры команды
        args = message.text.split()
        column = args[1]  # bucks или xp или level
        amount = int(args[2]) # сколько дать
        
        if column not in ["bucks", "xp", "level"]:
            await message.answer("❌ Ошибка! Можно выдавать только: `bucks`, `xp`, `level`", parse_mode="Markdown")
            return
            
        update_user_value(message.from_user.id, column, amount, mode="give")
        await message.answer(f"✅ Успешно выдано *{amount}* для параметра *{column}*!", parse_mode="Markdown")
    except Exception:
        await message.answer("❌ Неверный формат! Пишите так:\n`/give bucks 1000`\n`/give xp 50`\n`/give level 5`", parse_mode="Markdown")

# Команда: /take [тип] [количество] (Например: /take bucks 200)
@dp.message(Command("take"))
async def admin_take(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    try:
        args = message.text.split()
        column = args[1]
        amount = int(args[2])
        
        if column not in ["bucks", "xp", "level"]:
            await message.answer("❌ Ошибка! Забирать можно только: `bucks`, `xp`, `level`", parse_mode="Markdown")
            return
            
        update_user_value(message.from_user.id, column, amount, mode="take")
        await message.answer(f"📉 Успешно забрано *{amount}* из параметра *{column}*!", parse_mode="Markdown")
    except Exception:
        await message.answer("❌ Неверный формат! Пишите так:\n`/take bucks 500`", parse_mode="Markdown")

# === ЗАПУСК ===
async def main():
    init_db()
    print("Симулятор жизни с Админ-панелью успешно запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
(
