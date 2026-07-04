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

# 🔑 НАСТРОЙКИ ИМПЕРИИ: Вставь свой токен и свой личный ID из Telegram ниже
TOKEN = "8233072384:AAEd6QXeUxz6M5UV-v_0I3SXhpcDdWagDLY"
ADMIN_ID = 7303801260

 # <- Обязательно замени нули на свой ID (например: 54321098)

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())
DB_NAME = "rice_empire.db"

# Состояния FSM для регистрации и одиночных игр
class GameStates(StatesGroup):
    waiting_for_nickname = State()
    waiting_for_detective = State()
    cooking_step = State()
    cave_step = State()

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Таблица пользователей (Добавлен плейтайм, индекс действий и бан)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            nickname TEXT,
            rice INTEGER DEFAULT 100,
            xp INTEGER DEFAULT 0,
            level INTEGER DEFAULT 1,
            vip_until INTEGER DEFAULT 0,
            vip_days_bought INTEGER DEFAULT 0,
            current_title TEXT DEFAULT '🚫 Отсутствует',
            last_bonus INTEGER DEFAULT 0,
            last_work INTEGER DEFAULT 0,
            last_rob INTEGER DEFAULT 0,
            energy_until INTEGER DEFAULT 0,
            clover_until INTEGER DEFAULT 0,
            insurance_active INTEGER DEFAULT 0,
            wins INTEGER DEFAULT 0,
            losses INTEGER DEFAULT 0,
            playtime INTEGER DEFAULT 0,
            total_actions INTEGER DEFAULT 0,
            last_click_time INTEGER DEFAULT 0,
            is_banned INTEGER DEFAULT 0
        )
    ''')
    # Таблица бизнесов
    cursor.execute('''
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
    ''')
    # Таблица инвентаря под все 6 новых бустеров и 3 вида боксов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            user_id INTEGER PRIMARY KEY,
            energy_drink INTEGER DEFAULT 0,
            amulet INTEGER DEFAULT 0,
            clover INTEGER DEFAULT 0,
            fertilizer INTEGER DEFAULT 0,
            compass INTEGER DEFAULT 0,
            insurance INTEGER DEFAULT 0,
            box1 INTEGER DEFAULT 0,
            box2 INTEGER DEFAULT 0,
            box3 INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

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
    
    # Считаем и обновляем Playtime (время активности) при каждом запросе данных
    now = int(time.time())
    current_playtime = user[16]
    last_click = user[18]
    
    if last_click > 0 and (now - last_click) < 300: # Если клик был меньше 5 минут назад
        added_time = now - last_click
        current_playtime += added_time
        conn_upd = sqlite3.connect(DB_NAME)
        cursor_upd = conn_upd.cursor()
        cursor_upd.execute("UPDATE users SET playtime = ?, last_click_time = ? WHERE user_id = ?", (current_playtime, now, user_id))
        conn_upd.commit()
        conn_upd.close()
    else:
        conn_upd = sqlite3.connect(DB_NAME)
        cursor_upd = conn_upd.cursor()
        cursor_upd.execute("UPDATE users SET last_click_time = ? WHERE user_id = ?", (now, user_id))
        conn_upd.commit()
        conn_upd.close()

    return {
        "user_id": user[0], "nickname": user[1], "rice": user[2], "xp": user[3],
        "level": user[4], "vip_until": user[5], "vip_days_bought": user[6], "current_title": user[7],
        "last_bonus": user[8], "last_work": user[9], "last_rob": user[10],
        "energy_until": user[11], "clover_until": user[12], "insurance_active": user[13],
        "wins": user[14], "losses": user[15], "playtime": current_playtime, "total_actions": user[17],
        "last_click_time": now, "is_banned": user[19],
        "b1": biz[1], "b2": biz[2], "b3": biz[3], "b4": biz[4], "b5": biz[5], "b6": biz[6], "b7": biz[7],
        "last_passive_collect": biz[8],
        "energy_drink": inv[1], "amulet": inv[2], "clover": inv[3], "fertilizer": inv[4],
        "compass": inv[5], "insurance": inv[6], "box1": inv[7], "box2": inv[8], "box3": inv[9]
    }

def register_user(user_id, nickname):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    now = int(time.time())
    cursor.execute("INSERT OR REPLACE INTO users (user_id, nickname, last_bonus, last_work, last_passive_collect, last_rob, last_click_time) VALUES (?, ?, 0, 0, 0, 0, ?)", (user_id, nickname, now))
    cursor.execute("INSERT OR REPLACE INTO businesses (user_id, last_passive_collect) VALUES (?, ?)", (user_id, now))
    cursor.execute("INSERT OR REPLACE INTO inventory (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()

def update_field(user_id, table, field, value):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(f"UPDATE {table} SET {field} = ? WHERE user_id = ?", (value, user_id))
    conn.commit()
    conn.close()

def track_action(user_id):
    data = get_user_data(user_id)
    if data:
        update_field(user_id, "users", "total_actions", data["total_actions"] + 1)
# ==========================================
# КОНФИГУРАЦИЯ И ЭКОНОМИКА ИМПЕРИИ
# ==========================================
BUSINESS_CONFIG = {
    "b1": {"name": "🌱 Рисовая грядка", "price": 500, "income": 5},
    "b2": {"name": "🧺 Небольшая теплица", "price": 2500, "income": 30},
    "b3": {"name": "🚜 Автоматическая плантация", "price": 10000, "income": 130},
    "b4": {"name": "🏭 Сельская фабрика", "price": 25000, "income": 350},
    "b5": {"name": "🏢 Рисовый синдикат", "price": 50000, "income": 750},
    "b6": {"name": "🚀 Международный экспорт", "price": 100000, "income": 1600},
    "b7": {"name": "🌌 Межгалактическая корпорация", "price": 250000, "income": 4500}
}

TITLES_CONFIG = {
    2000: "🌱 Рисовый росток", 5000: "🌾 Помощник на поле", 15000: "🚜 Смотритель плантации",
    20000: "🌾 Мастер урожая", 40000: "💼 Поставщик риса", 50000: "🏯 Хозяин полей",
    70000: "💎 Золотой колос", 80000: "👑 Хранительница урожая", 100000: "🌌 Императрица Галактики"
}

def get_auto_status(rice):
    if rice < 5000: return "🌾 Новичок"
    elif rice < 10000: return "🚜 Работяга"
    elif rice < 18000: return "🧺 Сборщик урожая"
    elif rice < 25000: return "🍙 Мастер Суши"
    elif rice < 35000: return "🏪 Владелец Лавки"
    elif rice < 50000: return "📈 Рисовый Трейдер"
    elif rice < 70000: return "🏯 Помещик"
    elif rice < 100000: return "💎 Олигарх Плантаций"
    else: return "👑 Рисовый Бог"

def get_required_xp(level):
    if level <= 5: return 25
    elif level <= 15: return 100
    elif level <= 20: return 150
    else: return 200

def make_progress_bar(current, total):
    if total <= 0: return "[⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜] 0%"
    filled_length = int(10 * current // total)
    if filled_length > 10: filled_length = 10
    if filled_length < 0: filled_length = 0
    bar = "🟩" * filled_length + "⬜" * (10 - filled_length)
    percentage = min(100, int((current / total) * 100))
    return f"`{bar}` **{percentage}%**"

def add_xp(user_id, xp_to_add):
    data = get_user_data(user_id)
    if not data or data["level"] >= 25: return ""
    
    now = int(time.time())
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
        
        if current_level == 15:
            reward_text += "🎁 **RICE PASS SUPREME!** Тебе начислен **VIP-статус на 2 дня**! 👑\n"
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
                r_rice = random.randint(2000, 6000)
                r_xp = random.randint(30, 50)
            
            reward_text += f"🎁 **Награда за {current_level} уровень:** +{r_rice} 🍙 и +{r_xp} бонусных XP!\n"
            update_field(user_id, "users", "rice", get_user_data(user_id)["rice"] + r_rice)
            new_xp += r_xp

    update_field(user_id, "users", "xp", new_xp)
    update_field(user_id, "users", "level", current_level)
    
    if leveled_up:
        return f"\n\n🎉 **ПОВЫШЕНИЕ РАНГА RICE PASS!** Ты достиг **{current_level} уровня**! 🎉\n" + reward_text
    return f"\n✨ +{xp_to_add} XP для Rice Pass"

def calc_passive_income(data):
    now = int(time.time())
    seconds_passed = now - data["last_passive_collect"]
    hours_passed = seconds_passed / 3600.0
    
    if hours_passed <= 0: return 0
    
    total_income_per_hour = 0
    for key, config in BUSINESS_CONFIG.items():
        total_income_per_hour += data[key] * config["income"]
        
    if data["energy_until"] > now:
        total_income_per_hour = int(total_income_per_hour * 1.5)
        
    return int(hours_passed * total_income_per_hour)
# ==========================================
# НИЖНИЕ КЛАВИАТУРЫ ИНТЕРФЕЙСА (REPLY)
# ==========================================
def main_keyboard(user_id):
    buttons = [
        [types.KeyboardButton(text="👤 Мой Профиль"), types.KeyboardButton(text="🏪 Магазин Империи")],
        [types.KeyboardButton(text="🌾 Сбор Бонуса"), types.KeyboardButton(text="🎒 Мой Инвентарь")],
        [types.KeyboardButton(text="🎮 Игровой Центр"), types.KeyboardButton(text="🏆 Топ Империи")]
    ]
    if user_id == ADMIN_ID:
        buttons.append([types.KeyboardButton(text="👑 Админ Панель")])
    return types.ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def shop_categories_keyboard():
    return types.ReplyKeyboardMarkup(keyboard=[
        [types.KeyboardButton(text="🚜 Рисовые Предприятия"), types.KeyboardButton(text="👑 VIP-Подписка")],
        [types.KeyboardButton(text="🎫 Уровни Rice Pass XP"), types.KeyboardButton(text="🥤 Расходники и Бусты")],
        [types.KeyboardButton(text="📦 Кейсы и Сундуки"), types.KeyboardButton(text="🏅 Магазин Титулов")],
        [types.KeyboardButton(text="🔙 Главное Меню")]
    ], resize_keyboard=True)

def admin_keyboard():
    return types.ReplyKeyboardMarkup(keyboard=[
        [types.KeyboardButton(text="📊 Статистика"), types.KeyboardButton(text="🔍 Чек Профиля")],
        [types.KeyboardButton(text="🎁 Выдать Себе"), types.KeyboardButton(text="🚫 Бан / Разбан")],
        [types.KeyboardButton(text="🔙 Главное Меню")]
    ], resize_keyboard=True)

# ==========================================
# КОМАНДЫ СТАРТА И РЕГИСТРАЦИИ ИГРОКА
# ==========================================
@dp.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    init_db()
    user_id = message.from_user.id
    data = get_user_data(user_id)
    
    if data:
        if data["is_banned"] == 1:
            await message.answer("❌ **Ты заблокирован в Рисовой Империи!**", parse_mode="Markdown")
            return
        track_action(user_id)
        await message.answer(
            f"👋 Приветствуем снова, **{data['nickname']}** в Рисовой Империи! 🍙\n"
            f"Используй нижнее меню для управления рисовой базой:", 
            parse_mode="Markdown", 
            reply_markup=main_keyboard(user_id)
        )
    else:
        await message.answer(
            "👋 **Добро пожаловать в текстовую вселенную Рисовой Империи!** 🍙\n\n"
            "Перед тем как начать копить богатства, строить заводы и участвовать в дуэлях, "
            "придумай свой **уникальный игровой никнейм**.\n\n"
            "✏️ _Введи никнейм прямо сейчас в ответном сообщении:_ ", 
            parse_mode="Markdown"
        )
        await state.set_state(RegistrationStates.waiting_for_nickname)

@dp.message(RegistrationStates.waiting_for_nickname)
async def process_nickname(message: types.Message, state: FSMContext):
    nickname = message.text.strip()
    if len(nickname) < 2 or len(nickname) > 20 or "/" in nickname:
        await message.answer("❌ Никнейм должен содержать от 2 до 20 символов и не иметь косых черт! Попробуй еще раз:")
        return
        
    register_user(message.from_user.id, nickname)
    await state.clear()
    track_action(message.from_user.id)
    await message.answer(
        f"🎉 **Отлично! Твой игровой профиль успешно создан.**\n"
        f"Твой никнейм: **{nickname}**\n"
        f"Тебе начислено стартовые 100 🍙!\n\n"
        f"_Начнем строить империю!_ 👇", 
        parse_mode="Markdown", 
        reply_markup=main_keyboard(message.from_user.id)
    )

@dp.message(lambda msg: msg.text == "🔙 Главное Меню")
async def back_to_main_msg(message: types.Message):
    data = get_user_data(message.from_user.id)
    if not data or data["is_banned"] == 1: return
    track_action(message.from_user.id)
    await message.answer("🗂 **Главное управление рисовой базой:**", parse_mode="Markdown", reply_markup=main_keyboard(message.from_user.id))
# ==========================================
# ОБРАБОТЧИКИ ПРОФИЛЯ, БОНУСА И ИНВЕНТАРЯ
# ==========================================
@dp.message(lambda msg: msg.text == "👤 Мой Профиль")
async def profile_msg_handler(message: types.Message):
    user_id = message.from_user.id
    data = get_user_data(user_id)
    if not data or data["is_banned"] == 1: return
    
    track_action(user_id)
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
        energy_status = " ⚡ _(Энергетик x1.5)_"
        
    auto_status = get_auto_status(data["rice"])
    req_xp = get_required_xp(data["level"])
    progress_bar = make_progress_bar(data["xp"], req_xp)
    
    # Форматирование времени в игре (из секунд в часы и минуты)
    p_hours = data["playtime"] // 3600
    p_minutes = (data["playtime"] % 3600) // 60
    
    profile_text = (
        f"👤 **ИГРОВОЙ ПРОФИЛЬ ИМПЕРИИ**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🆔 **Твой ID:** `{data['user_id']}`\n"
        f"👤 **Никнейм:** *{data['nickname']}*\n"
        f"🏅 **Купленный Титул:** `{data['current_title']}`\n"
        f"📊 **Ранг за богатство:** *{auto_status}*\n"
        f"👑 **VIP-Статус:** {vip_status}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🍙 **Баланс риса:** **{data['rice']} 🍙**{energy_status}\n"
        f"🎟 **Rice Pass:** `{data['level']}/25 Уровень`\n"
        f"🔹 Прогресс XP: {progress_bar} _({data['xp']}/{req_xp} XP)_\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"⏱ **Время в игре:** {p_hours} ч. {p_minutes} мин.\n"
        f"⚡ **Всего действий:** {data['total_actions']}\n"
        f"⚔️ **Дуэли:** 🏆 {data['wins']} | 💀 {data['losses']}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🌾 _Пассивный доход начислен автоматически!_"
    )
    await message.answer(profile_text, parse_mode="Markdown", reply_markup=main_keyboard(user_id))

@dp.message(lambda msg: msg.text == "🌾 Сбор Бонуса")
async def bonus_msg_handler(message: types.Message):
    user_id = message.from_user.id
    data = get_user_data(user_id)
    if not data or data["is_banned"] == 1: return
    
    track_action(user_id)
    now = int(time.time())
    cooldown = 6 * 3600
    
    if now - data["last_bonus"] < cooldown:
        time_left = cooldown - (now - data["last_bonus"])
        hours = time_left // 3600
        minutes = (time_left % 3600) // 60
        await message.answer(f"⏳ **Сбор плантации закрыт!**\n\nТвои крестьяне отдыхают. Сбор будет доступен через: **{hours} ч. {minutes} мин.** 🍙", parse_mode="Markdown")
        return
        
    is_vip = data["vip_until"] > now
    if is_vip:
        give_rice = 3500
        give_xp = random.randint(20, 40)
        vip_tag = "👑 **VIP Бонус**"
    else:
        give_rice = 2000
        give_xp = random.randint(5, 25)
        vip_tag = "🌾 **Обычный Бонус**"
        
    update_field(user_id, "users", "rice", data["rice"] + give_rice)
    update_field(user_id, "users", "last_bonus", now)
    xp_msg = add_xp(user_id, give_xp)
    
    await message.answer(f"{vip_tag} успешно собран!\n\n🧺 Ты проверил поля:\n💰 Получено: **+{give_rice} 🍙**\n{xp_msg}", parse_mode="Markdown")

@dp.message(lambda msg: msg.text == "🎒 Мой Инвентарь")
async def inventory_msg_handler(message: types.Message):
    user_id = message.from_user.id
    data = get_user_data(user_id)
    if not data or data["is_banned"] == 1: return
    
    track_action(user_id)
    inv_text = (
        f"🎒 **ТВОЙ КАРМАННЫЙ ИНВЕНТАРЬ**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🥤 Рисовый энергетик (x1.5): **{data['energy_drink']} шт.**\n"
        f"🛡 Амулет от наглых воров: **{data['amulet']} шт.**\n"
        f"🍀 Счастливый клевер (Казино): **{data['clover']} шт.**\n"
        f"🧪 Удобрение «Мега-Рост»: **{data['fertilizer']} шт.**\n"
        f"🧲 Золотой Компас (Вор): **{data['compass']} шт.**\n"
        f"📜 Императорский Указ (Страховка): **{data['insurance']} шт.**\n\n"
        f"📦 **Хранилище сундуков:**\n"
        f"├ 📦 Рисовая коробка: {data['box1']} шт.\n"
        f"├ 💎 Ларец Сенсея: {data['box2']} шт.\n"
        f"└ 🌌 Императорский сундук: {data['box3']} шт.\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"⚡ _Для использования бустов или открытия сундуков нажми кнопки ниже:_ "
    )
    
    buttons = []
    if data["energy_drink"] > 0: buttons.append([types.InlineKeyboardButton(text="🥤 Выпить Энергетик", callback_data="use_energy")])
    if data["clover"] > 0: buttons.append([types.InlineKeyboardButton(text="🍀 Активировать Клевер", callback_data="use_clover")])
    if data["fertilizer"] > 0: buttons.append([types.InlineKeyboardButton(text="🧪 Насыпать Удобрение", callback_data="use_fertilizer")])
    if data["insurance"] > 0: buttons.append([types.InlineKeyboardButton(text="📜 Зачитать Указ (Страховка)", callback_data="use_insurance")])
    if data["box1"] > 0: buttons.append([types.InlineKeyboardButton(text="📦 Открыть Рисовую коробку", callback_data="open_box1")])
    if data["box2"] > 0: buttons.append([types.InlineKeyboardButton(text="💎 Открыть Ларец Сенсея", callback_data="open_box2")])
    if data["box3"] > 0: buttons.append([types.InlineKeyboardButton(text="🌌 Открыть Императорский сундук", callback_data="open_box3")])
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=buttons) if buttons else None
    await message.answer(inv_text, parse_mode="Markdown", reply_markup=kb)
# ==========================================
# ИСПОЛЬЗОВАНИЕ ПРЕДМЕТОВ И СУНДУКОВ
# ==========================================
@dp.callback_query(F.data == "use_energy")
async def use_energy_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    data = get_user_data(user_id)
    if not data or data["energy_drink"] <= 0 or data["is_banned"] == 1: return
    
    now = int(time.time())
    new_time = max(data["energy_until"], now) + 3600
    update_field(user_id, "inventory", "energy_drink", data["energy_drink"] - 1)
    update_field(user_id, "users", "energy_until", new_time)
    track_action(user_id)
    
    await callback.message.edit_text("🥤 **Глоток энергии!**\n\nТы выпил рисовый энергетик. Теперь в течение **1 часа** все твои заводы и грядки приносят в **полтора раза (x1.5) больше 🍙** пассивного дохода!", parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "use_clover")
async def use_clover_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    data = get_user_data(user_id)
    if not data or data["clover"] <= 0 or data["is_banned"] == 1: return
    
    now = int(time.time())
    new_time = max(data["clover_until"], now) + 1800
    update_field(user_id, "inventory", "clover", data["clover"] - 1)
    update_field(user_id, "users", "clover_until", new_time)
    track_action(user_id)
    
    await callback.message.edit_text("🍀 **Удача на твоей стороне!**\n\nТы активировал Счастливый клевер. В течение следующих **30 минут** твой шанс выиграть в Казино и Трейдинге поднят до **65%**!", parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "use_fertilizer")
async def use_fertilizer_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    data = get_user_data(user_id)
    if not data or data["fertilizer"] <= 0 or data["is_banned"] == 1: return
    
    update_field(user_id, "inventory", "fertilizer", data["fertilizer"] - 1)
    update_field(user_id, "users", "last_bonus", 0)
    update_field(user_id, "users", "last_work", 0)
    track_action(user_id)
    
    await callback.message.edit_text("🧪 **Мгновенное созревание!**\n\nТы распылил удобрение «Мега-Рост». Все таймеры перезарядки сброшены! Ты можешь прямо сейчас снова собрать Бонус и пойти на Работу!", parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "use_insurance")
async def use_insurance_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    data = get_user_data(user_id)
    if not data or data["insurance"] <= 0 or data["is_banned"] == 1: return
    
    update_field(user_id, "inventory", "insurance", data["insurance"] - 1)
    update_field(user_id, "users", "insurance_active", 1)
    track_action(user_id)
    
    await callback.message.edit_text("📜 **Императорская защита!**\n\nТы зачитал Императорский Указ. Теперь твой баланс застрахован на **12 часов**. Если ты проиграешь в казино, на бирже или тебя ограбят — указ вернет тебе 100% потерь (сработает один раз на неудачу)!", parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data.startswith("open_box"))
async def open_box_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    box_type = callback.data.split("box")[-1]
    data = get_user_data(user_id)
    if not data or data["is_banned"] == 1: return
    
    track_action(user_id)
    if box_type == "1" and data["box1"] > 0:
        update_field(user_id, "inventory", "box1", data["box1"] - 1)
        res = random.choice(["rice", "xp", "drink"])
        if res == "rice":
            val = random.randint(500, 2000)
            update_field(user_id, "users", "rice", data["rice"] + val)
            msg = f"💰 Из коробки выпало: **+{val} 🍙**!"
        elif res == "xp":
            val = random.randint(15, 40)
            xp_msg = add_xp(user_id, val)
            msg = f"🎫 Из коробки выпало: {xp_msg}"
        else:
            update_field(user_id, "inventory", "energy_drink", data["energy_drink"] + 1)
            msg = "🥤 Удача! Из коробки выпал **1 Рисовый энергетик**!"
            
    elif box_type == "2" and data["box2"] > 0:
        update_field(user_id, "inventory", "box2", data["box2"] - 1)
        res = random.choice(["rice", "xp", "vip"])
        if res == "rice":
            val = random.randint(2500, 8000)
            update_field(user_id, "users", "rice", data["rice"] + val)
            msg = f"💰 Из Ларца Сенсея выпало: **+{val} 🍙**!"
        elif res == "xp":
            val = random.randint(50, 120)
            xp_msg = add_xp(user_id, val)
            msg = f"🎫 Из Ларца Сенсея выпало: {xp_msg}"
        else:
            now = int(time.time())
            vip_time = max(data["vip_until"], now) + (3 * 24 * 3600)
            update_field(user_id, "users", "vip_until", vip_time)
            msg = "👑 **ОГО! СУПЕР ПРИЗ!** Из ларца выпал **VIP-статус на 3 дня**!"
            
    elif box_type == "3" and data["box3"] > 0:
        update_field(user_id, "inventory", "box3", data["box3"] - 1)
        r_rice = random.randint(7000, 30000)
        r_xp = random.randint(150, 400)
        update_field(user_id, "users", "rice", data["rice"] + r_rice)
        xp_msg = add_xp(user_id, r_xp)
        
        item = random.choice(["drink", "amulet", "vip10"])
        if item == "drink":
            update_field(user_id, "inventory", "energy_drink", data["energy_drink"] + 3)
            item_text = "🥤 **3 Рисовых энергетика**"
        elif item == "amulet":
            update_field(user_id, "inventory", "amulet", data["amulet"] + 1)
            item_text = "🛡 **1 Амулет от воров**"
        else:
            now = int(time.time())
            vip_time = max(data["vip_until"], now) + (10 * 24 * 3600)
            update_field(user_id, "users", "vip_until", vip_time)
            item_text = "👑 **VIP-СТАТУС НА 10 ДНЕЙ!**"
            
        msg = f"🌌 **Двойной Дроп из Императорского сундука!**\n\n🎁 **Приз №1 (Ресурсы):** +{r_rice} 🍙 и {xp_msg}\n🎁 **Приз №2 (Вещь в инвентарь):** Добавлено {item_text}!"
    else:
        await callback.answer("Сундук закончился!")
        return
        
    await callback.message.edit_text(f"🎉 **ОТКРЫТИЕ КЕЙСА:**\n\n{msg}", parse_mode="Markdown")
    await callback.answer()
# ==========================================
# МАГАЗИН ИМПЕРИИ И КАТЕГОРИИ (КЛАВИАТУРА) - ЧАСТЬ 1
# ==========================================
@dp.message(lambda msg: msg.text == "🏪 Магазин Империи")
async def shop_main_handler(message: types.Message):
    user_id = message.from_user.id
    data = get_user_data(user_id)
    if not data or data["is_banned"] == 1: return
    track_action(user_id)
    await message.answer(
        f"🏪 **ДОБРО ПОЖАЛОВАТЬ В ТОРГОВЫЙ ЦЕНТР ИМПЕРИИ!** 🍙\n\n"
        f"💰 Твой баланс: **{data['rice']} 🍙**\n\n"
        f"⬇️ _Используй нижнюю клавиатуру телефона для перехода по категориям товаров:_ ",
        parse_mode="Markdown", reply_markup=shop_categories_keyboard()
    )

@dp.message(lambda msg: msg.text == "🚜 Рисовые Предприятия")
async def shop_biz_handler(message: types.Message):
    user_id = message.from_user.id
    data = get_user_data(user_id)
    if not data or data["is_banned"] == 1: return
    track_action(user_id)
    
    text = "🚜 **МАГАЗИН: РИСОВЫЕ ПРЕДПРИЯТИЯ (Доход в час)**\n\n"
    buttons = []
    for key, cfg in BUSINESS_CONFIG.items():
        text += f"▪️ {cfg['name']} | Цена: {cfg['price']} 🍙 | Доход: +{cfg['income']} 🍙/ч\n   👉 У тебя: {data[key]} шт.\n\n"
        buttons.append([types.InlineKeyboardButton(text=f"Купить {cfg['name']}", callback_data=f"buy_biz_{key}")])
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer(text, parse_mode="Markdown", reply_markup=kb)

@dp.callback_query(F.data.startswith("buy_biz_"))
async def buy_biz_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    biz_key = callback.data.split("buy_biz_")[-1]
    data = get_user_data(user_id)
    if not data or data["is_banned"] == 1: return
    cfg = BUSINESS_CONFIG[biz_key]
    
    if data["rice"] < cfg["price"]:
        await callback.answer(f"❌ Недостаточно 🍙! Нужно {cfg['price']}", show_alert=True)
        return
        
    update_field(user_id, "users", "rice", data["rice"] - cfg["price"])
    update_field(user_id, "businesses", biz_key, data[biz_key] + 1)
    track_action(user_id)
    await callback.answer(f"🎉 Вы успешно приобрели {cfg['name']}!", show_alert=True)

@dp.message(lambda msg: msg.text == "👑 VIP-Подписка")
async def shop_vip_handler(message: types.Message):
    user_id = message.from_user.id
    data = get_user_data(user_id)
    if not data or data["is_banned"] == 1: return
    track_action(user_id)
    
    text = (
        f"👑 **МАГАЗИН: ПОКУПКА VIP-СТАТУСА**\n\n"
        f"💰 Твой баланс: **{data['rice']} 🍙**\n\n"
        f"✨ **Преимущества VIP:**\n"
        f"├ Доход со всех бонусов увеличен!\n"
        f"├ Бесплатный ежедневный прокрут рулетки!\n"
        f"├ Ускоренное получение опыта Rice Pass (x1.5)!\n"
        f"└ 🔥 **Элитный Буст (x1.3)** на все призы Кухни и Экспедиций (при покупке тарифов на 20 и 30 дней)!\n\n"
        f"🛒 _Выбери тариф подписки на кнопках под текстом:_ "
    )
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🎫 VIP на 10 дней — 12 000 🍙", callback_data="buy_vip_10")],
        [types.InlineKeyboardButton(text="🎫 VIP на 20 дней — 18 000 🍙 🔥", callback_data="buy_vip_20")],
        [types.InlineKeyboardButton(text="🎫 VIP на 30 дней — 25 000 🍙 🔥", callback_data="buy_vip_30")]
    ])
    await message.answer(text, parse_mode="Markdown", reply_markup=kb)

@dp.callback_query(F.data.startswith("buy_vip_"))
async def buy_vip_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    days = int(callback.data.split("buy_vip_")[-1])
    data = get_user_data(user_id)
    if not data or data["is_banned"] == 1: return
    
    prices = {10: 12000, 20: 18000, 30: 25000}
    price = prices[days]
    
    if data["rice"] < price:
        await callback.answer(f"❌ Недостаточно 🍙! Нужно {price}", show_alert=True)
        return
        
    now = int(time.time())
    new_vip_time = max(data["vip_until"], now) + (days * 24 * 3600)
    
    update_field(user_id, "users", "rice", data["rice"] - price)
    update_field(user_id, "users", "vip_until", new_vip_time)
    update_field(user_id, "users", "vip_days_bought", days)
    track_action(user_id)
    await callback.answer(f"🎉 Поздравляем! VIP-статус успешно оформлен на {days} дней!", show_alert=True)

@dp.message(lambda msg: msg.text == "🎫 Уровни Rice Pass XP")
async def shop_xp_handler(message: types.Message):
    user_id = message.from_user.id
    data = get_user_data(user_id)
    if not data or data["is_banned"] == 1: return
    track_action(user_id)
    
    text = (
        f"🎫 **МАГАЗИН: ПАКИ ОПЫТА RICE PASS**\n\n"
        f"💰 Твой баланс: **{data['rice']} 🍙**\n\n"
        f"1. 🍬 Конфета XP (+25 XP) — 600 🍙\n"
        f"2. 🔋 Малый пак XP (+75 XP) — 1 800 🍙\n"
        f"3. 📦 Средняя коробка XP (+150 XP) — 3 500 🍙\n"
        f"4. 🚀 Большой контейнер XP (+300 XP) — 6 500 🍙\n"
        f"5. 🎫 Билет Прорыва (+1 Уровень) — 9 000 000 🍙"
    )
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🍬 Конфета", callback_data="buy_xp_1"), types.InlineKeyboardButton(text="🔋 Малый пак", callback_data="buy_xp_2")],
        [types.InlineKeyboardButton(text="📦 Коробка", callback_data="buy_xp_3"), types.InlineKeyboardButton(text="🚀 Контейнер", callback_data="buy_xp_4")],
        [types.InlineKeyboardButton(text="🎫 Купить Скип Уровня", callback_data="buy_xp_5")]
    ])
    await message.answer(text, parse_mode="Markdown", reply_markup=kb)

@dp.callback_query(F.data.startswith("buy_xp_"))
async def buy_xp_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    pack_type = callback.data.split("buy_xp_")[-1]
    data = get_user_data(user_id)
    if not data or data["is_banned"] == 1: return
    
    config = {
        "1": {"price": 600, "xp": 25, "skip": False},
        "2": {"price": 1800, "xp": 75, "skip": False},
        "3": {"price": 3500, "xp": 150, "skip": False},
        "4": {"price": 6500, "xp": 300, "skip": False},
        "5": {"price": 9000, "xp": 0, "skip": True}
    }
    cfg = config[pack_type]
    
    if data["rice"] < cfg["price"]:
        await callback.answer(f"❌ Недостаточно 🍙! Нужно {cfg['price']}", show_alert=True)
        return
        
    update_field(user_id, "users", "rice", data["rice"] - cfg["price"])
    track_action(user_id)
    if cfg["skip"]:
        if data["level"] < 25:
            update_field(user_id, "users", "level", data["level"] + 1)
            update_field(user_id, "users", "xp", 0)
            await callback.answer("🎉 Уровень Rice Pass успешно повышен!", show_alert=True)
        else:
            await callback.answer("❌ У тебя уже максимальный уровень!", show_alert=True)
    else:
        xp_msg = add_xp(user_id, cfg["xp"])
        await callback.answer(f"🎉 Опыт добавлен! {xp_msg.replace('**', '')}", show_alert=True)
# ==========================================
# МАГАЗИН ИМПЕРИИ И КАТЕГОРИИ (КЛАВИАТУРА) - ЧАСТЬ 2
# ==========================================
@dp.message(lambda msg: msg.text == "🥤 Расходники и Бусты")
async def shop_items_handler(message: types.Message):
    user_id = message.from_user.id
    data = get_user_data(user_id)
    if not data or data["is_banned"] == 1: return
    track_action(user_id)
    
    text = (
        f"🥤 **МАГАЗИН: РАСХОДНИКИ И БУСТЕРЫ**\n\n"
        f"💰 Твой баланс: **{data['rice']} 🍙**\n\n"
        f"1. 🥤 **Рисовый энергетик** — 1 000 🍙\n"
        f"👉 _Дает x1.5 ко всему пассивному доходу на 1 час!_\n\n"
        f"2. 🛡 **Амулет от воров** — 2 000 🍙\n"
        f"👉 _Защищает баланс от 1 ограбления, вор платит штраф!_\n\n"
        f"3. 🍀 **Счастливый клевер** — 1 500 🍙\n"
        f"👉 _Повышает шанс победы в Казино и Трейдинге до 65% на 30 мин!_\n\n"
        f"4. 🧪 **Удобрение «Мега-Рост»** — 3 000 🍙\n"
        f"👉 _Мгновенно сбрасывает время перезарядки Бонуса и Работы!_\n\n"
        f"5. 🧲 **Золотой Компас** — 2 500 🍙\n"
        f"👉 _Повышает шанс успешного налета /rob до 70% на 1 раз!_\n\n"
        f"6. 📜 **Императорский Указ** — 4 500 🍙\n"
        f"👉 _Страховка: возвращает 100% проигрыша в играх /rob на 12 часов!_"
    )
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="Купить Энергетик 🥤", callback_data="buy_item_drink"), types.InlineKeyboardButton(text="Купить Амулет 🛡", callback_data="buy_item_amulet")],
        [types.InlineKeyboardButton(text="Купить Клевер 🍀", callback_data="buy_item_clover"), types.InlineKeyboardButton(text="Купить Удобрение 🧪", callback_data="buy_item_fertilizer")],
        [types.InlineKeyboardButton(text="Купить Компас 🧲", callback_data="buy_item_compass"), types.InlineKeyboardButton(text="Купить Указ 📜", callback_data="buy_item_insurance")]
    ])
    await message.answer(text, parse_mode="Markdown", reply_markup=kb)

@dp.callback_query(F.data.startswith("buy_item_"))
async def buy_item_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    item = callback.data.split("buy_item_")[-1]
    data = get_user_data(user_id)
    if not data or data["is_banned"] == 1: return
    
    prices = {"drink": 1000, "amulet": 2000, "clover": 1500, "fertilizer": 3000, "compass": 2500, "insurance": 4500}
    db_fields = {"drink": "energy_drink", "amulet": "amulet", "clover": "clover", "fertilizer": "fertilizer", "compass": "compass", "insurance": "insurance"}
    
    price = prices.get(item, 999999)
    field = db_fields.get(item)
    
    if data["rice"] < price:
        await callback.answer(f"❌ Недостаточно 🍙! Нужно {price}", show_alert=True)
        return
        
    update_field(user_id, "users", "rice", data["rice"] - price)
    update_field(user_id, "inventory", field, data[field] + 1)
    track_action(user_id)
    await callback.answer("🎉 Товар успешно приобретен и добавлен в твой 🎒 Инвентарь!", show_alert=True)

@dp.message(lambda msg: msg.text == "📦 Кейсы и Сундуки")
async def shop_boxes_handler(message: types.Message):
    user_id = message.from_user.id
    data = get_user_data(user_id)
    if not data or data["is_banned"] == 1: return
    track_action(user_id)
    
    text = (
        f"📦 **МАГАЗИН: СУНДУКИ С СЮРПРИЗОМ**\n\n"
        f"💰 Твой баланс: **{data['rice']} 🍙**\n\n"
        f"1. **Рисовая коробка** 📦 — 1 500 🍙\n"
        f"2. **Ларец Сенсея** 💎 — 5 000 🍙\n"
        f"3. **Императорский сундук** 🌌 — 15 000 🍙 *(Гарантированный двойной дроп!)*"
    )
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="Купить Коробку 📦", callback_data="buy_box_1")],
        [types.InlineKeyboardButton(text="Купить Ларец 💎", callback_data="buy_box_2")],
        [types.InlineKeyboardButton(text="Купить Сундук 🌌", callback_data="buy_box_3")]
    ])
    await message.answer(text, parse_mode="Markdown", reply_markup=kb)

@dp.callback_query(F.data.startswith("buy_box_"))
async def buy_box_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    box_num = callback.data.split("buy_box_")[-1]
    data = get_user_data(user_id)
    if not data or data["is_banned"] == 1: return
    
    prices = {"1": 1500, "2": 5000, "3": 15000}
    db_fields = {"1": "box1", "2": "box2", "3": "box3"}
    
    price = prices[box_num]
    field = db_fields[box_num]
    
    if data["rice"] < price:
        await callback.answer(f"❌ Недостаточно 🍙! Нужно {price}", show_alert=True)
        return
        
    update_field(user_id, "users", "rice", data["rice"] - price)
    update_field(user_id, "inventory", field, data[field] + 1)
    track_action(user_id)
    await callback.answer("🎉 Сундук успешно куплен и добавлен в твой 🎒 Инвентарь!", show_alert=True)

@dp.message(lambda msg: msg.text == "🏅 Магазин Титулов")
async def shop_titles_handler(message: types.Message):
    user_id = message.from_user.id
    data = get_user_data(user_id)
    if not data or data["is_banned"] == 1: return
    track_action(user_id)
    
    text = f"🏅 **МАГАЗИН УНИКАЛЬНЫХ ТИТУЛОВ**\n\n💰 Твой баланс: **{data['rice']} 🍙**\n\n"
    buttons = []
    for price, title_name in TITLES_CONFIG.items():
        text += f"▪️ {title_name} — *{price} 🍙*\n"
        if data["current_title"] != title_name:
            buttons.append([types.InlineKeyboardButton(text=f"Купить: {title_name}", callback_data=f"buy_title_{price}")])
            
    kb = types.InlineKeyboardMarkup(inline_keyboard=buttons) if buttons else None
    await message.answer(text, parse_mode="Markdown", reply_markup=kb)

@dp.callback_query(F.data.startswith("buy_title_"))
async def buy_title_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    price = int(callback.data.split("buy_title_")[-1])
    data = get_user_data(user_id)
    if not data or data["is_banned"] == 1: return
    title_name = TITLES_CONFIG[price]
    
    if data["rice"] < price:
        await callback.answer(f"❌ Недостаточно 🍙! Нужно {price}", show_alert=True)
        return
        
    update_field(user_id, "users", "rice", data["rice"] - price)
    update_field(user_id, "users", "current_title", title_name)
    track_action(user_id)
    await callback.answer(f"🎉 Поздравляем! Твой новый титул: {title_name}", show_alert=True)

@dp.message(lambda msg: msg.text == "🏆 Топ Империи")
async def top_players_handler(message: types.Message):
    user_id = message.from_user.id
    data = get_user_data(user_id)
    if not data or data["is_banned"] == 1: return
    track_action(user_id)
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT nickname, rice FROM users WHERE is_banned = 0 ORDER BY rice DESC LIMIT 5")
    top_list = cursor.fetchall()
    conn.close()
    
    text = "🏆 **ТОП-5 БОГАЧЕЙ РИСОВОЙ ИМПЕРИИ**\n━━━━━━━━━━━━━━━━━━━━\n"
    emojis = ["🥇", "🥈", "🥉", "🏅", "🏅"]
    
    for i, player in enumerate(top_list):
        text += f"{emojis[i]} {i+1}. **{player[0]}** — {player[1]} 🍙\n"
    text += "━━━━━━━━━━━━━━━━━━━━\n🌾 _Заводы работают каждую секунду!_"
    
    await message.answer(text, parse_mode="Markdown")
# ==========================================
# ИГРОВОЙ ЦЕНТР И ОДИНОЧНЫЕ ИГРЫ (ИСПРАВЛЕНО)
# ==========================================
@dp.message(lambda msg: msg.text == "🎮 Игровой Центр")
async def games_menu_handler(message: types.Message):
    user_id = message.from_user.id
    data = get_user_data(user_id)
    if not data or data["is_banned"] == 1: return
    track_action(user_id)
    
    text = (
        "🎮 **ИГРОВОЙ ЦЕНТР РИСОВОЙ ИМПЕРИИ**\n\n"
        "🎪 _Здесь ты можете играть один или соревноваться в чате!_\n\n"
        "📖 **ИНСТРУКЦИЯ К БАЗОВЫМ ИГРАМ (Пиши в чат):**\n"
        "🎰 `/casino [ставка]` — Автомат 50/50\n"
        "👉 _Пример:_ `/casino 100`\n"
        "🎲 `/dice [ставка] [число 1-6]` — Угадай кость (Приз х5!)\n"
        "👉 _Пример:_ `/dice 200 4`\n"
        "📊 `/trade [ставка] [вверх/вниз]` — Биржа курса риса\n"
        "👉 _Пример:_ `/trade 150 вверх`\n\n"
        "⚔️ `/duel [ставка]` — Дуэль! *(Ответь этой командой на сообщение друга в чате)*\n\n"
        "⬇️ **ОДИНОЧНЫЕ СУПЕР-КВЕСТЫ (Жми на кнопки ниже):**"
    )
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🕵️‍♂️ Детектив Улик", callback_data="play_detective"), types.InlineKeyboardButton(text="🥠 Печенье Удачи", callback_data="play_cookie")],
        [types.InlineKeyboardButton(text="👨‍🍳 Рисовая Кухня", callback_data="play_kitchen"), types.InlineKeyboardButton(text="🗺 Экспедиция в Пещеры", callback_data="play_cave")],
        [types.InlineKeyboardButton(text="🎡 Крутить Рулетку", callback_data="play_roulette_wheel")]
    ])
    await message.answer(text, parse_mode="Markdown", reply_markup=kb)

# --- 1. ОДИНОЧНАЯ ИГРА: ДЕТЕКТИВ УЛИК ---
DETECTIVE_WORDS = ["РИС", "СУШИ", "УРОЖАЙ", "ПЛАНТАЦИЯ", "ЗАВОД", "СИНДИКАТ", "КОРПОРАЦИЯ", "ТИТУЛ"]

@dp.callback_query(F.data == "play_detective")
async def start_detective_callback(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    data = get_user_data(user_id)
    if not data or data["is_banned"] == 1: return
    
    word = random.choice(DETECTIVE_WORDS)
    mixed = list(word)
    while mixed == list(word):
        random.shuffle(mixed)
    mixed_word = "".join(mixed)
    
    await state.set_state(GameStates.waiting_for_detective)
    await state.update_data(correct_word=word)
    track_action(user_id)
    
    await callback.message.edit_text(
        f"🕵️‍♂️ **ДЕТЕКТИВ: РАССЛЕДОВАНИЕ УЛИК**\n\n"
        f"Преступники зашифровали секретное слово Империи!\n"
        f"Угадай оригинальное слово из этих букв: **{mixed_word}**\n\n"
        f"✏️ _Отправь разгаданное слово простым сообщением в ответ:_ ",
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.message(GameStates.waiting_for_detective)
async def process_detective_answer(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    data = get_user_data(user_id)
    if not data or data["is_banned"] == 1: return
    
    state_data = await state.get_data()
    correct = state_data.get("correct_word")
    user_answer = message.text.strip().upper()
    await state.clear()
    
    now = int(time.time())
    is_elite_vip = (data["vip_until"] > now) and (data["vip_days_bought"] in)
    
    if user_answer == correct:
        r_rice = random.randint(300, 800)
        r_xp = random.randint(5, 15)
        
        if is_elite_vip:
            r_rice = int(r_rice * 1.3)
            r_xp = int(r_xp * 1.3)
            vip_text = " 🔥 *(+30% Элитный буст)*"
        else:
            vip_text = ""
            
        update_field(user_id, "users", "rice", data["rice"] + r_rice)
        xp_msg = add_xp(user_id, r_xp)
        
        await message.answer(f"🎉 **БЕЗУПРЕЧНО, ДЕТЕКТИВ!**\nУлика расшифрована, это было слово **{correct}**.\n\n💰 Награда: **+{r_rice} 🍙**{vip_text}\n{xp_msg}", parse_mode="Markdown")
    else:
        await message.answer(f"😢 **ОШИБКА!** Преступники запутали следы. На самом деле это было слово **{correct}**. Попробуй в следующий раз!", parse_mode="Markdown")

# --- 2. ОДИНОЧНАЯ ИГРА: ПЕЧЕНЬЕ УДАЧИ ---
COOKIE_PREDICTIONS = [
    {"text": "Свиток Дракона 🐉: Сегодня звезды благоволят твоим рисовым полям!", "type": "rice"},
    {"text": "Свиток Черепахи 🐢: Тише едешь — дальше будешь. Твой опыт растет!", "type": "xp"},
    {"text": "Свиток Пустоты 💨: Твои мысли чисты, но карманы пока пустые.", "type": "lose"},
    {"text": "Свиток Феникса 🔥: Из пепла возродится великий урожай!", "type": "rice"},
    {"text": "Свиток Бамбука 🎋: Твоя empire растет крепкой и гибкой.", "type": "xp"}
]

@dp.callback_query(F.data == "play_cookie")
async def play_cookie_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    data = get_user_data(user_id)
    if not data or data["is_banned"] == 1: return
    
    cost = 200
    if data["rice"] < cost:
        await callback.answer("❌ Печенье Удачи стоит 200 🍙!", show_alert=True)
        return
        
    update_field(user_id, "users", "rice", data["rice"] - cost)
    track_action(user_id)
    
    pred = random.choice(COOKIE_PREDICTIONS)
    now = int(time.time())
    is_elite_vip = (data["vip_until"] > now) and (data["vip_days_bought"] in)
    
    msg_bonus = ""
    if pred["type"] == "rice":
        amount = random.randint(400, 1200)
        if is_elite_vip: amount = int(amount * 1.3)
        update_field(user_id, "users", "rice", get_user_data(user_id)["rice"] + amount)
        msg_bonus = f"\n\n💰 Найдено внутри: **+{amount} 🍙**!"
        if is_elite_vip: msg_bonus += " 🔥 *(x1.3 буст)*"
    elif pred["type"] == "xp":
        amount = random.randint(10, 25)
        if is_elite_vip: amount = int(amount * 1.3)
        xp_msg = add_xp(user_id, amount)
        msg_bonus = f"\n\n⚡ Найдено внутри: {xp_msg}"
        if is_elite_vip: msg_bonus += " 🔥 *(x1.3 буст)*"
        
    await callback.message.edit_text(
        f"🥠 **ПЕЧЕНЬЕ УДАЧИ**\n━━━━━━━━━━━━━━━━━━━━\n"
        f"Ты разламываешь хрустящее рисовое печенье... Внутри спрятан тайный свиток мудреца:\n\n"
        f"💬 *«{pred['text']}»*{msg_bonus}",
        parse_mode="Markdown"
    )
    await callback.answer()
# # ==========================================
# ОДИНОЧНЫЕ ИГРЫ: КУХНЯ И ЭКСПЕДИЦИЯ (ИСПРАВЛЕНО)
# ==========================================

# --- 3. ОДИНОЧНАЯ ИГРА: РИСОВАЯ КУХНЯ ---
@dp.callback_query(F.data == "play_kitchen")
async def start_kitchen_callback(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    data = get_user_data(user_id)
    if not data or data["is_banned"] == 1: return
    
    guest_target = random.choice(["🐟 ЛОСОСЬ", "🦀 КРАБ", "🥑 АВОКАДО"])
    await state.set_state(GameStates.cooking_step)
    await state.update_data(step=1, target=guest_target)
    track_action(user_id)
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🚰 Промыть рис 3 раза", callback_data="cook_action_wash")],
        [types.InlineKeyboardButton(text="🔥 Сразу бросить варить", callback_data="cook_action_nowash")]
    ])
    
    await callback.message.edit_text(
        f"👨‍🍳 **РИСОВАЯ КУХНЯ: КРАФТ СУШИ**\n\n"
        f"На кухню заглянул важный гость! Он заказал премиум-суши с начинкой: **{guest_target}**.\n\n"
        f"**Шаг 1: Подготовка сырья.** Рис нужно правильно подготовить. Твоё действие?",
        parse_mode="Markdown", reply_markup=kb
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("cook_action_"), GameStates.cooking_step)
async def process_cooking_steps(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    data = get_user_data(user_id)
    if not data or data["is_banned"] == 1: return
    
    action = callback.data.split("cook_action_")[-1]
    state_data = await state.get_data()
    step = state_data.get("step")
    target = state_data.get("target")
    
    if step == 1:
        if action == "nowash":
            await state.clear()
            await callback.message.edit_text("😢 **БЛЮДО ИСПОРЧЕНО!** Ты не промыл рис, он превратился в липкую серую кашу. Гость ушёл недовольным!", parse_mode="Markdown")
            await callback.answer()
            return
        
        await state.update_data(step=2)
        kb = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="🔴 Сильный огонь", callback_data="cook_action_high"),
             types.InlineKeyboardButton(text="🟡 Средний огонь", callback_data="cook_action_mid")],
            [types.InlineKeyboardButton(text="🟢 Слабый огонь", callback_data="cook_action_low")]
        ])
        await callback.message.edit_text(
            f"👨‍🍳 **РИСОВАЯ КУХНЯ: ШАГ 2**\n\n"
            f"Отлично, рис идеально промыт и засыпан в чашу!\n\n"
            f"**Шаг 2: Термообработка.** На каком огне начнём варить?",
            parse_mode="Markdown", reply_markup=kb
        )
        await callback.answer()
        return

    elif step == 2:
        if action in ["high", "low"]:
            await state.clear()
            reason = "сгорел до углей" if action == "high" else "остался сырым и жёстким"
            await callback.message.edit_text(f"😢 **БЛЮДО ИСПОРЧЕНО!** Рис {reason}. Гость отказался это есть!", parse_mode="Markdown")
            await callback.answer()
            return
            
        await state.update_data(step=3)
        kb = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="🐟 Добавить Лосось", callback_data="cook_action_fish"),
             types.InlineKeyboardButton(text="🦀 Добавить Краба", callback_data="cook_action_crab")],
            [types.InlineKeyboardButton(text="🥑 Добавить Авокадо", callback_data="cook_action_avo")]
        ])
        await callback.message.edit_text(
            f"👨‍🍳 **РИСОВАЯ КУХНЯ: ШАГ 3**\n\n"
            f"Идеально! Рис получился рассыпчатым и ароматным.\n\n"
            f"**Шаг 3: Сборка.** Вспомни, какую начинку просил гость? Нам нужен: **{target}**.",
            parse_mode="Markdown", reply_markup=kb
        )
        await callback.answer()
        return

    elif step == 3:
        await state.clear()
        success = False
        if action == "fish" and "ЛОСОСЬ" in target: success = True
        elif action == "crab" and "КРАБ" in target: success = True
        elif action == "avo" and "АВОКАДО" in target: success = True
        
        if not success:
            await callback.message.edit_text(f"😢 **БЛЮДО ИСПОРЧЕНО!** Ты перепутал ингредиенты и положил не то! Гость устроил скандал.", parse_mode="Markdown")
            await callback.answer()
            return
            
        now = int(time.time())
        is_elite_vip = (data["vip_until"] > now) and (data["vip_days_bought"] in (20, 30))
        
        r_rice = 1500
        r_xp = 40
        vip_text = ""
        
        if is_elite_vip:
            r_rice = int(r_rice * 1.3)
            r_xp = int(r_xp * 1.3)
            vip_text = " 🔥 *(+30% Элитный буст)*"
            
        update_field(user_id, "users", "rice", data["rice"] + r_rice)
        xp_msg = add_xp(user_id, r_xp)
        track_action(user_id)
        
        await callback.message.edit_text(
            f"👨‍🍳 **ШЕФ-ПОВАР ИМПЕРИИ!**\n\n"
            f"Гость в абсолютном восторге! Твои суши признаны кулинарным шедевром.\n\n"
            f"💰 Чаевые: **+{r_rice} 🍙**{vip_text}\n"
            f"{xp_msg}", parse_mode="Markdown"
        )
        await callback.answer()

# --- 4. ОДИНОЧНАЯ ИГРА: ЭКСПЕДИЦИЯ В ПЕЩЕРЫ ---
@dp.callback_query(F.data == "play_cave")
async def start_cave_callback(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    data = get_user_data(user_id)
    if not data or data["is_banned"] == 1: return
    
    await state.set_state(GameStates.cave_step)
    await state.update_data(c_step=1)
    track_action(user_id)
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="⬅️ Налево в сырой туннель", callback_data="cave_move_left")],
        [types.InlineKeyboardButton(text="➡️ Направо к эху", callback_data="cave_move_right")]
    ])
    await callback.message.edit_text(
        f"🗺 **ЭКСПЕДИЦИЯ: ТАЙНЫЕ ПЕЩЕРЫ**\n\n"
        f"Ты снарядил команду фермеров и спустился в древние шахты под плантациями.\n"
        f"Перед вами глухая развилка и пугающая темнота.\n\n"
        f"**Куда направим команду?**", parse_mode="Markdown", reply_markup=kb
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("cave_move_"), GameStates.cave_step)
async def process_cave_steps(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    data = get_user_data(user_id)
    if not data or data["is_banned"] == 1: return
    
    direction = callback.data.split("cave_move_")[-1]
    state_data = await state.get_data()
    c_step = state_data.get("c_step")
    
    if c_step == 1:
        await state.update_data(c_step=2)
        kb = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="🕳 Проползти снизу", callback_data="cave_move_crawl")],
            [types.InlineKeyboardButton(text="⛏ Пробить стену киркой", callback_data="cave_move_mine")]
        ])
        await callback.message.edit_text(
            f"🗺 **ЭКСПЕДИЦИЯ: ТАЙНЫЕ ПЕЩЕРЫ (ШАГ 2)**\n\n"
            f"Команда прошла глубже! Путь преградил огромный завал из древних камней.\n\n"
            f"**Как преодолеем препятствие?**", parse_mode="Markdown", reply_markup=kb
        )
        await callback.answer()
        return
        
    elif c_step == 2:
        await state.clear()
        now = int(time.time())
        is_elite_vip = (data["vip_until"] > now) and (data["vip_days_bought"] in (20, 30))
        
        if random.random() < 0.20:
            straf = 150
            if data["rice"] < straf: straf = data["rice"]
            update_field(user_id, "users", "rice", data["rice"] - straf)
            await callback.message.edit_text(f"💥 **ОБВАЛ ПЕЩЕРЫ!** Свод шахты задрожал, и камни засыпали проход. Команде пришлось бросить снаряжение и спасаться бегством! Потери: **-{straf} 🍙**.", parse_mode="Markdown")
            return
            
        r_rice = 1000
        r_xp = 25
        vip_text = ""
        
        if is_elite_vip:
            r_rice = int(r_rice * 1.3)
            r_xp = int(r_xp * 1.3)
            vip_text = " 🔥 *(x1.3 Элитный бонус)*"
            
        update_field(user_id, "users", "rice", data["rice"] + r_rice)
        xp_msg = add_xp(user_id, r_xp)
        track_action(user_id)
        
        await callback.message.edit_text(
            f"🗺 **ЦЕННАЯ НАХОДКА В ПЕЩЕРЕ!**\n\n"
            f"Разобрав завалы, твои рабочие наткнулись на окаменелый золотой ларец.\n"
            f"Внутри лежал легендарный **Древний Янтарный Рис**!\n\n"
            f"💰 Обменено в банке: **+{r_rice} 🍙**{vip_text}\n"
            f"{xp_msg}", parse_mode="Markdown"
        )
        await callback.answer()
# ==========================================
# ОДИНОЧНАЯ ИГРА: РИСОВАЯ КУХНЯ (ЧАСТЬ 9.1)
# ==========================================
@dp.callback_query(F.data == "play_kitchen")
async def start_kitchen_callback(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    data = get_user_data(user_id)
    if not data or data["is_banned"] == 1: return
    
    guest_target = random.choice(["🐟 ЛОСОСЬ", "🦀 КРАБ", "🥑 АВОКАДО"])
    await state.set_state(GameStates.cooking_step)
    await state.update_data(step=1, target=guest_target)
    track_action(user_id)
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🚰 Промыть рис 3 раза", callback_data="cook_action_wash")],
        [types.InlineKeyboardButton(text="🔥 Сразу бросить варить", callback_data="cook_action_nowash")]
    ])
    
    await callback.message.edit_text(
        f"👨‍🍳 **РИСОВАЯ КУХНЯ: КРАФТ СУШИ**\n\n"
        f"На кухню заглянул важный гость! Он заказал премиум-суши с начинкой: **{guest_target}**.\n\n"
        f"**Шаг 1: Подготовка сырья.** Рис нужно правильно подготовить. Твоё действие?",
        parse_mode="Markdown", reply_markup=kb
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("cook_action_"), GameStates.cooking_step)
async def process_cooking_steps(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    data = get_user_data(user_id)
    if not data or data["is_banned"] == 1: return
    
    action = callback.data.split("cook_action_")[-1]
    state_data = await state.get_data()
    step = state_data.get("step")
    target = state_data.get("target")
    
    if step == 1:
        if action == "nowash":
            await state.clear()
            await callback.message.edit_text("😢 **БЛЮДО ИСПОРЧЕНО!** Ты не промыл рис, он превратился в липкую серую кашу. Гость ушёл недовольным!", parse_mode="Markdown")
            await callback.answer()
            return
        
        await state.update_data(step=2)
        kb = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="🔴 Сильный огонь", callback_data="cook_action_high"),
             types.InlineKeyboardButton(text="🟡 Средний огонь", callback_data="cook_action_mid")],
            [types.InlineKeyboardButton(text="🟢 Слабый огонь", callback_data="cook_action_low")]
        ])
        await callback.message.edit_text(
            f"👨‍🍳 **РИСОВАЯ КУХНЯ: ШАГ 2**\n\n"
            f"Отлично, rice идеально промыт и засыпан в чашу!\n\n"
            f"**Шаг 2: Термообработка.** На каком огне начнём варить?",
            parse_mode="Markdown", reply_markup=kb
        )
        await callback.answer()
        return

    elif step == 2:
        if action in ["high", "low"]:
            await state.clear()
            reason = "сгорел до углей" if action == "high" else "остался сырым и жёстким"
            await callback.message.edit_text(f"😢 **БЛЮДО ИСПОРЧЕНО!** Рис {reason}. Гость отказался это есть!", parse_mode="Markdown")
            await callback.answer()
            return
            
        await state.update_data(step=3)
        kb = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="🐟 Добавить Лосось", callback_data="cook_action_fish"),
             types.InlineKeyboardButton(text="🦀 Добавить Краба", callback_data="cook_action_crab")],
            [types.InlineKeyboardButton(text="🥑 Добавить Авокадо", callback_data="cook_action_avo")]
        ])
        await callback.message.edit_text(
            f"👨‍🍳 **РИСОВАЯ КУХНЯ: ШАГ 3**\n\n"
            f"Идеально! Рис получился рассыпчатым и ароматным.\n\n"
            f"**Шаг 3: Сборка.** Вспомни, какую начинку просил гость? Нам нужен: **{target}**.",
            parse_mode="Markdown", reply_markup=kb
        )
        await callback.answer()
        return

    elif step == 3:
        await state.clear()
        success = False
        if action == "fish" and "ЛОСОСЬ" in target: success = True
        elif action == "crab" and "КРАБ" in target: success = True
        elif action == "avo" and "АВОКАДО" in target: success = True
        
        if not success:
            await callback.message.edit_text(f"😢 **БЛЮДО ИСПОРЧЕНО!** Ты перепутал ингредиенты и положил не то! Гость устроил скандал.", parse_mode="Markdown")
            await callback.answer()
            return
            
        now = int(time.time())
        is_elite_vip = (data["vip_until"] > now) and (data["vip_days_bought"] in)
        
        r_rice = 1500
        r_xp = 40
        vip_text = ""
        
        if is_elite_vip:
            r_rice = int(r_rice * 1.3)
            r_xp = int(r_xp * 1.3)
            vip_text = " 🔥 *(+30% Элитный буст)*"
            
        update_field(user_id, "users", "rice", data["rice"] + r_rice)
        xp_msg = add_xp(user_id, r_xp)
        track_action(user_id)
        
        await callback.message.edit_text(
            f"👨‍🍳 **ШЕФ-ПОВАР ИМПЕРИИ!**\n\n"
            f"Гость в абсолютном восторге! Твои суши признаны кулинарным шедевром.\n\n"
            f"💰 Чаевые: **+{r_rice} 🍙**{vip_text}\n"
            f"{xp_msg}", parse_mode="Markdown"
        )
        await callback.answer()
# ==========================================
# ОДИНОЧНАЯ ИГРА: ЭКСПЕДИЦИЯ И КОЛЕСО (ЧАСТЬ 9.2)
# ==========================================
@dp.callback_query(F.data == "play_cave")
async def start_cave_callback(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    data = get_user_data(user_id)
    if not data or data["is_banned"] == 1: return
    
    await state.set_state(GameStates.cave_step)
    await state.update_data(c_step=1)
    track_action(user_id)
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="⬅️ Налево в сырой туннель", callback_data="cave_move_left")],
        [types.InlineKeyboardButton(text="➡️ Направо к эху", callback_data="cave_move_right")]
    ])
    await callback.message.edit_text(
        f"🗺 **ЭКСПЕДИЦИЯ: ТАЙНЫЕ ПЕЩЕРЫ**\n\n"
        f"Ты снарядил команду фермеров и спустился в древние шахты под плантациями.\n"
        f"Перед вами глухая развилка и пугающая темнота.\n\n"
        f"**Куда направим команду?**", parse_mode="Markdown", reply_markup=kb
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("cave_move_"), GameStates.cave_step)
async def process_cave_steps(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    data = get_user_data(user_id)
    if not data or data["is_banned"] == 1: return
    
    direction = callback.data.split("cave_move_")[-1]
    state_data = await state.get_data()
    c_step = state_data.get("c_step")
    
    if c_step == 1:
        await state.update_data(c_step=2)
        kb = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="🕳 Проползти снизу", callback_data="cave_move_crawl")],
            [types.InlineKeyboardButton(text="⛏ Пробить стену киркой", callback_data="cave_move_mine")]
        ])
        await callback.message.edit_text(
            f"🗺 **ЭКСПЕДИЦИЯ: ТАЙНЫЕ ПЕЩЕРЫ (ШАГ 2)**\n\n"
            f"Команда прошла глубже! Путь преградил огромный завал из древних камней.\n\n"
            f"**Как преодолеем препятствие?**", parse_mode="Markdown", reply_markup=kb
        )
        await callback.answer()
        return
        
    elif c_step == 2:
        await state.clear()
        now = int(time.time())
        is_elite_vip = (data["vip_until"] > now) and (data["vip_days_bought"] in)
        
        if random.random() < 0.20:
            straf = 150
            if data["rice"] < straf: straf = data["rice"]
            update_field(user_id, "users", "rice", data["rice"] - straf)
            await callback.message.edit_text(f"💥 **ОБВАЛ ПЕЩЕРЫ!** Свод шахты задрожал, и камни засыпали проход. Команде пришлось бросить снаряжение и спасаться бегством! Потери: **-{straf} 🍙**.", parse_mode="Markdown")
            return
            
        r_rice = 1000
        r_xp = 25
        vip_text = ""
        
        if is_elite_vip:
            r_rice = int(r_rice * 1.3)
            r_xp = int(r_xp * 1.3)
            vip_text = " 🔥 *(x1.3 Элитный бонус)*"
            
        update_field(user_id, "users", "rice", data["rice"] + r_rice)
        xp_msg = add_xp(user_id, r_xp)
        track_action(user_id)
        
        await callback.message.edit_text(
            f"🗺 **ЦЕННАЯ НАХОДКА В ПЕЩЕРЕ!**\n\n"
            f"Разобрав завалы, твои рабочие наткнулись на окаменелый золотой ларец.\n"
            f"Внутри лежал легендарный **Древний Янтарный Рис**!\n\n"
            f"💰 Обменено в банке: **+{r_rice} 🍙**{vip_text}\n"
            f"{xp_msg}", parse_mode="Markdown"
        )
        await callback.answer()

@dp.callback_query(F.data == "play_roulette_wheel")
async def roulette_wheel_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    data = get_user_data(user_id)
    if not data or data["is_banned"] == 1: return
    
    now = int(time.time())
    is_vip = data["vip_until"] > now
    price = 0 if is_vip else 500
    
    if not is_vip and data["rice"] < price:
        await callback.answer("❌ Колесо Удачи стоит 500 🍙! У тебя не хватает средств.", show_alert=True)
        return
        
    if not is_vip:
        update_field(user_id, "users", "rice", data["rice"] - price)
    track_action(user_id)
    
    win_type = random.choice(["rice", "xp", "lose"])
    if win_type == "rice":
        amount = random.randint(100, 2500)
        update_field(user_id, "users", "rice", get_user_data(user_id)["rice"] + amount)
        msg = f"🎉 **УДАЧА!** Стрелка указала на мешок зерна! Награда: **+{amount} 🍙**"
    elif win_type == "xp":
        amount = random.randint(20, 60)
        xp_msg = add_xp(user_id, amount)
        msg = f"⚡ **ОПЫТ!** Колесо начислило тебе очки активности! {xp_msg}"
    else:
        msg = "😢 **НЕ ПЕЧАЛЬСЯ!** Стрелка остановилась на пустом секторе. Попробуй еще раз!"
        
    await callback.message.edit_text(f"🎡 **КОЛЕСО УДАЧИ**\n\n{msg}", parse_mode="Markdown")
    await callback.answer()
# ==========================================
# ЧАТ-КОМАНДЫ ДЛЯ ИГРОКОВ (ЧАСТЬ 9.3)
# ==========================================
@dp.message(Command("casino"))
async def cmd_casino(message: types.Message):
    user_id = message.from_user.id
    data = get_user_data(user_id)
    if not data or data["is_banned"] == 1: return
    
    args = message.text.split()
    if len(args) < 2 or not args[1].isdigit():
        await message.answer("🎰 **Ошибка!** Напиши: `/casino [ставка]`\n💡 _Пример:_ `/casino 100`", parse_mode="Markdown")
        return
        
    bet = int(args[1])
    if bet <= 0 or data["rice"] < bet:
        await message.answer("❌ Неверная сумма ставки или у тебя нет столько 🍙!")
        return
        
    track_action(user_id)
    now = int(time.time())
    
    win_chance = 0.65 if data["clover_until"] > now else 0.45
    
    if random.random() < win_chance:
        update_field(user_id, "users", "rice", data["rice"] + bet)
        xp_msg = add_xp(user_id, random.randint(2, 6))
        await message.answer(f"🎰 **ПОБЕДА!** Твоя ставка сыграла! Получено **+{bet} 🍙**{xp_msg}", parse_mode="Markdown")
    else:
        if data["insurance_active"] == 1:
            update_field(user_id, "users", "insurance_active", 0)
            await message.answer(f"🎰 **Проигрыш!** Но твой **Императорский Указ** аннулировал потерю! **{bet} 🍙** возвращены на баланс. 🛡", parse_mode="Markdown")
        else:
            update_field(user_id, "users", "rice", data["rice"] - bet)
            await message.answer(f"🎰 **ПРОИГРЫШ!** Автомат забрал твои **{bet} 🍙**. Попробуй отыграться!", parse_mode="Markdown")

@dp.message(Command("dice"))
async def cmd_dice(message: types.Message):
    user_id = message.from_user.id
    data = get_user_data(user_id)
    if not data or data["is_banned"] == 1: return
    
    args = message.text.split()
    if len(args) < 3 or not args[1].isdigit() or not args[2].isdigit():
        await message.answer("🎲 **Ошибка!** Напиши: `/dice [ставка] [число от 1 до 6]`\n💡 _Пример:_ `/dice 200 4`", parse_mode="Markdown")
        return
        
    bet = int(args[1])
    guess = int(args[2])
    
    if bet <= 0 or data["rice"] < bet or guess < 1 or guess > 6:
        await message.answer("❌ Ошибка в ставке или выбранном числе (нужно от 1 до 6)!")
        return
        
    track_action(user_id)
    bot_dice = random.randint(1, 6)
    
    if guess == bot_dice:
        win = bet * 5
        update_field(user_id, "users", "rice", data["rice"] + win)
        xp_msg = add_xp(user_id, random.randint(5, 12))
        await message.answer(f"🎲 **ДЖЕКПОТ!** Выпало число `{bot_dice}`! Ты угадал и получил **+{win} 🍙** (x5 к ставке)!{xp_msg}", parse_mode="Markdown")
    else:
        if data["insurance_active"] == 1:
            update_field(user_id, "users", "insurance_active", 0)
            await message.answer(f"🎲 Выпало число `{bot_dice}`. Ставка возвращена по страховке Указа! 🛡", parse_mode="Markdown")
        else:
            update_field(user_id, "users", "rice", data["rice"] - bet)
            await message.answer(f"🎲 **МИМО!** Выпало число `{bot_dice}`, а ты ставил на `{guess}`. Ставка **{bet} 🍙** потеряна.", parse_mode="Markdown")

@dp.message(Command("trade"))
async def cmd_trade(message: types.Message):
    user_id = message.from_user.id
    data = get_user_data(user_id)
    if not data or data["is_banned"] == 1: return
    
    args = message.text.split()
    if len(args) < 3 or not args[1].isdigit() or args[2].lower() not in ["вверх", "вниз"]:
        await message.answer("📊 **Ошибка!** Напиши: `/trade [ставка] [вверх / вниз]`\n💡 _Пример:_ `/trade 150 вверх`", parse_mode="Markdown")
        return
        
    bet = int(args[1])
    direction = args[2].lower()
    
    if bet <= 0 or data["rice"] < bet:
        await message.answer("❌ Проблема со ставкой или у тебя нет столько 🍙!")
        return
        
    track_action(user_id)
    now = int(time.time())
    win_chance = 0.65 if data["clover_until"] > now else 0.45
    
    market = direction if random.random() < win_chance else ("вниз" if direction == "вверх" else "вверх")
    
    if direction == market:
        update_field(user_id, "users", "rice", data["rice"] + bet)
        xp_msg = add_xp(user_id, random.randint(3, 8))
        await message.answer(f"📈 **БИРЖА РИСА:** Курс пошел **{market}**! Прогноз верный: **+{bet} 🍙**{xp_msg}", parse_mode="Markdown")
    else:
        if data["insurance_active"] == 1:
            update_field(user_id, "users", "insurance_active", 0)
            await message.answer(f"📉 Курс пошел {market}. Потери застрахованы по Императорским Указу! Баланс сохранен. 🛡", parse_mode="Markdown")
        else:
            update_field(user_id, "users", "rice", data["rice"] - bet)
            await message.answer(f"📉 **БИРЖА РИСА:** Курс пошел **{market}**. Твоя сделка в **-{bet} 🍙** закрылась в убыток.", parse_mode="Markdown")

@dp.message(Command("work"))
async def cmd_work(message: types.Message):
    user_id = message.from_user.id
    data = get_user_data(user_id)
    if not data or data["is_banned"] == 1: return
    
    now = int(time.time())
    if now - data["last_work"] < 7200:
        rem = 7200 - (now - data["last_work"])
        await message.answer(f"⏳ Твоя спина ещё болит! Плантации закрыты. Отдыхать осталось: **{rem // 60} мин.**")
        return
        
    earned = random.randint(50, 150)
    xp_earned = random.randint(3, 8)
    
    update_field(user_id, "users", "rice", data["rice"] + earned)
    update_field(user_id, "users", "last_work", now)
    xp_msg = add_xp(user_id, xp_earned)
    track_action(user_id)
    
    texts = [
        f"🌾 Ты по колено в грязи аккуратно полол грядки... Заработано: **+{earned} 🍙**!{xp_msg}",
        f"🚜 Ты весь день чинил сломанный трактор хозяина: **+{earned} 🍙**!{xp_msg}",
        f"🧺 Ты вручную упаковывал мешки риса на склад: **+{earned} 🍙**!{xp_msg}"
    ]
    await message.answer(random.choice(texts), parse_mode="Markdown")
# ==========================================
# ЧАТ-КОМАНДЫ: ОГРАБЛЕНИЯ И ДУЭЛИ (ЧАСТЬ 9.4)
# ==========================================
@dp.message(Command("rob"))
async def cmd_rob(message: types.Message):
    user_id = message.from_user.id
    data = get_user_data(user_id)
    if not data or data["is_banned"] == 1: return
    
    args = message.text.split()
    if len(args) < 2 or not args[1].isdigit():
        await message.answer("🥷 **Ошибка!** Напиши ID игрока цифрами: `/rob [ID]`")
        return
        
    target_id = int(args[1])
    target_data = get_user_data(target_id)
    
    if not target_data or target_id == user_id or target_data["is_banned"] == 1:
        await message.answer("❌ Такой живой игрок не найден в базах данных Империи!")
        return
        
    now = int(time.time())
    if now - data["last_rob"] < 14400:
        await message.answer("❌ Полиция все еще следит за тобой. Снизь криминальную активность на пару часов!")
        return
        
    track_action(user_id)
    
    if target_data["amulet"] > 0:
        update_field(target_id, "inventory", "amulet", target_data["amulet"] - 1)
        straf = int(data["rice"] * 0.15) if data["rice"] > 0 else 50
        update_field(user_id, "users", "rice", data["rice"] - straf)
        update_field(target_id, "users", "rice", target_data["rice"] + straf)
        update_field(user_id, "users", "last_rob", now)
        await message.answer(f"🛡 **ОХРАНА!** У игрока сработал **Амулет от воров**! Ты пойман с поличным и выплатил штраф жертве: **-{straf} 🍙**.")
        return
        
    rob_chance = 0.70 if data["compass"] > 0 else 0.40
    if data["compass"] > 0:
        update_field(user_id, "inventory", "compass", data["compass"] - 1)
        
    if random.random() < rob_chance:
        stolen = int(target_data["rice"] * random.uniform(0.1, 0.25))
        if stolen <= 0: stolen = 20
        update_field(user_id, "users", "rice", data["rice"] + stolen)
        update_field(target_id, "users", "rice", target_data["rice"] - stolen)
        update_field(user_id, "users", "last_rob", now)
        await message.answer(f"🥷 **УСПЕШНОЕ ОГРАБЛЕНИЕ!** Ты обчистил закрома *{target_data['nickname']}* и унес **+{stolen} 🍙**!", parse_mode="Markdown")
    else:
        if data["insurance_active"] == 1:
            update_field(user_id, "users", "insurance_active", 0)
            update_field(user_id, "users", "last_rob", now)
            await message.answer("🥷 Облава стражи! Твой побег застрахован Императорским Указом, штраф платить не пришлось! 🛡", parse_mode="Markdown")
        else:
            straf = random.randint(100, 500)
            if data["rice"] < straf: straf = data["rice"]
            update_field(user_id, "users", "rice", data["rice"] - straf)
            update_field(user_id, "users", "last_rob", now)
            await message.answer(f"🥷 **ОБЛАВА!** Стражники поймали тебя у забора. Пришлось заплатить крупный штраф: **-{straf} 🍙**.")

@dp.message(Command("duel"))
async def cmd_duel(message: types.Message):
    user_id = message.from_user.id
    data = get_user_data(user_id)
    if not data or data["is_banned"] == 1: return
    
    if not message.reply_to_message:
        await message.answer("⚔️ **Вызови друга на бой!** Ответь (сделай reply) на сообщение игрока в чате и напиши: `/duel [ставка]`", parse_mode="Markdown")
        return
        
    target_id = message.reply_to_message.from_user.id
    target_data = get_user_data(target_id)
    
    if not target_data or target_id == user_id or target_data["is_banned"] == 1:
        await message.answer("❌ Ты не можешь вызвать на дуэль этого пользователя или самого себя!")
        return
        
    args = message.text.split()
    if len(args) < 2 or not args[1].isdigit():
        await message.answer("⚔️ Укажи сумму ставки цифрами! Пример: `/duel 300`", parse_mode="Markdown")
        return
        
    bet = int(args[1])
    if bet <= 0 or data["rice"] < bet or target_data["rice"] < bet:
        await message.answer("❌ Неверная ставка, либо у кого-то из вас не хватает 🍙 на балансе!")
        return
        
    track_action(user_id)
    p1 = data["nickname"]
    p2 = target_data["nickname"]
    
    scenarios = [
        f"⚔️ **РИСОВАЯ ДУЭЛЬ!** {p1} забросал соперника гнилыми суши... Но {p2} ловко увернулся и сокрушил его ударом тяжелого мешка с зерном!",
        f"⚔️ **РИСОВАЯ ДУЭЛЬ!** {p2} поскользнулся на мокром стебле, и {p1} мгновенно обезоружил его точным выпадом рисового меча!"
    ]
    
    await message.answer("⚔️ _Зерновые мечи скрестились, битва началась..._")
    await asyncio.sleep(2)
    
    if random.choice([True, False]):
        update_field(user_id, "users", "rice", data["rice"] + bet)
        update_field(target_id, "users", "rice", target_data["rice"] - bet)
        update_field(user_id, "users", "wins", data["wins"] + 1)
        update_field(target_id, "users", "losses", target_data["losses"] + 1)
        xp_msg = add_xp(user_id, random.randint(10, 20))
        await message.answer(f"{random.choice(scenarios)}\n\n🏆 **Победитель:** {p1}! Твой куш: **+{bet} 🍙**{xp_msg}", parse_mode="Markdown")
    else:
        update_field(user_id, "users", "rice", data["rice"] - bet)
        update_field(target_id, "users", "rice", target_data["rice"] + bet)
        update_field(user_id, "users", "losses", data["losses"] + 1)
        update_field(target_id, "users", "wins", target_data["wins"] + 1)
        xp_msg = add_xp(target_id, random.randint(10, 20))
        await message.answer(f"{random.choice(scenarios)}\n\n🏆 **Победитель:** {p2}! Твой куш: **+{bet} 🍙**{xp_msg}", parse_mode="Markdown")

@dp.message(Command("darts"))
async def cmd_darts(message: types.Message):
    await cmd_duel(message)
# ==========================================
# ИМПЕРСКАЯ АДМИН-ПАНЕЛЬ (ТОЛЬКО ДЛЯ ВЛАДЕЛЬЦА)
# ==========================================
@dp.message(lambda msg: msg.text == "👑 Админ Панель")
@dp.message(Command("admin"))
async def cmd_admin_handler(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return # Полный игнор обычных игроков
        
    track_action(ADMIN_ID)
    admin_text = (
        "👑 **ДОБРО ПОЖАЛОВАТЬ, ХОЗЯЙКА ИМПЕРИИ!**\n━━━━━━━━━━━━━━━━━━━━\n"
        "Твоё нижнее меню успешно изменено на пульт управления базой данных.\n\n"
        "📖 **ИНСТРУКЦИЯ К ТЕКСТОВЫМ КОМАНДАМ АДМИНА:**\n"
        "💰 ` /give_rice [ID] [число] ` — Начислить рис игроку\n"
        "📉 ` /take_rice [ID] [число] ` — Отобрать рис у игрока\n"
        "🎫 ` /give_xp [ID] [число] ` — Выдать опыт Rice Pass\n"
        "📊 ` /take_xp [ID] [число] ` — Снизить опыт Rice Pass\n\n"
        "⬇️ _Для быстрого управления используй клавиатуру ниже:_ "
    )
    await message.answer(admin_text, parse_mode="Markdown", reply_markup=admin_keyboard())

@dp.message(lambda msg: msg.text == "📊 Статистика")
async def admin_stats_handler(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*), SUM(rice), AVG(playtime) FROM users")
    stats = cursor.fetchone()
    cursor.execute("SELECT COUNT(*) FROM users WHERE is_banned = 1")
    banned_count = cursor.fetchone()[0]
    conn.close()
    
    total_users = stats[0] if stats[0] else 0
    total_rice = stats[1] if stats[1] else 0
    avg_playtime = int(stats[2] // 60) if stats[2] else 0
    
    text = (
        f"📊 **ОБЩАЯ СТАТИСТИКА РИСОВОЙ ИМПЕРИИ**\n━━━━━━━━━━━━━━━━━━━━\n"
        f"👥 Всего зарегистрировано: **{total_users} игроков**\n"
        f"💰 Рис в обороте экономики: **{total_rice} 🍙**\n"
        f"⏱ Среднее время активности: **{avg_playtime} мин. на юзера**\n"
        f"🚫 Всего аккаунтов в бане: **{banned_count} шт.**\n━━━━━━━━━━━━━━━━━━━━"
    )
    await message.answer(text, parse_mode="Markdown")

@dp.message(lambda msg: msg.text == "🎁 Выдать Себе")
async def admin_give_self_handler(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    
    data = get_user_data(ADMIN_ID)
    if not data: return
    
    update_field(ADMIN_ID, "users", "rice", data["rice"] + 10000)
    xp_msg = add_xp(ADMIN_ID, 100)
    
    await message.answer(f"👑 **Имперские ресурсы зачислены Хозяйке!**\n\n💰 На баланс: **+10,000 🍙**\n{xp_msg}", parse_mode="Markdown")

@dp.message(Command("give_rice"), Command("take_rice"), Command("give_xp"), Command("take_xp"))
async def admin_modify_resources_cmd(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    
    args = message.text.split()
    if len(args) < 3 or not args[1].isdigit() or not args[2].isdigit():
        await message.answer("❌ **Формат команды:** ` /give_rice [ID] [количество] `", parse_mode="Markdown")
        return
        
    t_id = int(args[1])
    val = int(args[2])
    t_data = get_user_data(t_id)
    
    if not t_data:
        await message.answer("❌ Игрок с таким ID не найден!")
        return
        
    cmd = args[0].replace("/", "")
    if "give_rice" in cmd:
        update_field(t_id, "users", "rice", t_data["rice"] + val)
        await message.answer(f"✅ Успешно выдано **{val} 🍙** игроку *{t_data['nickname']}*!", parse_mode="Markdown")
    elif "take_rice" in cmd:
        new_val = max(0, t_data["rice"] - val)
        update_field(t_id, "users", "rice", new_val)
        await message.answer(f"✅ Успешно изъято **{val} 🍙** у игрока *{t_data['nickname']}*!", parse_mode="Markdown")
    elif "give_xp" in cmd:
        xp_msg = add_xp(t_id, val)
        await message.answer(f"✅ Игроку *{t_data['nickname']}* начислено **{val} XP**! {xp_msg}", parse_mode="Markdown")
    elif "take_xp" in cmd:
        new_val = max(0, t_data["xp"] - val)
        update_field(t_id, "users", "xp", new_val)
        await message.answer(f"✅ У игрока *{t_data['nickname']}* изъято **{val} XP**!", parse_mode="Markdown")

@dp.message(Command("ban"), Command("unban"), lambda msg: msg.text == "🚫 Бан / Разбан")
async def admin_ban_unban_handler(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    
    args = message.text.split()
    if len(args) < 2 or not args[1].isdigit():
        await message.answer("🚫 **Управление банами:** Напиши текстовую команду ` /ban [ID] ` или ` /unban [ID] `", parse_mode="Markdown")
        return
        
    t_id = int(args[1])
    t_data = get_user_data(t_id)
    if not t_data:
        await message.answer("❌ Игрок не найден!")
        return
        
    if "unban" in args[0]:
        update_field(t_id, "users", "is_banned", 0)
        await message.answer(f"🟢 Игрок *{t_data['nickname']}* успешно разблокирован в Империи!", parse_mode="Markdown")
    else:
        update_field(t_id, "users", "is_banned", 1)
        await message.answer(f"🔴 Игрок *{t_data['nickname']}* навсегда забанен и лишен плантаций!", parse_mode="Markdown")

@dp.message(Command("check"), lambda msg: msg.text == "🔍 Чек Профиля")
async def admin_check_profile_handler(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    
    args = message.text.split()
    if len(args) < 2 or not args[1].isdigit():
        await message.answer("🔍 **Просмотр базы:** Напиши команду с ID игрока: ` /check [ID] `", parse_mode="Markdown")
        return
        
    t_id = int(args[1])
    d = get_user_data(t_id)
    if not d:
        await message.answer("❌ Игрок не найден!")
        return
        
    p_hours = d["playtime"] // 3600
    p_minutes = (d["playtime"] % 3600) // 60
    ban_status = "🔴 ЗАБАНЕН" if d["is_banned"] == 1 else "🟢 Активен"
    
    text = (
        f"🔍 **БАЗА ДАННЫХ: КАРТОЧКА ИГРОКА**\n━━━━━━━━━━━━━━━━━━━━\n"
        f"🆔 ID: `{d['user_id']}` | Статус: **{ban_status}**\n"
        f"👤 Никнейм: *{d['nickname']}* | Титул: `{d['current_title']}`\n"
        f"🍙 Баланс: **{d['rice']} 🍙** | Уровень Pass: `{d['level']}/25`\n"
        f"⏱ Плейтайм: {p_hours} ч. {p_minutes} мин. | Действий: {d['total_actions']}\n"
        f"⚔️ Дуэли: 🏆 {d['wins']} побед | 💀 {d['losses']} поражений\n━━━━━━━━━━━━━━━━━━━━"
    )
    await message.answer(text, parse_mode="Markdown")

# ==========================================
# ИСПРАВЛЕНИЕ ОШИБОК И ФИНАЛЬНЫЙ ЗАПУСК БОТА
# ==========================================
@dp.message()
async def block_banned_users_global_handler(message: types.Message):
    data = get_user_data(message.from_user.id)
    if data and data["is_banned"] == 1:
        await message.answer("❌ **Ты заблокирован в Рисовой Империи!**")

async def main():
    init_db()
    print("🚀 Рисовая Империя успешно запущена со всеми играми, плейтаймом и админкой!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
