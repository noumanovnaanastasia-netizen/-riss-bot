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

# =========================
# ТОКЕН БОТА
# =========================
TOKEN = "СЮДА_ВСТАВЬ_ТОКЕН"

# Логирование
logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

DB_NAME = "rice_empire.db"

# =========================
# FSM СОСТОЯНИЯ
# =========================
class RegistrationStates(StatesGroup):
    waiting_for_nickname = State()

# =========================
# БАЗА ДАННЫХ
# =========================
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            nickname TEXT,
            rice INTEGER DEFAULT 100,
            xp INTEGER DEFAULT 0,
            level INTEGER DEFAULT 1,
            vip_until INTEGER DEFAULT 0,
            current_title TEXT DEFAULT '🚫 Отсутствует',
            last_bonus INTEGER DEFAULT 0,
            last_work INTEGER DEFAULT 0,
            last_rob INTEGER DEFAULT 0,
            energy_until INTEGER DEFAULT 0,
            wins INTEGER DEFAULT 0,
            losses INTEGER DEFAULT 0
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS businesses (
            user_id INTEGER PRIMARY KEY,
            b1 INTEGER DEFAULT 0,
            b2 INTEGER DEFAULT 0,
            b3 INTEGER DEFAULT 0,
            b4 INTEGER DEFAULT 0,
            b5 INTEGER DEFAULT 0,
            b6 INTEGER DEFAULT 0,
            b7 INTEGER DEFAULT 0,
            last_passive_collect INTEGER DEFAULT 0
        )
    """)

    cursor.execute("""
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

