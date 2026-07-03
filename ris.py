import asyncio
import time
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

# ТОКЕН: Убедитесь, что внутри кавычек вставлен ваш реальный токен из Telegram!
TOKEN = "8233072384:AAHm8Lc62SJDlRDLqnyx0x7Ls1Ikyj3myGk"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Временный словарь для хранения баланса пользователей в памяти
users = {}

@dp.message(Command("start"))
async def start(message: types.Message):
    users.setdefault(message.from_user.id, {"rice": 0, "last": 0})
    await message.answer("Бот риса запущен 🍚")

@dp.message(Command("balance"))
async def balance(message: types.Message):
    user_data = users.get(message.from_user.id, {"rice": 0, "last": 0})
    await message.answer(f"Баланс: {user_data['rice']} риса")

@dp.message(Command("daily"))
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
