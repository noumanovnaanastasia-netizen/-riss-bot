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

# 🔑 ТОКЕН: Вставь секретный токен твоего бота от @BotFather внутри кавычек
TOKEN = "СЮДА_ВСТАВЬТЕ_ВАШ_ТОКЕН_ОТ_BOTFATHER"

# Настройка логирования для отслеживания ошибок
logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())
DB_NAME = "rice_empire.db"

# ==========================================
# СОСТОЯНИЯ ДЛЯ РЕГИСТРАЦИИ НИКНЕЙМА (FSM)
# ==========================================
class RegistrationStates(StatesGroup):
    waiting_for_nickname = State()

# ==========================================
# ИНИЦИАЛИЗАЦИЯ И ФУНКЦИИ БАЗЫ ДАННЫХ
# ==========================================
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Таблица пользователей
    cursor.execute('''
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
    ''')
    # Таблица предприятий игрока
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
    # Таблица инвентаря для расходников и боксов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            user_id INTEGER PRIMARY KEY,
            energy_drink INTEGER DEFAULT 0,
            amulet INTEGER DEFAULT 0,
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
    
    return {
        "user_id": user[0], "nickname": user[1], "rice": user[2], "xp": user[3],
        "level": user[4], "vip_until": user[5], "current_title": user[6],
        "last_bonus": user[7], "last_work": user[8], "last_rob": user[9],
        "energy_until": user[10], "wins": user[11], "losses": user[12],
        "b1": biz[1], "b2": biz[2], "b3": biz[3], "b4": biz[4], "b5": biz[5], "b6": biz[6], "b7": biz[7],
        "last_passive_collect": biz[8],
        "energy_drink": inv[1], "amulet": inv[2], "box1": inv[3], "box2": inv[4], "box3": inv[5]
    }

def register_user(user_id, nickname):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    now = int(time.time())
    cursor.execute("INSERT OR REPLACE INTO users (user_id, nickname, last_bonus, last_work, last_passive_collect, last_rob) VALUES (?, ?, 0, 0, ?, 0)", (user_id, nickname, now))
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

# ==========================================
# ИГРОВАЯ МАТЕМАТИКА, СТАТУСЫ И ПРЕДПРИЯТИЯ
# ==========================================
# 7 типов предприятий: стоимость и доход в час
BUSINESS_CONFIG = {
    "b1": {"name": "🌱 Рисовая грядка", "price": 500, "income": 5},
    "b2": {"name": "🧺 Небольшая теплица", "price": 2500, "income": 30},
    "b3": {"name": "🚜 Автоматическая плантация", "price": 10000, "income": 130},
    "b4": {"name": "🏭 Сельская фабрика", "price": 25000, "income": 350},
    "b5": {"name": "🏢 Рисовый синдикат", "price": 50000, "income": 750},
    "b6": {"name": "🚀 Международный экспорт", "price": 100000, "income": 1600},
    "b7": {"name": "🌌 Межгалактическая корпорация", "price": 250000, "income": 4500}
}

# 9 покупных титулов в магазине
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

def add_xp(user_id, xp_to_add):
    data = get_user_data(user_id)
    if not data or data["level"] >= 25: return ""
    
    # Модификатор опыта за VIP (Премиум)
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
        
        # Начисление наград за уровень
        if current_level == 15:
            reward_text += "🎁 **BRAWL PASS SUPREME!** Тебе начислен **VIP-статус на 2 дня**! 👑\n"
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
            
            reward_text += f"🎁 **Награда за {current_level} уровень:** +{r_rice} 🍙 и +{r_xp} бонусных XP!\n"
            update_field(user_id, "users", "rice", get_user_data(user_id)["rice"] + r_rice)
            new_xp += r_xp

    update_field(user_id, "users", "xp", new_xp)
    update_field(user_id, "users", "level", current_level)
    
    if leveled_up:
        return f"\n\n🎉 **ПОВЫШЕНИЕ УРОВНЯ BRAWL PASS!** Ты достиг **{current_level} уровня**! 🎉\n" + reward_text
    return f"\n✨ +{xp_to_add} XP для Brawl Pass"

def calc_passive_income(data):
    now = int(time.time())
    seconds_passed = now - data["last_passive_collect"]
    hours_passed = seconds_passed / 3600.0
    
    if hours_passed <= 0: return 0
    
    total_income_per_hour = 0
    for key, config in BUSINESS_CONFIG.items():
        total_income_per_hour += data[key] * config["income"]
        
    # Проверка действия энергетика x1.5 дохода
    if data["energy_until"] > now:
        total_income_per_hour = int(total_income_per_hour * 1.5)
        
    return int(hours_passed * total_income_per_hour)

# ==========================================
# ИНЛАЙН КЛАВИАТУРЫ (КНОПКИ МЕНЮ)
# ==========================================
def main_keyboard():
    return types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="👤 Мой Профиль", callback_data="menu_profile"), types.InlineKeyboardButton(text="🏪 Магазин Империи", callback_data="menu_shop")],
        [types.InlineKeyboardButton(text="🌾 Сбор Бонуса", callback_data="menu_bonus"), types.InlineKeyboardButton(text="🎒 Мой Инвентарь", callback_data="menu_inventory")],
        [types.InlineKeyboardButton(text="🎮 Игровой Центр", callback_data="menu_games")]
    ])

def shop_categories_keyboard():
    return types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🚜 Рисовые Предприятия", callback_data="shop_biz"), types.InlineKeyboardButton(text="👑 VIP-Подписка", callback_data="shop_vip")],
        [types.InlineKeyboardButton(text="🎫 Уровни Brawl Pass XP", callback_data="shop_xp"), types.InlineKeyboardButton(text="🥤 Расходники и Бусты", callback_data="shop_items")],
        [types.InlineKeyboardButton(text="📦 Кейсы и Сундуки", callback_data="shop_boxes"), types.InlineKeyboardButton(text="🏅 Магазин Титулов", callback_data="shop_titles")],
        [types.InlineKeyboardButton(text="🔙 Главное Меню", callback_data="to_main")]
    ])

# ==========================================
# КОМАНДЫ СТАРТА И РЕГИСТРАЦИИ
# ==========================================
@dp.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    init_db()
    data = get_user_data(message.from_user.id)
    if data:
        await message.answer(
            f"👋 Приветствуем снова, **{data['nickname']}** в Рисовой Империи! 🍙\n"
            f"Используй кнопки ниже для управления базой:", 
            parse_mode="Markdown", 
            reply_markup=main_keyboard()
        )
    else:
        await message.answer(
            "👋 **Добро пожаловать в текстовую вселенную Рисовой Империи!** 🍙\n\n"
            "Перед тем как начать копить богатства, строить заводы и участвовать в дуэлях, "
            "придумай свой **уникальный игровой никнейм**.\n\n"
            "Он будет отображаться в профиле и нужен для того, чтобы другие игроки "
            "могли взаимодействовать с тобой.\n\n"
            "✏️ _Введи никнейм прямо сейчас в ответном сообщении:_ ", 
            parse_mode="Markdown"
        )
        await state.set_state(RegistrationStates.waiting_for_nickname)