# =========================
# ПОЛУЧЕНИЕ ДАННЫХ ПОЛЬЗОВАТЕЛЯ
# =========================
def get_user_data(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()

    if not user:
        conn.close()
        return None

    cursor.execute("SELECT * FROM businesses WHERE user_id = ?", (user_id,))
    biz = cursor.fetchone()

    cursor.execute("SELECT * FROM inventory WHERE user_id = ?", (user_id,))
    inv = cursor.fetchone()

    conn.close()

    return {
        "user_id": user[0],
        "nickname": user[1],
        "rice": user[2],
        "xp": user[3],
        "level": user[4],
        "vip_until": user[5],
        "current_title": user[6],
        "last_bonus": user[7],
        "last_work": user[8],
        "last_rob": user[9],
        "energy_until": user[10],
        "wins": user[11],
        "losses": user[12],

        "b1": biz[1],
        "b2": biz[2],
        "b3": biz[3],
        "b4": biz[4],
        "b5": biz[5],
        "b6": biz[6],
        "b7": biz[7],
        "last_passive_collect": biz[8],

        "energy_drink": inv[1],
        "amulet": inv[2],
        "box1": inv[3],
        "box2": inv[4],
        "box3": inv[5],
    }

# =========================
# РЕГИСТРАЦИЯ ПОЛЬЗОВАТЕЛЯ (ИСПРАВЛЕНО)
# =========================
def register_user(user_id, nickname):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    now = int(time.time())

    cursor.execute("""
        INSERT OR REPLACE INTO users
        (user_id, nickname, last_bonus, last_work, last_rob)
        VALUES (?, ?, 0, 0, 0)
    """, (user_id, nickname))

    cursor.execute("""
        INSERT OR REPLACE INTO businesses (user_id, last_passive_collect)
        VALUES (?, ?)
    """, (user_id, now))

    cursor.execute("""
        INSERT OR REPLACE INTO inventory (user_id)
        VALUES (?)
    """, (user_id,))

    conn.commit()
    conn.close()

# =========================
# ОБНОВЛЕНИЕ ПОЛЯ
# =========================
def update_field(user_id, table, field, value):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(f"""
        UPDATE {table}
        SET {field} = ?
        WHERE user_id = ?
    """, (value, user_id))

    conn.commit()
    conn.close()
    
    # =========================
# ПРЕДПРИЯТИЯ (БИЗНЕСЫ)
# =========================

BUSINESS_CONFIG = {
    "b1": {"name": "🌱 Рисовая грядка", "price": 500, "income": 5},
    "b2": {"name": "🧺 Небольшая теплица", "price": 2500, "income": 30},
    "b3": {"name": "🚜 Автоматическая плантация", "price": 10000, "income": 130},
    "b4": {"name": "🏭 Сельская фабрика", "price": 25000, "income": 350},
    "b5": {"name": "🏢 Рисовый синдикат", "price": 50000, "income": 750},
    "b6": {"name": "🚀 Международный экспорт", "price": 100000, "income": 1600},
    "b7": {"name": "🌌 Межгалактическая корпорация", "price": 250000, "income": 4500}
}

# =========================
# ТИТУЛЫ
# =========================

TITLES_CONFIG = {
    2000: "🌱 Рисовый росток",
    5000: "🌾 Помощник на поле",
    15000: "🚜 Смотритель плантации",
    20000: "🌾 Мастер урожая",
    40000: "💼 Поставщик риса",
    50000: "🏯 Хозяин полей",
    70000: "💎 Золотой колос",
    80000: "👑 Хранительница урожая",
    100000: "🌌 Императрица Галактики"
}

# =========================
# СТАТУС ПО РИСУ
# =========================

def get_auto_status(rice):
    if rice < 5000:
        return "🌾 Новичок"
    elif rice < 10000:
        return "🚜 Работяга"
    elif rice < 18000:
        return "🧺 Сборщик урожая"
    elif rice < 25000:
        return "🍙 Мастер Суши"
    elif rice < 35000:
        return "🏪 Владелец Лавки"
    elif rice < 50000:
        return "📈 Рисовый Трейдер"
    elif rice < 70000:
        return "🏯 Помещик"
    elif rice < 100000:
        return "💎 Олигарх Плантаций"
    else:
        return "👑 Рисовый Бог"

# =========================
# ОПЫТ И УРОВНИ
# =========================

def get_required_xp(level):
    if level <= 5:
        return 25
    elif level <= 15:
        return 100
    elif level <= 20:
        return 150
    else:
        return 200

# =========================
# ДОБАВЛЕНИЕ XP
# =========================

def add_xp(user_id, xp_to_add):
    data = get_user_data(user_id)
    if not data or data["level"] >= 25:
        return ""

    now = int(time.time())

    # VIP буст
    if data["vip_until"] > now:
        xp_to_add = int(xp_to_add * 1.5)

    new_xp = data["xp"] + xp_to_add
    current_level = data["level"]
    leveled_up = False
    reward_text = ""

    while current_level < 25 and new_xp >= get_required_xp(current_level):
        new_xp -= get_required_xp(current_level)
        current_level += 1
        leveled_up = True

        # награды
        if current_level == 15:
            reward_text += "🎁 VIP НА 2 ДНЯ!\n"
            vip_time = max(data["vip_until"], now) + (2 * 24 * 3600)
            update_field(user_id, "users", "vip_until", vip_time)

        else:
            if current_level <= 5:
                r_rice = random.randint(200, 1000)
                r_xp = random.randint(1, 20)
            elif current_level <= 15:
                r_rice = random.randint(500, 3000)
                r_xp = random.randint(20, 30)
            elif current_level <= 20:
                r_rice = random.randint(1000, 4000)
                r_xp = random.randint(25, 40)
            else:
                r_rice = random.randint(200, 6000)
                r_xp = random.randint(30, 50)

            reward_text += f"🎁 +{r_rice} 🍙 и +{r_xp} XP\n"

            user_data = get_user_data(user_id)
            update_field(
                user_id,
                "users",
                "rice",
                user_data["rice"] + r_rice
            )

            new_xp += r_xp

    update_field(user_id, "users", "xp", new_xp)
    update_field(user_id, "users", "level", current_level)

    if leveled_up:
        return f"🎉 LEVEL UP! Ты достиг {current_level} уровня!\n{reward_text}"

    return f"✨ +{xp_to_add} XP"
    
    # =========================
# ПАССИВНЫЙ ДОХОД
# =========================

def calc_passive_income(data):
    now = int(time.time())
    seconds_passed = now - data["last_passive_collect"]
    hours_passed = seconds_passed / 3600.0

    if hours_passed <= 0:
        return 0

    total_income_per_hour = 0

    for key, config in BUSINESS_CONFIG.items():
        total_income_per_hour += data[key] * config["income"]

    # VIP буст дохода
    if data["energy_until"] > now:
        total_income_per_hour = int(total_income_per_hour * 1.5)

    return int(hours_passed * total_income_per_hour)

# =========================
# ИНЛАЙН КЛАВИАТУРЫ
# =========================

def main_keyboard():
    return types.InlineKeyboardMarkup(inline_keyboard=[
        [
            types.InlineKeyboardButton(text="👤 Профиль", callback_data="menu_profile"),
            types.InlineKeyboardButton(text="🏪 Магазин", callback_data="menu_shop")
        ],
        [
            types.InlineKeyboardButton(text="🌾 Бонус", callback_data="menu_bonus"),
            types.InlineKeyboardButton(text="🎒 Инвентарь", callback_data="menu_inventory")
        ],
        [
            types.InlineKeyboardButton(text="🎮 Игры", callback_data="menu_games")
        ]
    ])

def shop_categories_keyboard():
    return types.InlineKeyboardMarkup(inline_keyboard=[
        [
            types.InlineKeyboardButton(text="🚜 Бизнес", callback_data="shop_biz"),
            types.InlineKeyboardButton(text="👑 VIP", callback_data="shop_vip")
        ],
        [
            types.InlineKeyboardButton(text="🎫 XP", callback_data="shop_xp"),
            types.InlineKeyboardButton(text="🥤 Бусты", callback_data="shop_items")
        ],
        [
            types.InlineKeyboardButton(text="📦 Кейсы", callback_data="shop_boxes"),
            types.InlineKeyboardButton(text="🏅 Титулы", callback_data="shop_titles")
        ],
        [
            types.InlineKeyboardButton(text="🔙 Меню", callback_data="to_main")
        ]
    ])
    
    # =========================
# /START И РЕГИСТРАЦИЯ
# =========================

@dp.message(CommandStart())
async def start_cmd(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    data = get_user_data(user_id)

    if not data:
        register_user(user_id, message.from_user.first_name)

        await message.answer(
            "👋 Добро пожаловать в Rice Empire!\n\n"
            "Введите свой никнейм для регистрации:"
        )

        await state.set_state(RegistrationStates.waiting_for_nickname)
        return

    await message.answer(
        f"👋 С возвращением, {data['nickname']}!\n"
        f"🍙 Рис: {data['rice']}\n"
        f"⭐ Уровень: {data['level']}\n\n"
        "Выбери действие:",
        reply_markup=main_keyboard()
    )

# =========================
# РЕГИСТРАЦИЯ НИКНЕЙМА
# =========================

@dp.message(RegistrationStates.waiting_for_nickname)
async def set_nickname(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    nickname = message.text.strip()

    if len(nickname) < 2:
        await message.answer("❌ Ник слишком короткий, попробуй ещё раз.")
        return

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET nickname = ? WHERE user_id = ?",
        (nickname, user_id)
    )
    conn.commit()
    conn.close()

    await state.clear()

    await message.answer(
        f"✅ Ник установлен: {nickname}\n\n"
        "Добро пожаловать в игру!",
        reply_markup=main_keyboard()
    )

# =========================
# ФУНКЦИЯ ПРОВЕРКИ ПОЛЬЗОВАТЕЛЯ
# =========================

def ensure_user(user_id, first_name):
    data = get_user_data(user_id)
    if not data:
        register_user(user_id, first_name)
        return False
    return True
    
    # =========================
# МАГАЗИН: БИЗНЕС
# =========================

@dp.callback_query(F.data == "shop_biz")
async def shop_biz(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    data = get_user_data(user_id)

    text = "🚜 Бизнес-магазин:\n\n"

    for key, biz in BUSINESS_CONFIG.items():
        text += f"{biz['name']} — {biz['price']} 🍙\n"

    text += "\n(Покупка пока не добавлена полностью)"

    await callback.message.edit_text(text, reply_markup=shop_categories_keyboard())


# =========================
# VIP МАГАЗИН
# =========================

@dp.callback_query(F.data == "shop_vip")
async def shop_vip(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "👑 VIP Магазин\n\n"
        "VIP пока не реализован полностью.",
        reply_markup=shop_categories_keyboard()
    )


# =========================
# XP МАГАЗИН
# =========================

@dp.callback_query(F.data == "shop_xp")
async def shop_xp(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "🎫 Магазин XP\n\n"
        "Покупка XP пока не добавлена.",
        reply_markup=shop_categories_keyboard()
    )


# =========================
# ПРЕДМЕТЫ
# =========================

@dp.callback_query(F.data == "shop_items")
async def shop_items(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "🥤 Бусты и предметы\n\n"
        "Скоро будет доступно.",
        reply_markup=shop_categories_keyboard()
    )


# =========================
# КЕЙСЫ
# =========================

@dp.callback_query(F.data == "shop_boxes")
async def shop_boxes(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "📦 Кейсы\n\n"
        "Открытие кейсов пока не добавлено.",
        reply_markup=shop_categories_keyboard()
    )


# =========================
# ТИТУЛЫ
# =========================

@dp.callback_query(F.data == "shop_titles")
async def shop_titles(callback: types.CallbackQuery):
    text = "🏅 Титулы:\n\n"

    for price, title in TITLES_CONFIG.items():
        text += f"{title} — {price} 🍙\n"

    text += "\n(Покупка пока не добавлена)"

    await callback.message.edit_text(text, reply_markup=shop_categories_keyboard())
    
    # =========================
# ЗАВЕРШЕНИЕ РЕГИСТРАЦИИ (FSM)
# =========================

@dp.message(RegistrationStates.waiting_for_nickname)
async def set_nickname(message: types.Message, state: FSMContext):
    nickname = message.text.strip()

    if len(nickname) < 2 or len(nickname) > 20:
        await message.answer(
            "❌ Никнейм должен содержать от 2 до 20 символов! Попробуй еще раз:"
        )
        return

    register_user(message.from_user.id, nickname)
    await state.clear()

    await message.answer(
        f"🎉 Отлично! Твой игровой профиль успешно создан.\n"
        f"Твой никнейм: {nickname}\n"
        f"Тебе начислено стартовые 100 🍙!\n\n"
        "_Начнем строить империю!_ 👇",
        parse_mode="Markdown",
        reply_markup=main_keyboard()
    )


# =========================
# МЕНЮ КОМАНДА
# =========================

@dp.message(Command("menu"))
async def cmd_menu(message: types.Message):
    data = get_user_data(message.from_user.id)
    if not data:
        return

    await message.answer(
        "🗂 Главное управление рисовой базой:",
        parse_mode="Markdown",
        reply_markup=main_keyboard()
    )


# =========================
# ВОЗВРАТ В ГЛАВНОЕ МЕНЮ
# =========================

@dp.callback_query(F.data == "to_main")
async def back_to_main_callback(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "🗂 Главное управление рисовой базой:",
        parse_mode="Markdown",
        reply_markup=main_keyboard()
    )
    await callback.answer()


# =========================
# ПРОФИЛЬ
# =========================

@dp.callback_query(F.data == "menu_profile")
async def profile_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    data = get_user_data(user_id)
    if not data:
        return

    # пассивный доход
    passive = calc_passive_income(data)
    if passive > 0:
        update_field(user_id, "users", "rice", data["rice"] + passive)
        update_field(user_id, "businesses", "last_passive_collect", int(time.time()))
        data = get_user_data(user_id)

    now = int(time.time())

    vip_status = "❌ Не активен"
    if data["vip_until"] > now:
        rem = data["vip_until"] - now
        vip_status = f"👑 Активен (осталось {rem // 3600} ч.)"

    energy_status = ""
    if data["energy_until"] > now:
        energy_status = " ⚡ (Действует Энергетик x1.5)"

    auto_status = get_auto_status(data["rice"])
    req_xp = get_required_xp(data["level"])

    profile_text = (
        f"👤 ИГРОВОЙ ПРОФИЛЬ ИМПЕРИИ\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🆔 Твой ID: {data['user_id']}\n"
        f"👤 Никнейм: {data['nickname']}\n"
        f"🏅 Купленный Титул: {data['current_title']}\n"
        f"📊 Ранг за богатство: {auto_status}\n"
        f"👑 VIP-Статус: {vip_status}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🍙 Баланс риса: {data['rice']} 🍙{energy_status}\n"
        f"🎟 Brawl Pass: {data['level']}/25 Уровень ({data['xp']}/{req_xp} XP)\n"
        f"⚔️ Статистика дуэлей: 🏆 Побед: {data['wins']} | 💀 Проиграно: {data['losses']}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🌾 Пассивный доход зачислен автоматически при открытии профиля!"
    )

    kb = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="🔙 Назад", callback_data="to_main")]
        ]
    )

    await callback.message.edit_text(
        profile_text,
        parse_mode="Markdown",
        reply_markup=kb
    )
    await callback.answer()


