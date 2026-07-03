import asyncio
import sqlite3
import time
import random
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

# ТОКЕН: Вставьте ваш секретный ключ от @BotFather (внутри кавычек)
TOKEN = "8233072384:AAHm8Lc62SJDlRDLqnyx0x7Ls1Ikyj3myGk"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Инициализация базы данных
def init_db():
    conn = sqlite3.connect('/data/bot_database.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            rice INTEGER DEFAULT 0,
            last_daily INTEGER DEFAULT 0,
            farms INTEGER DEFAULT 0,
            last_farm_collect INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = sqlite3.connect('/data/bot_database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT rice, last_daily, farms, last_farm_collect FROM users WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    if not row:
        now = int(time.time())
        cursor.execute('INSERT INTO users (user_id, rice, last_daily, farms, last_farm_collect) VALUES (?, 0, 0, 0, ?)', (user_id, now))
        conn.commit()
        row = (0, 0, 0, now)
    conn.close()
    return {"rice": row[0], "last": row[1], "farms": row[2], "last_collect": row[3]}

def update_user_field(user_id, field, value):
    conn = sqlite3.connect('/data/bot_database.db')
    cursor = conn.cursor()
    cursor.execute(f'UPDATE users SET {field} = ? WHERE user_id = ?', (value, user_id))
    conn.commit()
    conn.close()

# Клавиатура главного меню
menu_keyboard = types.ReplyKeyboardMarkup(
    keyboard=[
        [types.KeyboardButton(text="🌾 Награда (/daily)"), types.KeyboardButton(text="💰 Баланс (/balance)")],
        [types.KeyboardButton(text="🚜 Моя ферма (/farm)"), types.KeyboardButton(text="🎰 Казино (/casino)")],
        [types.KeyboardButton(text="ℹ️ Помощь (/help)")]
    ],
    resize_keyboard=True
)

@dp.message(Command("start"))
async def start(message: types.Message):
    get_user(message.from_user.id)
    await message.answer("🍚 Добро пожаловать в рисовую империю! Используйте меню ниже для игры.", reply_markup=menu_keyboard)

# ТА САМАЯ КОМАНДА ПОМОЩИ
@dp.message(Command("help"))
@dp.message(lambda msg: msg.text == "ℹ️ Помощь (/help)")
async def help_cmd(message: types.Message):
    text = (
        "❓ **Как играть:**\n\n"
        "🌾 `Награда` — 100 риса раз в 12 часов.\n"
        "💰 `Баланс` — ваш счет и сбор дохода.\n"
        "🚜 `Моя ферма` — покупка ферм за 500 риса. Приносят доход каждый час!\n"
        "🎰 `Казино` — сыграть на рис. Пишите: `/casino 50`\n"
        "💸 `Перевод` — отправьте команду `/pay 100` **ответом** на чужое сообщение, чтобы перевести рис другу."
    )
    await message.answer(text, parse_mode="Markdown")

@dp.message(Command("balance"))
@dp.message(lambda msg: msg.text == "💰 Баланс (/balance)")
async def balance(message: types.Message):
    user_id = message.from_user.id
    user_data = get_user(user_id)
    
    # Считаем пассивный доход
    now = int(time.time())
    hours_passed = (now - user_data["last_collect"]) // 3600
    pending_income = hours_passed * user_data["farms"] * 10
    
    inline_kb = None
    if pending_income > 0:
        inline_kb = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text=f"🧺 Собрать +{pending_income} риса", callback_data="collect_rice")]
        ])
        
    await message.answer(
        f"👤 Игрок: {message.from_user.first_name}\n"
        f"💰 Баланс: {user_data['rice']} риса\n"
        f"🚜 Количество ферм: {user_data['farms']}\n"
        f"📈 Пассивный доход: {user_data['farms'] * 10} риса/час",
        reply_markup=inline_kb
    )