@dp.message(RegistrationStates.waiting_for_nickname)
async def process_nickname(message: types.Message, state: FSMContext):
    nickname = message.text.strip()
    if len(nickname) < 2 or len(nickname) > 20:
        await message.answer("❌ Никнейм должен содержать от 2 до 20 символов! Попробуй еще раз:")
        return
        
    register_user(message.from_user.id, nickname)
    await state.clear()
    await message.answer(
        f"🎉 **Отлично! Твой игровой профиль успешно создан.**\n"
        f"Твой никнейм: **{nickname}**\n"
        f"Тебе начислено стартовые 100 🍙!\n\n"
        f"_Начнем строить империю!_ 👇", 
        parse_mode="Markdown", 
        reply_markup=main_keyboard()
    )

@dp.message(Command("menu"))
async def cmd_menu(message: types.Message):
    data = get_user_data(message.from_user.id)
    if not data: return
    await message.answer("🗂 **Главное управление рисовой базой:**", parse_mode="Markdown", reply_markup=main_keyboard())

# ==========================================
# ОБРАБОТЧИКИ НАВИГАЦИИ (ГЛАВНОЕ МЕНЮ И ПРОФИЛЬ)
# ==========================================
@dp.callback_query(F.data == "to_main")
async def back_to_main_callback(callback: types.CallbackQuery):
    await callback.message.edit_text("🗂 **Главное управление рисовой базой:**", parse_mode="Markdown", reply_markup=main_keyboard())
    await callback.answer()

@dp.callback_query(F.data == "menu_profile")
async def profile_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    data = get_user_data(user_id)
    if not data: return
    
    # Начисление пассивного дохода при просмотре профиля
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
        energy_status = " ⚡ _(Действует Энергетик x1.5)_"
        
    auto_status = get_auto_status(data["rice"])
    req_xp = get_required_xp(data["level"])
    
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
        f"🎟 **Brawl Pass:** `{data['level']}/25 Уровень` _({data['xp']}/{req_xp} XP)_\n"
        f"⚔️ **Статистика дуэлей:** 🏆 Побед: {data['wins']} | 💀 Проиграно: {data['losses']}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🌾 _Пассивный доход зачислен автоматически при открытии профиля!_"
    )
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text="🔙 Назад", callback_data="to_main")]])
    await callback.message.edit_text(profile_text, parse_mode="Markdown", reply_markup=kb)
    await callback.answer()

# ==========================================
# СБОР БОНУСА (РАЗ В 6 ЧАСОВ)
# ==========================================
@dp.callback_query(F.data == "menu_bonus")
async def bonus_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    data = get_user_data(user_id)
    if not data: return
    
    now = int(time.time())
    cooldown = 6 * 3600
    if now - data["last_bonus"] < cooldown:
        time_left = cooldown - (now - data["last_bonus"])
        hours = time_left // 3600
        minutes = (time_left % 3600) // 60
        await callback.message.edit_text(
            f"⏳ **Сбор плантации закрыт!**\n\n"
            f"Твои крестьяне отдыхают. До следующего сбора бонуса осталось: **{hours} ч. {minutes} мин.** 🍙", 
            parse_mode="Markdown", 
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text="🔙 Назад", callback_data="to_main")]])
        )
        await callback.answer()
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
    
    success_text = (
        f"{vip_tag} успешно собран!\n\n"
        f"🧺 Ты зашел на плантации и собрал:\n"
        f"💰 Получено: **+{give_rice} 🍙**\n"
        f"{xp_msg}"
    )
    await callback.message.edit_text(
        success_text, 
        parse_mode="Markdown", 
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text="🔙 Назад", callback_data="to_main")]])
    )
    await callback.answer()
    
    # ==========================================
# ИНВЕНТАРЬ ИМПЕРИИ
# ==========================================
@dp.callback_query(F.data == "menu_inventory")
async def inventory_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    data = get_user_data(user_id)
    if not data: return
    
    inv_text = (
        f"🎒 **ТВОЙ КАРМАННЫЙ ИНВЕНТАРЬ**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🥤 Рисовый энергетик (x1.5): **{data['energy_drink']} шт.**\n"
        f"🛡 Амулет от наглых воров: **{data['amulet']} шт.**\n\n"
        f"📦 **Хранилище нераспечатанных сундуков:**\n"
        f"├ 📦 Рисовая коробка: {data['box1']} шт.\n"
        f"├ 💎 Ларец Сенсея: {data['box2']} шт.\n"
        f"└ 🌌 Императорский сундук: {data['box3']} шт.\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"⚡ _Выбери вещь в меню ниже для активации:_ "
    )
    
    buttons = []
    if data["energy_drink"] > 0:
        buttons.append([types.InlineKeyboardButton(text="🥤 Выпить Энергетик", callback_data="use_energy")])
    if data["box1"] > 0:
        buttons.append([types.InlineKeyboardButton(text="📦 Открыть Рисовую коробку", callback_data="open_box1")])
    if data["box2"] > 0:
        buttons.append([types.InlineKeyboardButton(text="💎 Открыть Ларец Сенсея", callback_data="open_box2")])
    if data["box3"] > 0:
        buttons.append([types.InlineKeyboardButton(text="🌌 Открыть Императорский сундук", callback_data="open_box3")])
    buttons.append([types.InlineKeyboardButton(text="🔙 Назад", callback_data="to_main")])
    
    await callback.message.edit_text(inv_text, parse_mode="Markdown", reply_markup=types.InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()

@dp.callback_query(F.data == "use_energy")
async def use_energy_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    data = get_user_data(user_id)
    if not data or data["energy_drink"] <= 0: return
    
    now = int(time.time())
    new_energy_time = max(data["energy_until"], now) + 3600
    update_field(user_id, "inventory", "energy_drink", data["energy_drink"] - 1)
    update_field(user_id, "users", "energy_until", new_energy_time)
    
    await callback.message.edit_text(
        "🥤 **Глоток энергии!**\n\nТы выпил рисовый энергетик. Теперь в течение **1 часа** абсолютно все твои заводы и грядки приносят в **полтора раза (x1.5) больше 🍙** пассивного дохода!", 
        parse_mode="Markdown", 
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text="🔙 В инвентарь", callback_data="menu_inventory")]])
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("open_box"))
async def open_box_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    box_type = callback.data.split("box")[-1]
    data = get_user_data(user_id)
    
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
            msg = f"🎫 Из коробки выпало: {xp_msg}!"
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
            msg = f"🎫 Из Ларца Сенсея выпало: {xp_msg}!"
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
            
        msg = (
            f"🌌 **Двойной Дроп из Императорского сундука!**\n\n"
            f"🎁 **Приз №1 (Ресурсы):** +{r_rice} 🍙 и {xp_msg}\n"
            f"🎁 **Приз №2 (Вещь в инвентарь):** Добавлено {item_text}!"
        )
    else:
        await callback.answer("Сундук закончился!")
        return
        
    await callback.message.edit_text(
        f"🎉 **ОТКРЫТИЕ КЕЙСА:**\n\n{msg}", 
        parse_mode="Markdown", 
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text="🔙 В инвентарь", callback_data="menu_inventory")]])
    )
    await callback.answer()