# =========================
# БОНУС
# =========================

@dp.callback_query(F.data == "menu_bonus")
async def bonus_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    data = get_user_data(user_id)
    if not data:
        return

    now = int(time.time())
    cooldown = 6 * 3600

    if now - data["last_bonus"] < cooldown:
        time_left = cooldown - (now - data["last_bonus"])
        hours = time_left // 3600
        minutes = (time_left % 3600) // 60

        await callback.message.edit_text(
            f"⏳ Сбор плантации закрыт!\n\n"
            f"До следующего сбора: {hours} ч. {minutes} мин. 🍙",
            reply_markup=types.InlineKeyboardMarkup(
                inline_keyboard=[
                    [types.InlineKeyboardButton(text="🔙 Назад", callback_data="to_main")]
                ]
            )
        )
        await callback.answer()
        return

    is_vip = data["vip_until"] > now

    if is_vip:
        give_rice = 3500
        give_xp = random.randint(20, 40)
        vip_tag = "👑 VIP Бонус"
    else:
        give_rice = 2000
        give_xp = random.randint(5, 25)
        vip_tag = "🌾 Обычный Бонус"

    update_field(user_id, "users", "rice", data["rice"] + give_rice)
    update_field(user_id, "users", "last_bonus", now)

    xp_msg = add_xp(user_id, give_xp)

    success_text = (
        f"{vip_tag} успешно собран!\n\n"
        f"🌾 Ты собрал:\n"
        f"💰 +{give_rice} 🍙\n"
        f"{xp_msg}"
    )

    await callback.message.edit_text(
        success_text,
        parse_mode="Markdown",
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[
                [types.InlineKeyboardButton(text="🔙 Назад", callback_data="to_main")]
            ]
        )
    )
    await callback.answer()


# =========================
# ИНВЕНТАРЬ (НАЧАЛО)
# =========================

@dp.callback_query(F.data == "menu_inventory")
async def inventory_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    data = get_user_data(user_id)
    if not data:
        return

    inv_text = (
        "🎒 ИНВЕНТАРЬ\n\n"
        f"🥤 Энергетики: {data['energy_drink']}\n"
        f"🧿 Амулеты: {data['amulet']}\n"
        f"📦 Кейсы:\n"
        f" - Малый: {data['box1']}\n"
        f" - Средний: {data['box2']}\n"
        f" - Большой: {data['box3']}"
    )

    await callback.message.edit_text(
        inv_text,
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[
                [types.InlineKeyboardButton(text="🔙 Назад", callback_data="to_main")]
            ]
        )
    )
    await callback.answer()
    
    # =========================
# ИНВЕНТАРЬ
# =========================

