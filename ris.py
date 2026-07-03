import asyncio
import time
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# ТОКЕН: Сюда вставьте ваш секретный ключ от @BotFather (внутри кавычек)
TOKEN = "8233072384:AAHm8Lc62SJDlRDLqnyx0x7Ls1Ikyj3myGk"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Временный словарь для хранения баланса пользователей в памяти
users = {}

# Создаем меню из двух красивых кнопок на экране телефона
menu_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🌾 Получить рис (/daily)")],
        [KeyboardButton(text="💰 Баланс (/balance)")]
    ],
    resize_keyboard=True # Делает кнопки маленькими и аккуратными под размер экрана
)

@dp.message(Command("start"))
async def start(message: types.Message):
    users.setdefault(message.from_user.id, {"rice": 0, "last": 0})
    # Отправляем сообщение вместе с меню-клавиатурой
    await message.answer("Бот риса запущен 🍚\nИспользуйте меню ниже для игры:", reply_markup=menu_keyboard)

# Бот поймет команду, если пользователь нажмет на кнопку баланса или напишет /balance
@dp.message(lambda msg: msg.text in ["💰 Баланс (/balance)", "/balance"])
async def balance(message: types.Message):
    user_data = users.get(message.from_user.id, {"rice": 0, "last": 0})
    await message.answer(f"Баланс: {user_data['rice']} риса")

# Бот поймет команду, если пользователь нажмет на кнопку риса или напишет /daily
@dp.message(lambda msg: msg.text in ["🌾 Получить рис (/daily)", "/daily"])
async def daily(message: types.Message):
    user_data = users.setdefault(message.from_user.id, {"rice": 0, "last": 0})
    
    now = time.time()
    # Проверка: прошло ли 12 часов
    if now - user_data["last"] < 12 * 60 * 60:
        await message.answer("⏳ Подожди 12 часов")
        return

    user_data["rice"] += 100
    user_data["last"] = now
    await message.answer("🌾 Вы получили ежедневную награду: 100 риса!")

# ГЛАВНЫЙ БЛОК ЗАПУСКА БОТА
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