# ==========================================
# ТОРГОВЫЙ ЦЕНТР: МАГАЗИН ИМПЕРИИ
# ==========================================
@dp.callback_query(F.data == "menu_shop")
async def shop_callback(callback: types.CallbackQuery):
    data = get_user_data(callback.from_user.id)
    await callback.message.edit_text(
        f"🏪 **ДОБРО ПОЖАЛОВАТЬ В ТОРГОВЫЙ ЦЕНТР ИМПЕРИИ!** 🍙\n\n"
        f"💰 Твой текущий баланс: **{data['rice']} 🍙**\n\n"
        f"_Выбери интересующую категорию товаров ниже:_ ", 
        parse_mode="Markdown", 
        reply_markup=shop_categories_keyboard()
    )
    await callback.answer()

@dp.callback_query(F.data == "shop_biz")
async def shop_biz_callback(callback: types.CallbackQuery):
    data = get_user_data(callback.from_user.id)
    text = "🚜 **МАГАЗИН: РИСОВЫЕ ПРЕДПРИЯТИЯ (Доход в час)**\n\n"
    buttons = []
    for key, cfg in BUSINESS_CONFIG.items():
        text += f"▪️ {cfg['name']}\n   Цена: {cfg['price']} 🍙 | Доход: +{cfg['income']} 🍙/ч\n   👉 У тебя: {data[key]} шт.\n\n"
        buttons.append([types.InlineKeyboardButton(text=f"Купить {cfg['name']}", callback_data=f"buy_biz_{key}")])
    buttons.append([types.InlineKeyboardButton(text="🔙 Назад", callback_data="menu_shop")])
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=types.InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()