@dp.callback_query(F.data == "menu_inventory")
async def inventory_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    data = get_user_data(user_id)
    if not data:
        return

    inv_text = (
        f"🎒 ТВОЙ КАРМАННЫЙ ИНВЕНТАРЬ\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🥤 Рисовый энергетик (x1.5): {data['energy_drink']} шт.\n"
        f"🛡 Амулет от наглых воров: {data['amulet']} шт.\n\n"
        f"📦 Хранилище нераспечатанных сундуков:\n"
        f"├ 📦 Рисовая коробка: {data['box1']} шт.\n"
        f"├ 💎 Ларец Сенсея: {data['box2']} шт.\n"
        f"└ 🌌 Императорский сундук: {data['box3']} шт.\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"⚡ Выбери вещь в меню ниже для активации:"
    )

    buttons = []

    if data["energy_drink"] > 0:
        buttons.append([types.InlineKeyboardButton(
            text="🥤 Выпить Энергетик",
            callback_data="use_energy"
        )])

    if data["box1"] > 0:
        buttons.append([types.InlineKeyboardButton(
            text="📦 Открыть Рисовую коробку",
            callback_data="open_box1"
        )])

    if data["box2"] > 0:
        buttons.append([types.InlineKeyboardButton(
            text="💎 Открыть Ларец Сенсея",
            callback_data="open_box2"
        )])

    if data["box3"] > 0:
        buttons.append([types.InlineKeyboardButton(
            text="🌌 Открыть Императорский сундук",
            callback_data="open_box3"
        )])

    buttons.append([types.InlineKeyboardButton(
        text="🔙 Назад",
        callback_data="to_main"
    )])

    await callback.message.edit_text(
        inv_text,
        parse_mode="Markdown",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=buttons)
    )

    await callback.answer()


# =========================
# ЭНЕРГЕТИК
# =========================

@dp.callback_query(F.data == "use_energy")
async def use_energy_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    data = get_user_data(user_id)
    if not data or data["energy_drink"] <= 0:
        return

    now = int(time.time())
    new_energy_time = max(data["energy_until"], now) + 3600

    update_field(user_id, "inventory", "energy_drink", data["energy_drink"] - 1)
    update_field(user_id, "users", "energy_until", new_energy_time)

    await callback.message.edit_text(
        "🥤 Глоток энергии!\n\n"
        "Ты выпил энергетик. Теперь доход x1.5 на 1 час.",
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[
                [types.InlineKeyboardButton(text="🔙 В инвентарь", callback_data="menu_inventory")]
            ]
        )
    )

    await callback.answer()


# =========================
# ОТКРЫТИЕ КЕЙСОВ
# =========================

@dp.callback_query(F.data.startswith("open_box"))
async def open_box_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    data = get_user_data(user_id)
    if not data:
        return

    box_type = callback.data.split("box")[-1]

    msg = ""

    # ================= BOX 1 =================
    if box_type == "1" and data["box1"] > 0:
        update_field(user_id, "inventory", "box1", data["box1"] - 1)

        res = random.choice(["rice", "xp", "drink"])

        if res == "rice":
            val = random.randint(500, 2000)
            update_field(user_id, "users", "rice", data["rice"] + val)
            msg = f"💰 +{val} 🍙"

        elif res == "xp":
            val = random.randint(15, 40)
            msg = add_xp(user_id, val)

        else:
            update_field(user_id, "inventory", "energy_drink", data["energy_drink"] + 1)
            msg = "🥤 +1 энергетик"

    # ================= BOX 2 =================
    elif box_type == "2" and data["box2"] > 0:
        update_field(user_id, "inventory", "box2", data["box2"] - 1)

        res = random.choice(["rice", "xp", "vip"])

        if res == "rice":
            val = random.randint(2500, 8000)
            update_field(user_id, "users", "rice", data["rice"] + val)
            msg = f"💰 +{val} 🍙"

        elif res == "xp":
            val = random.randint(50, 120)
            msg = add_xp(user_id, val)

        else:
            vip_time = max(data["vip_until"], int(time.time())) + (3 * 24 * 3600)
            update_field(user_id, "users", "vip_until", vip_time)
            msg = "👑 VIP +3 дня"

    # ================= BOX 3 =================
    elif box_type == "3" and data["box3"] > 0:
        update_field(user_id, "inventory", "box3", data["box3"] - 1)

        r_rice = random.randint(7000, 30000)
        r_xp = random.randint(150, 400)

        update_field(user_id, "users", "rice", data["rice"] + r_rice)
        xp_msg = add_xp(user_id, r_xp)

        item = random.choice(["drink", "amulet", "vip10"])

        if item == "drink":
            update_field(user_id, "inventory", "energy_drink", data["energy_drink"] + 3)
            item_text = "🥤 +3 энергетика"

        elif item == "amulet":
            update_field(user_id, "inventory", "amulet", data["amulet"] + 1)
            item_text = "🛡 +1 амулет"

        else:
            vip_time = max(data["vip_until"], int(time.time())) + (10 * 24 * 3600)
            update_field(user_id, "users", "vip_until", vip_time)
            item_text = "👑 VIP +10 дней"

        msg = f"🎁 {r_rice} 🍙 + XP + предмет:\n{xp_msg}\n{item_text}"

    else:
        msg = "❌ У тебя нет этого кейса"

    await callback.message.edit_text(
        f"📦 Результат:\n\n{msg}",
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[
                [types.InlineKeyboardButton(text="🔙 В инвентарь", callback_data="menu_inventory")]
            ]
        )
    )

    await callback.answer()
    
    # =========================
# ИМПЕРАТОРСКИЙ КЕЙС (ЗАВЕРШЕНИЕ)
# =========================

# (этот кусок — продолжение open_box_callback, поэтому он должен быть внутри него)

# VIP награда
vip_time = max(data["vip_until"], now) + (10 * 24 * 3600)
update_field(user_id, "users", "vip_until", vip_time)

item_text = "👑 VIP-СТАТУС НА 10 ДНЕЙ!"

msg = (
    f"🌌 Двойной Дроп из Императорского сундука!\n\n"
    f"🎁 Приз №1 (Ресурсы): +{r_rice} 🍙 и {xp_msg}\n"
    f"🎁 Приз №2 (Вещь): {item_text}"
)

# если сундук пуст
# (ЭТО ДОЛЖНО БЫТЬ ВНУТРИ IF/ELSE В ТВОЁМ ФАЙЛЕ)
# else:
#     await callback.answer("Сундук закончился!")
#     return


# =========================
# МАГАЗИН ГЛАВНОЕ МЕНЮ
# =========================