@dp.callback_query(lambda c: c.data == "collect_rice")
async def collect_rice_callback(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    user_data = get_user(user_id)
    
    now = int(time.time())
    hours_passed = (now - user_data["last_collect"]) // 3600
    pending_income = hours_passed * user_data["farms"] * 10
    
    if pending_income <= 0:
        await callback_query.answer("❌ Пока нечего собирать!", show_alert=True)
        return
        
    new_rice = user_data["rice"] + pending_income
    update_user_field(user_id, "rice", new_rice)
    update_user_field(user_id, "last_farm_collect", now)
    
    await callback_query.message.edit_text(f"✅ Вы успешно собрали пассивный доход: +{pending_income} риса!")
    await callback_query.answer()

@dp.message(Command("daily"))
@dp.message(lambda msg: msg.text == "🌾 Награда (/daily)")
async def daily(message: types.Message):
    user_id = message.from_user.id
    user_data = get_user(user_id)
    
    now = int(time.time())
    cooldown = 12 * 60 * 60
    time_passed = now - user_data["last"]
    
    if time_passed < cooldown:
        time_left = cooldown - time_passed
        hours = time_left // 3600
        minutes = (time_left % 3600) // 60
        await message.answer(f"⏳ До следующей награды осталось: **{hours} ч. {minutes} мин.**", parse_mode="Markdown")
        return

    new_rice = user_data["rice"] + 100
    update_user_field(user_id, "rice", new_rice)
    update_user_field(user_id, "last_daily", now)
    await message.answer("🌾 Вы получили ежедневную награду: 100 риса!")

@dp.message(Command("farm"))
@dp.message(lambda msg: msg.text == "🚜 Моя ферма (/farm)")
async def farm(message: types.Message):
    user_id = message.from_user.id
    user_data = get_user(user_id)
    
    inline_kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🛒 Купить ферму (500 риса)", callback_data="buy_farm")]
    ])
    
    await message.answer(
        f"🚜 **Ваши рисовые плантации**\n\n"
        f"• Всего ферм: {user_data['farms']}\n"
        f"• Каждая ферма приносит 10 риса в час.\n"
        f"• Текущее производство: {user_data['farms'] * 10} риса/час.\n\n"
        f"Вы можете расширить свои владения, купив ещё одну ферму!",
        reply_markup=inline_kb,
        parse_mode="Markdown"
    )

@dp.callback_query(lambda c: c.data == "buy_farm")
async def buy_farm_callback(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    user_data = get_user(user_id)
    
    if user_data["rice"] < 500:
        await callback_query.answer("❌ У вас недостаточно риса! Нужно 500.", show_alert=True)
        return
        
    update_user_field(user_id, "rice", user_data["rice"] - 500)
    update_user_field(user_id, "farms", user_data["farms"] + 1)
    
    await callback_query.message.edit_text("🎉 Поздравляем! Вы купили ферму. Теперь пассивный доход увеличился!")
    await callback_query.answer()

@dp.message(Command("casino"))
async def casino(message: types.Message):
    user_id = message.from_user.id
    user_data = get_user(user_id)
    
    args = message.text.split()
    if len(args) < 2 or not args[1].isdigit():
        await message.answer("🎰 Чтобы сыграть, укажите ставку! Пример: `/casino 50`", parse_mode="Markdown")
        return
        
    bet = int(args[1])
    if bet <= 0:
        await message.answer("❌ Ставка должна быть больше нуля!")
        return
    if user_data["rice"] < bet:
        await message.answer("❌ У вас нет столько риса для ставки!")
        return
        
    if random.choice([True, False]):
        new_rice = user_data["rice"] + bet
        update_user_field(user_id, "rice", new_rice)
        await message.answer(f"🎉 Удача на вашей стороне! Вы выиграли {bet} риса! Теперь у вас {new_rice}.")
    else:
        new_rice = user_data["rice"] - bet
        update_user_field(user_id, "rice", new_rice)
        await message.answer(f"😢 Ставка не сыграла. Вы потеряли {bet} риса. Осталось {new_rice}.")

@dp.message(Command("pay"))
async def pay_rice(message: types.Message):
    sender_id = message.from_user.id
    sender_data = get_user(sender_id)
    
    if not message.reply_to_message:
        await message.answer("❌ Эта команда должна быть ответом на сообщение того, кому вы переводите рис!")
        return
        
    recipient_id = message.reply_to_message.from_user.id
    if sender_id == recipient_id:
        await message.answer("❌ Нельзя переводить рис самому себе!")
        return
        
    args = message.text.split()
    if len(args) < 2 or not args[1].isdigit():
        await message.answer("❌ Укажите сумму перевода. Пример: `/pay 100`", parse_mode="Markdown")
        return
        
    amount = int(args[1])
    if amount <= 0:
        await message.answer("❌ Сумма перевода должна быть больше нуля!")
        return
    if sender_data["rice"] < amount:
        await message.answer("❌ У вас недостаточно риса для перевода!")
        return
        
    recipient_data = get_user(recipient_id)
    
    update_user_field(sender_id, "rice", sender_data["rice"] - amount)
    update_user_field(recipient_id, "rice", recipient_data["rice"] + amount)
    
    await message.answer(f"💸 Вы успешно перевели {amount} риса пользователю {message.reply_to_message.from_user.first_name}!")

async def main():
    init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