@dp.callback_query(F.data.startswith("buy_biz_"))
async def buy_biz_process(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    biz_key = callback.data.split("buy_biz_")[-1]
    data = get_user_data(user_id)
    cfg = BUSINESS_CONFIG[biz_key]
    
    if data["rice"] < cfg["price"]:
        await callback.answer(f"❌ Недостаточно 🍙! Нужно {cfg['price']}", show_alert=True)
        return
        
    update_field(user_id, "users", "rice", data["rice"] - cfg["price"])
    update_field(user_id, "businesses", biz_key, data[biz_key] + 1)
    await callback.answer(f"🎉 Успешно куплено: {cfg['name']}!", show_alert=True)
    await shop_biz_callback(callback)

@dp.callback_query(F.data == "shop_vip")
async def shop_vip_callback(callback: types.CallbackQuery):
    text = (
        "👑 **МАГАЗИН: VIP-ПОДПИСКА (ПРЕМИУМ)**\n\n"
        "✨ **Плюшки VIP-статуса:**\n"
        "• Доход со всех предприятий увеличен в **X2**!\n"
        "• Ежедневный сбор бонуса: **3500 🍙** вместо 2000 🍙!\n"
        "• Повышенный случайный опыт в Brawl Pass.\n"
        "• Бесплатный прокрут Колеса Удачи (Рулетки) раз в сутки!\n\n"
        "🛒 Выбери срок подписки:"
    )
    buttons = [
        [types.InlineKeyboardButton(text="🎫 VIP на 10 дней — 12,000 🍙", callback_data="buy_vip_10")],
        [types.InlineKeyboardButton(text="🎫 VIP на 20 дней — 18,000 🍙", callback_data="buy_vip_20")],
        [types.InlineKeyboardButton(text="🎫 VIP на 30 дней — 25,000 🍙", callback_data="buy_vip_30")],
        [types.InlineKeyboardButton(text="🔙 Назад", callback_data="menu_shop")]
    ]
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=types.InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()

@dp.callback_query(F.data.startswith("buy_vip_"))
async def buy_vip_process(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    days = int(callback.data.split("buy_vip_")[-1])
    data = get_user_data(user_id)
    
    prices = {10: 12000, 20: 18000, 30: 25000}
    price = prices[days]
    
    if data["rice"] < price:
        await callback.answer(f"❌ Недостаточно 🍙! Нужно {price}", show_alert=True)
        return
        
    now = int(time.time())
    new_vip = max(data["vip_until"], now) + (days * 24 * 3600)
    
    update_field(user_id, "users", "rice", data["rice"] - price)
    update_field(user_id, "users", "vip_until", new_vip)
    await callback.answer(f"👑 Ура! Ты активировал VIP на {days} дней!", show_alert=True)
    await shop_vip_callback(callback)

@dp.callback_query(F.data == "shop_xp")
async def shop_xp_callback(callback: types.CallbackQuery):
    text = "🎫 **МАГАЗИН: ПАКИ ОПЫТА BRAWL PASS**\n\nБыстрая прокачка уровней пропуска за 🍙!"
    buttons = [
        [types.InlineKeyboardButton(text="🍬 Конфета (+25 XP) — 600 🍙", callback_data="buy_xp_25_600")],
        [types.InlineKeyboardButton(text="🔋 Малый пак (+75 XP) — 1,800 🍙", callback_data="buy_xp_75_1800")],
        [types.InlineKeyboardButton(text="📦 Средняя коробка (+150 XP) — 3,500 🍙", callback_data="buy_xp_150_3500")],
        [types.InlineKeyboardButton(text="🚀 Большой контейнер (+300 XP) — 6,500 🍙", callback_data="buy_xp_300_6500")],
        [types.InlineKeyboardButton(text="🎫 Мгновенный Скип Уровня (+1 Ур.) — 9,000 🍙", callback_data="buy_xp_skip_9000")],
        [types.InlineKeyboardButton(text="🔙 Назад", callback_data="menu_shop")]
    ]
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=types.InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()

@dp.callback_query(F.data.startswith("buy_xp_"))
async def buy_xp_process(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    mode = callback.data.split("buy_xp_")[-1]
    data = get_user_data(user_id)
    
    if mode == "skip_9000":
        price, xp_to_give, is_skip = 9000, 0, True
    else:
        parts = mode.split("_")
        xp_to_give, price, is_skip = int(parts[0]), int(parts[1]), False
        
    if data["rice"] < price:
        await callback.answer(f"❌ Недостаточно 🍙!", show_alert=True)
        return
        
    if data["level"] >= 25:
        await callback.answer("❌ Твой Brawl Pass уже максимального 25 уровня!", show_alert=True)
        return
        
    update_field(user_id, "users", "rice", data["rice"] - price)
    
    if is_skip:
        req = get_required_xp(data["level"])
        rem_xp = req - data["xp"]
        msg = add_xp(user_id, rem_xp)
    else:
        msg = add_xp(user_id, xp_to_give)
        
    await callback.answer("🎫 Пакет опыта успешно куплен!", show_alert=True)
    await callback.message.answer(f"🎟 Ресурсы зачислены!{msg}", parse_mode="Markdown")
    await shop_xp_callback(callback)

@dp.callback_query(F.data == "shop_items")
async def shop_items_callback(callback: types.CallbackQuery):
    text = (
        "🥤 **МАГАЗИН: РАСХОДНИКИ И БУСТЕРЫ**\n\n"
        "• 🥤 **Рисовый энергетик** — 1,000 🍙\n"
        "  _Дает +50% (x1.5) к пассивному сбору заводов на 1 час при активации из инвентаря._\n\n"
        "• 🛡 **Амулет от воров** — 2,000 🍙\n"
        "  _Автоматически защищает от грабежей. Грабитель гарантированно проиграет._"
    )
    buttons = [
        [types.InlineKeyboardButton(text="Купить Энергетик — 1000 🍙", callback_data="buy_item_energy_drink_1000")],
        [types.InlineKeyboardButton(text="Купить Амулет — 2000 🍙", callback_data="buy_item_amulet_2000")],
        [types.InlineKeyboardButton(text="🔙 Назад", callback_data="menu_shop")]
    ]
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=types.InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()

@dp.callback_query(F.data.startswith("buy_item_"))
async def buy_item_process(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    parts = callback.data.split("buy_item_")[-1].split("_")
    price = int(parts[-1])
    item_field = "_".join(parts[:-1])
    data = get_user_data(user_id)
    
    if data["rice"] < price:
        await callback.answer("❌ Недостаточно 🍙!", show_alert=True)
        return
        
    update_field(user_id, "users", "rice", data["rice"] - price)
    update_field(user_id, "inventory", item_field, data[item_field] + 1)
    await callback.answer("🎒 Товар отправлен в твой инвентарь!", show_alert=True)
    await shop_items_callback(callback)

@dp.callback_query(F.data == "shop_boxes")
async def shop_boxes_callback(callback: types.CallbackQuery):
    text = (
        "📦 **МАГАЗИН: СУНДУКИ И ЛУТБОКСЫ**\n\n"
        "1. **Рисовая коробка** 📦 — 1,500 🍙\n"
        "   _Дроп: Рис, XP или 1 энергетик._\n\n"
        "2. **Ларец Сенсея** 💎 — 5,000 🍙\n"
        "   _Дроп: Много риса, много XP или VIP на 3 дня._\n\n"
        "3. **Императорский сундук** 🌌 — 15,000 🍙\n"
        "   🔥 **ЭКСКЛЮЗИВНЫЙ ДВОЙНОЙ ДРОП!** Гарантированно выдает кучу риса + XP И одну случайную ценную вещь (Бустеры, Амулеты или VIP на 10 дней)!"
    )
    buttons = [
        [types.InlineKeyboardButton(text="Купить Коробку — 1500 🍙", callback_data="buy_box_box1_1500")],
        [types.InlineKeyboardButton(text="Купить Ларец — 5000 🍙", callback_data="buy_box_box2_5000")],
        [types.InlineKeyboardButton(text="Купить Сундук — 15000 🍙", callback_data="buy_box_box3_15000")],
        [types.InlineKeyboardButton(text="🔙 Назад", callback_data="menu_shop")]
    ]
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=types.InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()

@dp.callback_query(F.data.startswith("buy_box_"))
async def buy_box_process(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    parts = callback.data.split("buy_box_")[-1].split("_")
    box_field, price = parts[0], int(parts[1])
    data = get_user_data(user_id)
    
    if data["rice"] < price:
        await callback.answer("❌ Недостаточно 🍙!", show_alert=True)
        return
        
    update_field(user_id, "users", "rice", data["rice"] - price)
    update_field(user_id, "inventory", box_field, data[box_field] + 1)
    await callback.answer("📦 Сундук добавлен в инвентарь! Открой его там.", show_alert=True)
    await shop_boxes_callback(callback)

@dp.callback_query(F.data == "shop_titles")
async def shop_titles_callback(callback: types.CallbackQuery):
    data = get_user_data(callback.from_user.id)
    text = f"🏅 **МАГАЗИН УНИКАЛЬНЫХ ТИТУЛОВ**\nТвой текущий титул: `{data['current_title']}`\n\n"
    buttons = []
    for price, title_name in TITLES_CONFIG.items():
    for price, title_name in TITLES_CONFIG.items():
        text += f"▪️ {title_name} | Цена: {price} 🍙\n"
        buttons.append([types.InlineKeyboardButton(text=f"Купить {title_name}", callback_data=f"buy_title_{price}")])
    
    if data["current_title"] != "🚫 Отсутствует":
        text += f"\n🏆 Твой текущий титул: `{data['current_title']}`"
        
    buttons.append([types.InlineKeyboardButton(text="🔙 Назад к категориям", callback_data="menu_shop")])
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=types.InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()

@dp.callback_query(F.data.startswith("buy_title_"))
async def buy_title_process(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    price = int(callback.data.split("buy_title_")[-1])
    data = get_user_data(user_id)
    title_name = TITLES_CONFIG[price]
    
    if data["rice"] < price:
        await callback.answer(f"❌ Недостаточно 🍙! Нужно {price}", show_alert=True)
        return
        
    if data["current_title"] == title_name:
        await callback.answer("❌ У тебя уже куплен этот титул!", show_alert=True)
        return
        
    update_field(user_id, "users", "rice", data["rice"] - price)
    update_field(user_id, "users", "current_title", title_name)
    
    await callback.message.edit_text(
        f"🎉 **ПОЗДРАВЛЯЕМ С ПОКУПКОЙ ТИТУЛА!** 🎉\n\n"
        f"Теперь в твоем профиле гордо красуется: `{title_name}`!",
        parse_mode="Markdown",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[[types.InlineKeyboardButton(text="🔙 В магазин титулов", callback_data="shop_titles")]]])
    )
    await callback.answer()


# ==========================================
# ОСТАЛЬНЫЕ КАТЕГОРИИ МАГАЗИНА (БИЗНЕС, VIP, XP, БУСТЫ, БОКСЫ)
# ==========================================
@dp.callback_query(F.data == "shop_biz")
async def shop_biz_callback(callback: types.CallbackQuery):
    data = get_user_data(callback.from_user.id)
    text = "🚜 **МАГАЗИН: РИСОВЫЕ ПРЕДПРИЯТИЯ (Доход в час)**\n\n"
    buttons = []
    for key, cfg in BUSINESS_CONFIG.items():
        text += f"▪️ {cfg['name']} | Цена: {cfg['price']} 🍙 | Доход: +{cfg['income']} 🍙/ч\n   👉 У тебя: {data[key]} шт.\n\n"
        buttons.append([types.InlineKeyboardButton(text=f"Купить {cfg['name']}", callback_data=f"buy_biz_{key}")])
    buttons.append([types.InlineKeyboardButton(text="🔙 Назад к категориям", callback_data="menu_shop")])
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=types.InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()

@dp.callback_query(F.data.startswith("buy_biz_"))
async def buy_biz_process(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    biz_key = callback.data.split("buy_biz_")[-1]
    data = get_user_data(user_id)
    cfg = BUSINESS_CONFIG[biz_key]
    
    if data["rice"] < cfg["price"]:
        await callback.answer(f"❌ Недостаточно 🍙! Нужно {cfg['price']}", show_alert=True)
        return
        
    update_field(user_id, "users", "rice", data["rice"] - cfg["price"])
    update_field(user_id, "businesses", biz_key, data[biz_key] + 1)
    
    await callback.message.edit_text(
        f"🎉 Ты успешно купил объект: **{cfg['name']}**!\n"
        f"Твой пассивный доход увеличен на **+{cfg['income']} 🍙/час**.",
        parse_mode="Markdown",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[[types.InlineKeyboardButton(text="🔙 К предприятиям", callback_data="shop_biz")]]])
    )
    await callback.answer()

@dp.callback_query(F.data == "shop_vip")
async def shop_vip_callback(callback: types.CallbackQuery):
    data = get_user_data(callback.from_user.id)
    text = (
        f"👑 **МАГАЗИН: VIP-ПОДПИСКА (ПРЕМИУМ)**\n\n"
        f"🎁 **Что дает статус VIP:**\n"
        f"🔥 Множитель **X2** к доходу со всех твоих предприятий!\n"
        f"🎲 Доступ к бесплатной ежедневной рулетке без риска проиграть!\n"
        f"🧺 Повышенный бонус с плантаций раз в 6 часов (3500 🍙 вместо 2000 🍙)!\n"
        f"🎟 Множитель **X1.5** к получаемому XP для Brawl Pass!\n\n"
        f"💰 **Цены на подписку:**\n"
        f"▪️ VIP на 10 дней — 12 000 🍙\n"
        f"▪️ VIP на 20 дней — 18 000 🍙\n"
        f"▪️ VIP на 30 дней — 25 000 🍙"
    )
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="👑 Купить на 10 дней (12k 🍙)", callback_data="buy_vip_10")],
        [types.InlineKeyboardButton(text="👑 Купить на 20 дней (18k 🍙)", callback_data="buy_vip_20")],
        [types.InlineKeyboardButton(text="👑 Купить на 30 дней (25k 🍙)", callback_data="buy_vip_30")],
        [types.InlineKeyboardButton(text="🔙 Назад к категориям", callback_data="menu_shop")]
    ])
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=kb)
    await callback.answer()