@dp.callback_query(F.data == "menu_shop")
async def shop_callback(callback: types.CallbackQuery):
    data = get_user_data(callback.from_user.id)

    await callback.message.edit_text(
        f"🏪 ТОРГОВЫЙ ЦЕНТР ИМПЕРИИ 🍙\n\n"
        f"💰 Баланс: {data['rice']} 🍙\n\n"
        f"_Выбери категорию товаров:_",
        parse_mode="Markdown",
        reply_markup=shop_categories_keyboard()
    )

    await callback.answer()


# =========================
# МАГАЗИН БИЗНЕСА
# =========================

@dp.callback_query(F.data == "shop_biz")
async def shop_biz_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    data = get_user_data(user_id)

    text = "🚜 МАГАЗИН БИЗНЕСА (доход в час)\n\n"
    buttons = []

    for key, cfg in BUSINESS_CONFIG.items():
        text += (
            f"▪️ {cfg['name']}\n"
            f"💰 Цена: {cfg['price']} 🍙\n"
            f"📈 Доход: +{cfg['income']} 🍙/ч\n"
            f"📦 У тебя: {data[key]}
            
            # =========================
# МАГАЗИН XP
# =========================

@dp.callback_query(F.data == "shop_xp")
async def shop_xp_callback(callback: types.CallbackQuery):
    data = get_user_data(callback.from_user.id)

    text = (
        f"🎫 МАГАЗИН XP ПАКОВ\n\n"
        f"💰 Баланс: {data['rice']} 🍙\n\n"
        f"🍬 Конфета XP (+25 XP) — 600 🍙\n"
        f"🔋 Малый пак (+75 XP) — 1 800 🍙\n"
        f"📦 Средний пак (+150 XP) — 3 500 🍙\n"
        f"🚀 Большой пак (+300 XP) — 6 500 🍙\n"
        f"🎫 Скип уровня — 9 000 🍙"
    )

    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [
            types.InlineKeyboardButton(text="🍬 600", callback_data="buy_xp_1"),
            types.InlineKeyboardButton(text="🔋 1800", callback_data="buy_xp_2")
        ],
        [
            types.InlineKeyboardButton(text="📦 3500", callback_data="buy_xp_3"),
            types.InlineKeyboardButton(text="🚀 6500", callback_data="buy_xp_4")
        ],
        [
            types.InlineKeyboardButton(text="🎫 Скип уровня", callback_data="buy_xp_5")
        ],
        [
            types.InlineKeyboardButton(text="🔙 Назад", callback_data="menu_shop")
        ]
    ])

    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


# =========================
# ПОКУПКА XP
# =========================

@dp.callback_query(F.data.startswith("buy_xp_"))
async def buy_xp_process(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    pack_type = callback.data.split("buy_xp_")[-1]

    data = get_user_data(user_id)

    config = {
        "1": {"price": 600, "xp": 25, "skip": False},
        "2": {"price": 1800, "xp": 75, "skip": False},
        "3": {"price": 3500, "xp": 150, "skip": False},
        "4": {"price": 6500, "xp": 300, "skip": False},
        "5": {"price": 9000, "xp": 0, "skip": True}
    }

    cfg = config[pack_type]

    if data["rice"] < cfg["price"]:
        await callback.answer("❌ Недостаточно 🍙!", show_alert=True)
        return

    update_field(user_id, "users", "rice", data["rice"] - cfg["price"])

    if cfg["skip"]:
        if data["level"] < 25:
            update_field(user_id, "users", "level", data["level"] + 1)
            update_field(user_id, "users", "xp", 0)
            await callback.answer("🎉 Уровень повышен!", show_alert=True)
        else:
            await callback.answer("❌ Макс уровень!", show_alert=True)
    else:
        xp_msg = add_xp(user_id, cfg["xp"])
        await callback.answer(f"🎉 XP добавлен! {xp_msg}", show_alert=True)

    await shop_xp_callback(callback)


# =========================
# МАГАЗИН ПРЕДМЕТОВ
# =========================

@dp.callback_query(F.data == "shop_items")
async def shop_items_callback(callback: types.CallbackQuery):
    data = get_user_data(callback.from_user.id)

    text = (
        f"🥤 МАГАЗИН БУСТЕРОВ\n\n"
        f"💰 Баланс: {data['rice']} 🍙\n\n"
        f"🥤 Энергетик — 1000 🍙\n"
        f"⚡ x1.5 доход на 1 час\n\n"
        f"🛡 Амулет — 2000 🍙\n"
        f"🛡 защита от краж"
    )

    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🥤 1000", callback_data="buy_item_drink")],
        [types.InlineKeyboardButton(text="🛡 2000", callback_data="buy_item_amulet")],
        [types.InlineKeyboardButton(text="🔙 Назад", callback_data="menu_shop")]
    ])

    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


# =========================
# ПОКУПКА ПРЕДМЕТОВ
# =========================

@dp.callback_query(F.data.startswith("buy_item_"))
async def buy_item_process(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    item = callback.data.split("buy_item_")[-1]

    data = get_user_data(user_id)

    prices = {
        "drink": 1000,
        "amulet": 2000
    }

    if data["rice"] < prices[item]:
        await callback.answer("❌ Недостаточно 🍙!", show_alert=True)
        return

    update_field(user_id, "users", "rice", data["rice"] - prices[item])

    if item == "drink":
        update_field(user_id, "inventory", "energy_drink", data["energy_drink"] + 1)
        await callback.answer("🥤 Куплен энергетик!", show_alert=True)

    elif item == "amulet":
        update_field(user_id, "inventory", "amulet", data["amulet"] + 1)
        await callback.answer("🛡 Куплен амулет!", show_alert=True)

    await shop_items_callback(callback)


# =========================
# МАГАЗИН КЕЙСОВ (НАЧАЛО)
# =========================

@dp.callback_query(F.data == "shop_boxes")
async def shop_boxes_callback(callback: types.CallbackQuery):
    data = get_user_data(callback.from_user.id)

    text = (
        f"📦 МАГАЗИН КЕЙСОВ\n\n"
        f"💰 Баланс: {data['rice']} 🍙\n\n"
        f"📦 Рисовый кейс — 1500 🍙\n"
        f"💎 Ларец Сенсея — 5000 🍙\n"
        f"🌌 Императорский сундук — 15000 🍙"
    )

    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="📦 1500", callback_data="buy_box1")],
        [types.InlineKeyboardButton(text="💎 5000", callback_data="buy_box2")],
        [types.InlineKeyboardButton(text="🌌 15000", callback_data="buy_box3")],
        [types.InlineKeyboardButton(text="🔙 Назад", callback_data="menu_shop")]
    ])

    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()
    
    # =========================
# МАГАЗИН КЕЙСОВ
# =========================