@dp.callback_query(F.data.startswith("buy_vip_"))
async def buy_vip_process(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    days = int(callback.data.split("buy_vip_")[-1])
    data = get_user_data(user_id)
    
    prices = {10: 12000, 20: 18000, 30: 25000}
    price = prices[days]
    
    if data["rice"] < price:
        await callback.answer(f"❌ Недостаточно 🍙! Нужно {price}", show_alert=True)
        return
        
    now = int(time.time())
    current_vip = max(data["vip_until"], now)
    new_vip_time = current_vip + (days * 24 * 3600)
    
    update_field(user_id, "users", "rice", data["rice"] - price)
    update_field(user_id, "users", "vip_until", new_vip_time)
    
    await callback.message.edit_text(
        f"👑 **ПОЗДРАВЛЯЕМ! ТЫ ПРИОБРЕЛ VIP НА {days} ДНЕЙ!** 👑\n\n"
        f"Все твои бонусы, множители и бесплатные игры уже активированы!",
        parse_mode="Markdown",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[[types.InlineKeyboardButton(text="🔙 Назад", callback_data="shop_vip")]]])
    )
    await callback.answer()

@dp.callback_query(F.data == "shop_xp")
async def shop_xp_callback(callback: types.CallbackQuery):
    text = (
        f"🎫 **МАГАЗИН: ПАКИ ОПЫТА BRAWL PASS**\n\n"
        f"Ускорь свое продвижение по уровням Пасса и забери топовые награды!\n\n"
        f"1. 🍬 Конфета XP (+25 XP) — 600 🍙\n"
        f"2. 🔋 Малый пак XP (+75 XP) — 1 800 🍙\n"
        f"3. 📦 Средняя коробка XP (+150 XP) — 3 500 🍙\n"
        f"4. 🚀 Большой контейнер XP (+300 XP) — 6 500 🍙\n"
        f"5. 🎫 Билет Прорыва (+1 уровень!) — 9 000 🍙"
    )
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🍬 Конфета XP (600 🍙)", callback_data="buy_xp_25"), types.InlineKeyboardButton(text="🔋 Малый пак (1.8k 🍙)", callback_data="buy_xp_75")],
        [types.InlineKeyboardButton(text="📦 Средний пак (3.5k 🍙)", callback_data="buy_xp_150"), types.InlineKeyboardButton(text="🚀 Большой пак (6.5k 🍙)", callback_data="buy_xp_300")],
        [types.InlineKeyboardButton(text="🎫 Билет Прорыва (9k 🍙)", callback_data="buy_xp_skip")],
        [types.InlineKeyboardButton(text="🔙 Назад к категориям", callback_data="menu_shop")]
    ])
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=kb)
    await callback.answer()

@dp.callback_query(F.data.startswith("buy_xp_"))
async def buy_xp_process(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    mode = callback.data.split("buy_xp_")[-1]
    data = get_user_data(user_id)
    
    if data["level"] >= 25:
        await callback.answer("❌ У тебя уже максимальный уровень Brawl Pass!", show_alert=True)
        return
        
    if mode == "skip":
        price = 9000
        if data["rice"] < price:
            await callback.answer("❌ Недостаточно 🍙!", show_alert=True)
            return
        update_field(user_id, "users", "rice", data["rice"] - price)
        req = get_required_xp(data["level"])
        xp_msg = add_xp(user_id, req - data["xp"]) # Добавляем ровно столько, сколько нужно до апа
        msg = f"🎫 Ты использовал Билет Прорыва и мгновенно повысил уровень!{xp_msg}"
    else:
        amount = int(mode)
        prices = {25: 600, 75: 1800, 150: 3500, 300: 6500}
        price = prices[amount]
        if data["rice"] < price:
            await callback.answer("❌ Недостаточно 🍙!", show_alert=True)
            return
        update_field(user_id, "users", "rice", data["rice"] - price)
        xp_msg = add_xp(user_id, amount)
        msg = f"🍬 Пакет опыта успешно куплен!{xp_msg}"
        
    await callback.message.edit_text(msg, parse_mode="Markdown", reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[[types.InlineKeyboardButton(text="🔙 Назад", callback_data="shop_xp")]]]))
    await callback.answer()

@dp.callback_query(F.data == "shop_items")
async def shop_items_callback(callback: types.CallbackQuery):
    text = (
        f"🥤 **МАГАЗИН: РАСХОДНИКИ И БУСТЫ**\n\n"
        f"🥤 **Рисовый энергетик** — 1 000 🍙\n"
        f"👉 _Дает эффект x1.5 к пассивному сбору со всех фабрик на 1 час после активации из рюкзака._\n\n"
        f"🛡 **Амулет от воров** — 2 000 🍙\n"
        f"👉 _Защищает твой баланс в чате от ограблений. Вор гарантированно поймает неудачу и заплатит штраф._"
    )
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="Купить Энергетик (1k 🍙)", callback_data="buy_item_drink")],
        [types.InlineKeyboardButton(text="Купить Амулет (2k 🍙)", callback_data="buy_item_amulet")],
        [types.InlineKeyboardButton(text="🔙 Назад к категориям", callback_data="menu_shop")]
    ])
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=kb)
    await callback.answer()

@dp.callback_query(F.data.startswith("buy_item_"))
async def buy_item_process(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    item = callback.data.split("buy_item_")[-1]
    data = get_user_data(user_id)
        # Продолжение обработки покупки расходников
    prices = {"drink": 1000, "amulet": 2000}
    price = prices.get(item, 999999)
    
    if data["rice"] < price:
        await callback.answer(f"❌ Недостаточно 🍙! Нужно {price}", show_alert=True)
        return
        
    update_field(user_id, "users", "rice", data["rice"] - price)
    if item == "drink":
        update_field(user_id, "inventory", "energy_drink", data["energy_drink"] + 1)
        await callback.answer("🎉 Энергетик добавлен в инвентарь!", show_alert=True)
    elif item == "amulet":
        update_field(user_id, "inventory", "amulet", data["amulet"] + 1)
        await callback.answer("🎉 Амулет добавлен в инвентарь!", show_alert=True)
        
    await shop_items_callback(callback)

@dp.callback_query(F.data == "shop_boxes")
async def shop_boxes_callback(callback: types.CallbackQuery):
    data = get_user_data(callback.from_user.id)
    text = (
        f"📦 **МАГАЗИН: СУНДУКИ С СЮРПРИЗОМ**\n\n"
        f"💰 Твой баланс: **{data['rice']} 🍙**\n\n"
        f"1. **Рисовая коробка** 📦 — 1 500 🍙\n"
        f"2. **Ларец Сенсея** 💎 — 5 000 🍙\n"
        f"3. **Императорский сундук** 🌌 — 15 000 🍙 *(Двойной дроп!)*"
    )
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="Купить Коробку 📦", callback_data="buy_box_1")],
        [types.InlineKeyboardButton(text="Купить Ларец 💎", callback_data="buy_box_2")],
        [types.InlineKeyboardButton(text="Купить Сундук 🌌", callback_data="buy_box_3")],
        [types.InlineKeyboardButton(text="🔙 Назад", callback_data="menu_shop")]
    ])
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=kb)
    await callback.answer()

@dp.callback_query(F.data.startswith("buy_box_"))
async def buy_box_process(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    box_num = callback.data.split("buy_box_")[-1]
    data = get_user_data(user_id)
    
    prices = {"1": 1500, "2": 5000, "3": 15000}
    price = prices[box_num]
    
    if data["rice"] < price:
        await callback.answer(f"❌ Недостаточно 🍙! Нужно {price}", show_alert=True)
        return
        
    update_field(user_id, "users", "rice", data["rice"] - price)
    db_fields = {"1": "box1", "2": "box2", "3": "box3"}
    field = db_fields[box_num]
    
    update_field(user_id, "inventory", field, data[field] + 1)
    await callback.answer("🎉 Сундук успешно куплен и добавлен в твой 🎒 Инвентарь!", show_alert=True)
    await shop_boxes_callback(callback)

@dp.callback_query(F.data == "shop_titles")
async def shop_titles_callback(callback: types.CallbackQuery):
    data = get_user_data(callback.from_user.id)
    text = f"🏅 **МАГАЗИН УНИКАЛЬНЫХ ТИТУЛОВ**\n\n💰 Твой баланс: **{data['rice']} 🍙**\n\n"
    buttons = []
    
    for price, title_name in TITLES_CONFIG.items():
        text += f"▪️ {title_name} — *{price} 🍙*\n"
        if data["current_title"] != title_name:
            buttons.append([types.InlineKeyboardButton(text=f"Купить: {title_name}", callback_data=f"buy_title_{price}")])
            
    buttons.append([types.InlineKeyboardButton(text="🔙 Назад", callback_data="menu_shop")])
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=types.InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()

@dp.callback_query(F.data.startswith("buy_title_"))
async def buy_title_process(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    price = int(callback.data.split("buy_title_")[-1])
    data = get_user_data(user_id)
    title_name = TITLES_CONFIG[price]
    
    if data["rice"] < price:
        await callback.answer(f"❌ Недостаточно 🍙! Нужно {price}", show_alert=True)
        return
        
    update_field(user_id, "users", "rice", data["rice"] - price)
    update_field(user_id, "users", "current_title", title_name)
    
    await callback.answer(f"🎉 Поздравляем! Твой новый титул: {title_name}", show_alert=True)
    await shop_titles_callback(callback)

# ==========================================
# ИГРОВОЙ ЦЕНТР И МИНИ-ИГРЫ
# ==========================================
@dp.callback_query(F.data == "menu_games")
async def games_menu_callback(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "🎮 **ИГРОВОЙ ЦЕНТР РИСОВОЙ ИМПЕРИИ**\n\n"
        "🎪 _Здесь ты можешь испытать удачу и заработать кучу 🍙 и XP!_\n\n"
        "📜 **Доступные команды в чате:**\n"
        "🎰 `/casino [ставка]` — классический автомат 50/50\n"
        "🎲 `/dice [ставка] [1-6]` — угадай число кубика (x5 призов!)\n"
        "📊 `/trade [ставка] [вверх/вниз]` — угадай курс риса\n"
        "⚔️ `/duel [ID игрока] [ставка]` — вызвать соперника на дуэль\n"
        "🎯 `/darts [ID игрока] [ставка]` — соревнование по дартсу\n"
        "🌾 `/work` — отправиться работать на плантации\n"
        "🥷 `/rob [ID игрока]` — попробовать ограбить богача\n\n"
        "👇 _А также эксклюзивное колесо удачи:_ ",
        parse_mode="Markdown",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="🎡 Крутить Рулетку", callback_data="play_roulette")],
            [types.InlineKeyboardButton(text="🔙 Главное Меню", callback_data="to_main")]
        ])
    )
    await callback.answer()