@dp.callback_query(F.data == "shop_boxes")
async def shop_boxes_callback(callback: types.CallbackQuery):
    data = get_user_data(callback.from_user.id)

    text = (
        f"📦 СУНДУКИ С СЮРПРИЗОМ\n\n"
        f"💰 Баланс: {data['rice']} 🍙\n\n"
        f"📦 Рисовая коробка — 1 500 🍙\n"
        f"💎 Ларец Сенсея — 5 000 🍙\n"
        f"🌌 Императорский сундук — 15 000 🍙 (x2 дроп!)"
    )

    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="📦 1500", callback_data="buy_box_1")],
        [types.InlineKeyboardButton(text="💎 5000", callback_data="buy_box_2")],
        [types.InlineKeyboardButton(text="🌌 15000", callback_data="buy_box_3")],
        [types.InlineKeyboardButton(text="🔙 Назад", callback_data="menu_shop")]
    ])

    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


# =========================
# ПОКУПКА КЕЙСОВ
# =========================

@dp.callback_query(F.data.startswith("buy_box_"))
async def buy_box_process(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    box_num = callback.data.split("buy_box_")[-1]

    data = get_user_data(user_id)

    prices = {
        "1": 1500,
        "2": 5000,
        "3": 15000
    }

    if data["rice"] < prices[box_num]:
        await callback.answer("❌ Недостаточно 🍙!", show_alert=True)
        return

    update_field(user_id, "users", "rice", data["rice"] - prices[box_num])

    db_fields = {
        "1": "box1",
        "2": "box2",
        "3": "box3"
    }

    field = db_fields[box_num]

    update_field(user_id, "inventory", field, data[field] + 1)

    await callback.answer("🎉 Сундук куплен!", show_alert=True)

    await shop_boxes_callback(callback)


# =========================
# МАГАЗИН ТИТУЛОВ
# =========================

@dp.callback_query(F.data == "shop_titles")
async def shop_titles_callback(callback: types.CallbackQuery):
    data = get_user_data(callback.from_user.id)

    text = f"🏅 ТИТУЛЫ\n\n💰 Баланс: {data['rice']} 🍙\n\n"

    buttons = []

    for price, title_name in TITLES_CONFIG.items():
        text += f"▪️ {title_name} — {price} 🍙\n"

        if data["current_title"] != title_name:
            buttons.append([
                types.InlineKeyboardButton(
                    text=f"Купить {title_name}",
                    callback_data=f"buy_title_{price}"
                )
            ])

    buttons.append([
        types.InlineKeyboardButton(text="🔙 Назад", callback_data="menu_shop")
    ])

    await callback.message.edit_text(
        text,
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=buttons)
    )

    await callback.answer()


# =========================
# ПОКУПКА ТИТУЛА
# =========================

@dp.callback_query(F.data.startswith("buy_title_"))
async def buy_title_process(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    price = int(callback.data.split("buy_title_")[-1])

    data = get_user_data(user_id)

    title_name = TITLES_CONFIG[price]

    if data["rice"] < price:
        await callback.answer("❌ Недостаточно 🍙!", show_alert=True)
        return

    update_field(user_id, "users", "rice", data["rice"] - price)
    update_field(user_id, "users", "current_title", title_name)

    await callback.answer(f"🏅 Новый титул: {title_name}", show_alert=True)

    await shop_titles_callback(callback)


# =========================
# ИГРОВОЙ ЦЕНТР
# =========================

@dp.callback_query(F.data == "menu_games")
async def games_menu_callback(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "🎮 ИГРОВОЙ ЦЕНТР\n\n"
        "🎰 Казино / рулетка / дуэли / работа\n\n"
        "🎡 Нажми кнопку ниже:",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="🎡 Рулетка", callback_data="play_roulette")],
            [types.InlineKeyboardButton(text="🔙 Главное меню", callback_data="to_main")]
        ])
    )

    await callback.answer()


# =========================
# РУЛЕТКА (НАЧАЛО)
# =========================

@dp.callback_query(F.data == "play_roulette")
async def roulette_process(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    data = get_user_data(user_id)

    if not data:
        return

    now = int(time.time())

    is_vip = data["vip_until"] > now
    price = 0 if is_vip else 500

    if not is_vip and data["rice"] < price:
        await callback.answer("❌ Нужно 500 🍙!", show_alert=True)
        return

    update_field(user_id, "users", "rice", data["rice"] - price)

    result = random.choice(["win", "lose", "bigwin"])

    if result == "win":
        reward = random.randint(500, 2000)
        update_field(user_id, "users", "rice", data["rice"] + reward)
        msg = f"🎉 Победа! +{reward} 🍙"

    elif result == "bigwin":
        reward = random.randint(3000, 8000)
        update_field(user_id, "users", "rice", data["rice"] + reward)
        msg = f"🔥 ДЖЕКПОТ! +{reward} 🍙"

    else:
        msg = "💀 Вы проиграли!"

    await callback.message.edit_text(
        f"🎡 РУЛЕТКА\n\n{msg}",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="🔙 Назад", callback_data="menu_games")]
        ])
    )

    await callback.answer()
    
    # =========================
# РУЛЕТКА (ПРОДОЛЖЕНИЕ / ИСПРАВЛЕНИЕ)
# =========================

@dp.callback_query(F.data == "play_roulette")
async def roulette_process(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    data = get_user_data(user_id)

    if not data:
        return

    now = int(time.time())

    is_vip = data["vip_until"] > now
    price = 0 if is_vip else 500

    if not is_vip and data["rice"] < price:
        await callback.answer("❌ Обычная рулетка стоит 500 🍙!", show_alert=True)
        return

    if not is_vip:
        update_field(user_id, "users", "rice", data["rice"] - price)

    win_type = random.choice(["rice", "xp", "lose"])

    if win_type == "rice":
        amount = random.randint(100, 2500)
        new_data = get_user_data(user_id)
        update_field(user_id, "users", "rice", new_data["rice"] + amount)
        msg = f"🎉 УДАЧА! +{amount} 🍙"

    elif win_type == "xp":
        amount = random.randint(20, 60)
        xp_msg = add_xp(user_id, amount)
        msg = f"⚡ ОПЫТ! {xp_msg}"

    else:
        msg = "😢 НЕ ПОВЕЗЛО!"

    await callback.message.edit_text(
        f"🎡 РУЛЕТКА\n\n{msg}",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="🎡 Крутить снова", callback_data="play_roulette")],
            [types.InlineKeyboardButton(text="🔙 В меню", callback_data="menu_games")]
        ])
    )

    await callback.answer()


# =========================
# CASINO
# =========================