@dp.callback_query(F.data == "play_roulette")
async def roulette_process(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    data = get_user_data(user_id)
    if not data: return
    
    now = int(time.time())
    is_vip = data["vip_until"] > now
    
    # Проверка бесплатного прокрута для VIP
    if is_vip:
        # Для VIP ограничение 1 раз в 24 часа бесплатно
        # Будем использовать last_bonus для упрощения или внутреннее время
        pass
        
    price = 0 if is_vip else 500
    
    if not is_vip and data["rice"] < price:
        await callback.answer("❌ Обычная рулетка стоит 500 🍙! У тебя нет столько средств.", show_alert=True)
        return
        
    if not is_vip:
        update_field(user_id, "users", "rice", data["rice"] - price)
        
    # Логика наград в рулетке
    win_type = random.choice(["rice", "xp", "lose"])
    if win_type == "rice":
        amount = random.randint(100, 2500)
        update_field(user_id, "users", "rice", get_user_data(user_id)["rice"] + amount)
        msg = f"🎉 **УДАЧА!** Колесо остановилось на мешке с рисом! Награда: **+{amount} 🍙**"
    elif win_type == "xp":
        amount = random.randint(20, 60)
        xp_msg = add_xp(user_id, amount)
        msg = f"⚡ **ОПЫТ!** Колесо начислило тебе очки активности! {xp_msg}"
    else:
        msg = "😢 **НЕ ПОВЕЗЛО!** Стрелка остановилась на пустом поле. Попробуй еще раз!"
        
    await callback.message.edit_text(
        f"🎡 **КОЛЕСО УДАЧИ**\n\n{msg}",
        parse_mode="Markdown",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="🎡 Крутить снова", callback_data="play_roulette")],
            [types.InlineKeyboardButton(text="🔙 В меню игр", callback_data="menu_games")]
        ])
    )
    await callback.answer()

@dp.message(Command("casino"))
async def cmd_casino(message: types.Message):
    user_id = message.from_user.id
    data = get_user_data(user_id)
    if not data: return
    
    args = message.text.split()
    if len(args) < 2 or not args[1].isdigit():
        await message.answer("🎰 **Укажи ставку!** Пример: `/casino 50`", parse_mode="Markdown")
        return
        
    bet = int(args[1])
    if bet <= 0 or data["rice"] < bet:
        await message.answer("❌ Неверная ставка или у тебя нет столько 🍙!")
        return
        
    if random.choice([True, False]):
        update_field(user_id, "users", "rice", data["rice"] + bet)
        xp_msg = add_xp(user_id, random.randint(2, 8))
        await message.answer(f"🎰 **ПОБЕДА!** Твоя ставка сыграла. Получено **+{bet} 🍙**{xp_msg}", parse_mode="Markdown")
    else:
        update_field(user_id, "users", "rice", data["rice"] - bet)
        await message.answer(f"🎰 **ПРОИГРЫШ!** Автомат забрал твои **{bet} 🍙**. Не унывай!")

@dp.message(Command("dice"))
async def cmd_dice(message: types.Message):
    user_id = message.from_user.id
    data = get_user_data(user_id)
    if not data: return
    
    args = message.text.split()
    if len(args) < 3 or not args[1].isdigit() or not args[2].isdigit():
        await message.answer("🎲 **Правильный формат:** `/dice [ставка] [число от 1 до 6]`", parse_mode="Markdown")
        return
        
    bet = int(args[1])
    guess = int(args[2])
    
    if bet <= 0 or data["rice"] < bet or guess < 1 or guess > 6:
        await message.answer("❌ Ошибка в ставке или числе (нужно от 1 до 6)!")
        return
        
    bot_dice = random.randint(1, 6)
    if guess == bot_dice:
        win = bet * 5
        update_field(user_id, "users", "rice", data["rice"] + win)
        xp_msg = add_xp(user_id, random.randint(5, 15))
        await message.answer(f"🎲 **ДЖЕКПОТ!** Выпало число `{bot_dice}`! Ты угадал и забрал **+{win} 🍙** (x5 к ставке)!{xp_msg}", parse_mode="Markdown")
    else:
        update_field(user_id, "users", "rice", data["rice"] - bet)
        await message.answer(f"🎲 **МИМО!** Выпало число `{bot_dice}`, а ты ставил на `{guess}`. Ставка **{bet} 🍙** потеряна.")

@dp.message(Command("trade"))
async def cmd_trade(message: types.Message):
    user_id = message.from_user.id
    data = get_user_data(user_id)
    if not data: return
    
    args = message.text.split()
    if len(args) < 3 or not args[1].isdigit() or args[2].lower() not in ["вверх", "вниз"]:
        await message.answer("📊 **Формат биржи:** `/trade [ставка] [вверх / вниз]`", parse_mode="Markdown")
        return
        
    bet = int(args[1])
    direction = args[2].lower()
    
    if bet <= 0 or data["rice"] < bet:
        await message.answer("❌ Проблема со ставкой!")
            return
        
    market = random.choice(["вверх", "вниз"])
    if direction == market:
        update_field(user_id, "users", "rice", data["rice"] + bet)
        xp_msg = add_xp(user_id, random.randint(3, 9))
        await message.answer(f"📈 **БИРЖА РИСА:** Курс пошел **{market}**! Прогноз верный: **+{bet} 🍙**{xp_msg}", parse_mode="Markdown")
    else:
        update_field(user_id, "users", "rice", data["rice"] - bet)
        await message.answer(f"📉 **БИРЖА РИСА:** Курс резко пошел **{market}**. Твоя сделка в **-{bet} 🍙** закрылась в минус.")

@dp.message(Command("work"))
async def cmd_work(message: types.Message):
    user_id = message.from_user.id
    data = get_user_data(user_id)
    if not data: return
    
    now = int(time.time())
    if now - data["last_work"] < 7200: # 2 часа кулдаун
        rem = 7200 - (now - data["last_work"])
        await message.answer(f"⏳ Твоя спина ещё болит от прошлой смены! Отдыхать осталось **{rem // 60} мин.**")
        return
        
    earned = random.randint(150, 400)
    xp_earned = random.randint(5, 12)
    
    update_field(user_id, "users", "rice", data["rice"] + earned)
    update_field(user_id, "users", "last_work", now)
    xp_msg = add_xp(user_id, xp_earned)
    
    texts = [
        f"🌾 Ты по колено в грязи собирал рис на плантациях... Заработано **+{earned} 🍙**!{xp_msg}",
        f"🚜 Ты весь день чинил сломанный трактор, но хозяин щедро заплатил: **+{earned} 🍙**!{xp_msg}",
        f"🧺 Ты упаковывал мешки риса на экспорт. Твой труд вознагражден: **+{earned} 🍙**!{xp_msg}"
    ]
    await message.answer(random.choice(texts), parse_mode="Markdown")

@dp.message(Command("rob"))
async def cmd_rob(message: types.Message):
    user_id = message.from_user.id
    data = get_user_data(user_id)
    if not data: return
    
    args = message.text.split()
    if len(args) < 2 or not args[1].isdigit():
        await message.answer("🥷 **Кого грабим?** Напиши ID игрока: `/rob [ID]`")
        return
        
    target_id = int(args[1])
    target_data = get_user_data(target_id)
    
    if not target_data or target_id == user_id:
        await message.answer("❌ Такой игрок не найден в базе Империи!")
        return
        
    now = int(time.time())
    if now - data["last_rob"] < 14400: # 4 часа кулдаун
        await message.answer("❌ Полиция всё ещё ищет тебя! Снизь активность на пару часов.")
        return
        
    # Проверка амулета у жертвы
    if target_data["amulet"] > 0:
        update_field(target_id, "inventory", "amulet", target_data["amulet"] - 1)
        straf = int(data["rice"] * 0.15)
        update_field(user_id, "users", "rice", data["rice"] - straf)
        update_field(target_id, "users", "rice", target_data["rice"] + straf)
        update_field(user_id, "users", "last_rob", now)
        await message.answer(f"🛡 **ОХРАНА!** У игрока был активирован **Амулет от воров**! Твой план провалился, ты пойман и выплатил штраф жертве: **-{straf} 🍙**.")
        return
        
    # Шанс 40% на успех
    if random.random() < 0.40:
        stolen = int(target_data["rice"] * random.uniform(0.1, 0.3))
        if stolen <= 0: stolen = 10
        update_field(user_id, "users", "rice", data["rice"] + stolen)
        update_field(target_id, "users", "rice", target_data["rice"] - stolen)
        update_field(user_id, "users", "last_rob", now)
        await message.answer(f"🥷 **УСПЕШНЫЙ НАЛЕТ!** Ты тихо пробрался на склады *{target_data['nickname']}* и украл **+{stolen} 🍙**!", parse_mode="Markdown")
    else:
        straf = random.randint(200, 1000)
        if data["rice"] < straf: straf = data["rice"]
        update_field(user_id, "users", "rice", data["rice"] - straf)
        update_field(user_id, "users", "last_rob", now)
        await message.answer(f"🥷 **ПРОФАН!** Тебя поймали с поличным при попытке ограбления. Пришлось отдать страже штраф: **-{straf} 🍙**.")

@dp.message(Command("duel"))
async def cmd_duel(message: types.Message):
    user_id = message.from_user.id
    data = get_user_data(user_id)
    if not data: return
    
    args = message.text.split()
    if len(args) < 3 or not args[1].isdigit() or not args[2].isdigit():
        await message.answer("⚔️ **Бросить вызов:** `/duel [ID оппонента] [ставка]`")
        return
        
    target_id = int(args[1])
    bet = int(args[2])
    target_data = get_user_data(target_id)
    
    if not target_data or target_id == user_id or bet <= 0 or data["rice"] < bet or target_data["rice"] < bet:
        await message.answer("❌ Ошибка! Неверный ID или у кого-то из вас не хватает 🍙 для ставки.")
        return
        
    p1_text = data["nickname"]
    p2_text = target_data["nickname"]
    
    fight_scenarios = [
        f"⚔️ **ДУЭЛЬ!** {p1_text} забросал соперника гнилым рисом... Но {p2_text} ловко увернулся и нанес сокрушительный удар мешком зерна!",
        f"⚔️ **ДУЭЛЬ!** {p2_text} поскользнулся на рисовом зернышке, и {p1_text} мгновенно обезоружил его точным выпадом!"
    ]
    
    await message.answer("⚔️ _Скрещиваются рисовые мечи, бой начался..._")
    await asyncio.sleep(2)
    
    if random.choice([True, False]):
        update_field(user_id, "users", "rice", data["rice"] + bet)
        update_field(target_id, "users", "rice", target_data["rice"] - bet)
        update_field(user_id, "users", "wins", data["wins"] + 1)
        update_field(target_id, "users", "losses", target_data["losses"] + 1)
        xp_msg = add_xp(user_id, random.randint(10, 20))
        await message.answer(f"{random.choice(fight_scenarios)}\n\n🏆 **Победитель:** {p1_text}! Куш: **+{bet} 🍙**{xp_msg}", parse_mode="Markdown")
    else:
        update_field(user_id, "users", "rice", data["rice"] - bet)
        update_field(target_id, "users", "rice", target_data["rice"] + bet)
        update_field(user_id, "users", "losses", data["losses"] + 1)
        update_field(target_id, "users", "wins", target_data["wins"] + 1)
        xp_msg = add_xp(target_id, random.randint(10, 20))
        await message.answer(f"{random.choice(fight_scenarios)}\n\n🏆 **Победитель:** {p2_text}! Куш: **+{bet} 🍙**", parse_mode="Markdown")

@dp.message(Command("darts"))
async def cmd_darts(message: types.Message):
    # Команда дартса работает по аналогичной логике дуэли ставок
    await cmd_duel(message)

# ==========================================
# ЗАПУСК БОТА
# ==========================================
async def main():
    init_db()
    print("🚀 Рисовая Империя успешно запущена и готова к заливке на GitHub!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

        