@dp.message(Command("casino"))
async def cmd_casino(message: types.Message):
    user_id = message.from_user.id
    data = get_user_data(user_id)

    if not data:
        return

    args = message.text.split()

    if len(args) < 2 or not args[1].isdigit():
        await message.answer("🎰 Используй: /casino 100")
        return

    bet = int(args[1])

    if bet <= 0 or data["rice"] < bet:
        await message.answer("❌ Неверная ставка!")
        return

    if random.choice([True, False]):
        update_field(user_id, "users", "rice", data["rice"] + bet)
        xp_msg = add_xp(user_id, random.randint(2, 8))
        await message.answer(f"🎰 ПОБЕДА +{bet} 🍙{xp_msg}")
    else:
        update_field(user_id, "users", "rice", data["rice"] - bet)
        await message.answer(f"🎰 ПРОИГРЫШ -{bet} 🍙")


# =========================
# DICE
# =========================

@dp.message(Command("dice"))
async def cmd_dice(message: types.Message):
    user_id = message.from_user.id
    data = get_user_data(user_id)

    if not data:
        return

    args = message.text.split()

    if len(args) < 3:
        await message.answer("🎲 /dice ставка число(1-6)")
        return

    bet = int(args[1])
    guess = int(args[2])

    if bet <= 0 or bet > data["rice"] or guess < 1 or guess > 6:
        await message.answer("❌ Ошибка!")
        return

    bot_dice = random.randint(1, 6)

    if guess == bot_dice:
        win = bet * 5
        update_field(user_id, "users", "rice", data["rice"] + win)
        xp_msg = add_xp(user_id, 10)
        await message.answer(f"🎲 ДЖЕКПОТ! {bot_dice} +{win} 🍙{xp_msg}")
    else:
        update_field(user_id, "users", "rice", data["rice"] - bet)
        await message.answer(f"🎲 МИМО! Выпало {bot_dice}")


# =========================
# TRADE
# =========================

@dp.message(Command("trade"))
async def cmd_trade(message: types.Message):
    user_id = message.from_user.id
    data = get_user_data(user_id)

    if not data:
        return

    args = message.text.split()

    if len(args) < 3:
        await message.answer("📊 /trade ставка вверх/вниз")
        return

    bet = int(args[1])
    direction = args[2].lower()

    if bet <= 0 or bet > data["rice"]:
        await message.answer("❌ Ошибка ставки!")
        return

    market = random.choice(["вверх", "вниз"])

    if direction == market:
        update_field(user_id, "users", "rice", data["rice"] + bet)
        xp_msg = add_xp(user_id, 5)
        await message.answer(f"📈 УГАДАЛ +{bet} 🍙{xp_msg}")
    else:
        update_field(user_id, "users", "rice", data["rice"] - bet)
        await message.answer(f"📉 ПРОИГРЫШ -{bet} 🍙")


# =========================
# WORK (ДОРАБОТАНО)
# =========================

@dp.message(Command("work"))
async def cmd_work(message: types.Message):
    user_id = message.from_user.id
    data = get_user_data(user_id)

    if not data:
        return

    now = int(time.time())

    if now - data["last_work"] < 7200:
        await message.answer("⏳ Ты устал! Подожди 2 часа.")
        return

    earn = random.randint(300, 1200)

    update_field(user_id, "users", "rice", data["rice"] + earn)
    update_field(user_id, "users", "last_work", now)

    xp_msg = add_xp(user_id, random.randint(5, 15))

    await message.answer(f"🌾 Работа завершена! +{earn} 🍙{xp_msg}")
    
    # =========================
# WORK (ПРОДОЛЖЕНИЕ)
# =========================

@dp.message(Command("work"))
async def cmd_work(message: types.Message):
    user_id = message.from_user.id
    data = get_user_data(user_id)

    if not data:
        return

    now = int(time.time())

    if now - data["last_work"] < 7200:
        rem = 7200 - (now - data["last_work"])
        await message.answer(
            f"⏳ Отдыхай ещё {rem // 60} мин!"
        )
        return

    earned = random.randint(150, 400)
    xp_earned = random.randint(5, 12)

    update_field(user_id, "users", "rice", data["rice"] + earned)
    update_field(user_id, "users", "last_work", now)

    xp_msg = add_xp(user_id, xp_earned)

    texts = [
        f"🌾 Ты собирал рис и заработал +{earned} 🍙{xp_msg}",
        f"🚜 Тяжёлая смена на тракторе: +{earned} 🍙{xp_msg}",
        f"🧺 Упаковка мешков завершена: +{earned} 🍙{xp_msg}"
    ]

    await message.answer(random.choice(texts))


# =========================
# ROB
# =========================

@dp.message(Command("rob"))
async def cmd_rob(message: types.Message):
    user_id = message.from_user.id
    data = get_user_data(user_id)

    if not data:
        return

    args = message.text.split()

    if len(args) < 2 or not args[1].isdigit():
        await message.answer("🥷 /rob ID игрока")
        return

    target_id = int(args[1])
    target_data = get_user_data(target_id)

    if not target_data or target_id == user_id:
        await message.answer("❌ Игрок не найден")
        return

    now = int(time.time())

    if now - data["last_rob"] < 14400:
        await message.answer("⏳ Полиция ищет тебя!")
        return

    update_field(user_id, "users", "last_rob", now)

    # защита амулетом
    if target_data["amulet"] > 0:
        update_field(target_id, "inventory", "amulet", target_data["amulet"] - 1)

        penalty = int(data["rice"] * 0.15)

        update_field(user_id, "users", "rice", data["rice"] - penalty)
        update_field(target_id, "users", "rice", target_data["rice"] + penalty)

        await message.answer("🛡 Амулет активирован! Ограбление провалилось.")
        return

    if random.random() < 0.40:
        stolen = int(target_data["rice"] * random.uniform(0.1, 0.3))
        stolen = max(stolen, 10)

        update_field(user_id, "users", "rice", data["rice"] + stolen)
        update_field(target_id, "users", "rice", target_data["rice"] - stolen)

        await message.answer(f"🥷 УСПЕХ! Ты украл +{stolen} 🍙 у {target_data['nickname']}")
    else:
        penalty = random.randint(200, 1000)
        penalty = min(penalty, data["rice"])

        update_field(user_id, "users", "rice", data["rice"] - penalty)

        await message.answer(f"🚨 ПОЙМАН! Штраф -{penalty} 🍙")


# =========================
# DUEL
# =========================

@dp.message(Command("duel"))
async def cmd_duel(message: types.Message):
    user_id = message.from_user.id
    data = get_user_data(user_id)

    if not data:
        return

    args = message.text.split()

    if len(args) < 3 or not args[1].isdigit() or not args[2].isdigit():
        await message.answer("⚔️ /duel ID ставка")
        return

    target_id = int(args[1])
    bet = int(args[2])

    target_data = get_user_data(target_id)

    if (
        not target_data
        or target_id == user_id
        or bet <= 0
        or data["rice"] < bet
        or target_data["rice"] < bet
    ):
        await message.answer("❌ Ошибка дуэли!")
        return

    p1 = data["nickname"]
    p2 = target_data["nickname"]

    await message.answer("⚔️ Бой начинается...")
    await asyncio.sleep(2)

    fight_scenarios = [
        f"⚔️ {p1} атакует {p2} мешком риса!",
        f"⚔️ {p2} контратакует и сбивает {p1} с ног!"
    ]

    if random.choice([True, False]):
        update_field(user_id, "users", "rice", data["rice"] + bet)
        update_field(target_id, "users", "rice", target_data["rice"] - bet)

        update_field(user_id, "users", "wins", data["wins"] + 1)
        update_field(target_id, "users", "losses", target_data["losses"] + 1)

        xp_msg = add_xp(user_id, random.randint(10, 20))

        await message.answer(
            f"{random.choice(fight_scenarios)}\n\n🏆 Победил {p1}! +{bet} 🍙{xp_msg}"
        )

    else:
        update_field(target_id, "users", "rice", target_data["rice"] + bet)
        update_field(user_id, "users", "rice", data["rice"] - bet)

        update_field(target_id, "users", "wins", target_data["wins"] + 1)
        update_field(user_id, "users", "losses", data["losses"] + 1)

        await message.answer(
            f"{random.choice(fight_scenarios)}\n\n🏆 Победил {p2}! -{bet} 🍙"
        )
        
       # =========================
# DUEL (ПРОДОЛЖЕНИЕ / ФИНАЛ)
# =========================

# победа второго игрока
update_field(user_id, "users", "rice", data["rice"] - bet)
update_field(target_id, "users", "rice", target_data["rice"] + bet)

update_field(user_id, "users", "losses", data["losses"] + 1)
update_field(target_id, "users", "wins", target_data["wins"] + 1)

xp_msg = add_xp(target_id, random.randint(10, 20))

await message.answer(
    f"{random.choice(fight_scenarios)}\n\n🏆 Победитель: {p2_text}! +{bet} 🍙"
)


# =========================
# DARTS (АЛИАС DUEL)
# =========================

@dp.message(Command("darts"))
async def cmd_darts(message: types.Message):
    try:
        await cmd_duel(message)
    except Exception:
        await message.answer("❌ Ошибка в дартс-дуэли!")


# =========================
# ЗАПУСК БОТА
# =========================

async def main():
    init_db()
    print("🚀 Рисовая Империя запущена!")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
    
    # ======================
# CASINO
# ======================

@dp.message(Command("casino"))
async def casino(message: types.Message):
    data = get_user_data(message.from_user.id)
    if not data:
        return

    args = message.text.split()

    if len(args) < 2 or not args[1].isdigit():
        await message.answer("🎰 /casino ставка")
        return

    bet = int(args[1])

    if bet <= 0 or data["rice"] < bet:
        await message.answer("❌ Неверная ставка")
        return

    if random.choice([True, False]):
        reward = bet * 2
        update_field(data["user_id"], "users", "rice", data["rice"] + reward)
        xp_msg = add_xp(data["user_id"], 5)

        await message.answer(f"🎰 ПОБЕДА +{reward} 🍙 {xp_msg}")
    else:
        update_field(data["user_id"], "users", "rice", data["rice"] - bet)
        await message.answer(f"🎰 ПРОИГРЫШ -{bet} 🍙")


# ======================
# DICE
# ======================

@dp.message(Command("dice"))
async def dice(message: types.Message):
    data = get_user_data(message.from_user.id)
    if not data:
        return

    args = message.text.split()

    if len(args) < 3:
        await message.answer("🎲 /dice ставка число(1-6)")
        return

    bet = int(args[1])
    guess = int(args[2])

    if bet <= 0 or bet > data["rice"]:
        await message.answer("❌ Ошибка ставки")
        return

    bot_roll = random.randint(1, 6)

    if guess == bot_roll:
        win = bet * 5
        update_field(data["user_id"], "users", "rice", data["rice"] + win)
        xp_msg = add_xp(data["user_id"], 10)

        await message.answer(f"🎲 ДЖЕКПОТ {bot_roll}! +{win} 🍙 {xp_msg}")
    else:
        update_field(data["user_id"], "users", "rice", data["rice"] - bet)
        await message.answer(f"🎲 Выпало {bot_roll}, ты проиграл!")


# ======================
# TRADE (простая версия)
# ======================

@dp.message(Command("trade"))
async def trade(message: types.Message):
    data = get_user_data(message.from_user.id)
    if not data:
        return

    args = message.text.split()

    if len(args) < 3:
        await message.answer("📊 /trade ставка вверх/вниз")
        return

    bet = int(args[1])
    choice = args[2].lower()

    if bet <= 0 or bet > data["rice"]:
        await message.answer("❌ Ошибка ставки")
        return

    market = random.choice(["вверх", "вниз"])

    if choice == market:
        update_field(data["user_id"], "users", "rice", data["rice"] + bet)
        xp_msg = add_xp(data["user_id"], 5)
        await message.answer(f"📈 УСПЕХ +{bet} 🍙 {xp_msg}")
    else:
        update_field(data["user_id"], "users", "rice", data["rice"] - bet)
        await message.answer(f"📉 ПРОВАЛ -{bet} 🍙")


# ======================
# MAIN LOOP
# ======================

async def main():
    print("🚀 Bot started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
    
    # ======================
# CASINO
# ======================

@dp.message(Command("casino"))
async def casino(message: types.Message):
    data = get_user_data(message.from_user.id)

    args = message.text.split()
    if len(args) < 2:
        await message.answer("Используй: /casino 100")
        return

    bet = int(args[1])

    if bet <= 0 or bet > data["rice"]:
        await message.answer("❌ Нет денег")
        return

    if random.choice([True, False]):
        update_field(data["user_id"], "users", "rice", data["rice"] + bet)
        await message.answer(f"🎰 WIN +{bet}")
    else:
        update_field(data["user_id"], "users", "rice", data["rice"] - bet)
        await message.answer(f"💀 LOSE -{bet}")


# ======================
# WORK
# ======================

@dp.message(Command("work"))
async def work(message: types.Message):
    data = get_user_data(message.from_user.id)

    earned = random.randint(100, 300)
    update_field(data["user_id"], "users", "rice", data["rice"] + earned)

    await message.answer(f"🌾 Ты заработал +{earned} 🍙")


# ======================
# MAIN
# ======================

async def main():
    print("Bot started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())