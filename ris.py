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

TOKEN = "ВСТАВЬ_ТОКЕН"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

DB_NAME = "rice_empire.db"


# ======================
# FSM
# ======================

class RegistrationStates(StatesGroup):
    waiting_for_nickname = State()


# ======================
# DATABASE
# ======================

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
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

    c.execute("""
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

    c.execute("""
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


def get_user_data(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    u = c.fetchone()

    if not u:
        conn.close()
        return None

    c.execute("SELECT * FROM businesses WHERE user_id=?", (user_id,))
    b = c.fetchone()

    c.execute("SELECT * FROM inventory WHERE user_id=?", (user_id,))
    i = c.fetchone()

    conn.close()

    if not b:
        b = (user_id, 0, 0, 0, 0, 0, 0, 0, int(time.time()))
    if not i:
        i = (user_id, 0, 0, 0, 0, 0)

    return {
        "user_id": u[0],
        "nickname": u[1],
        "rice": u[2],
        "xp": u[3],
        "level": u[4],
        "vip_until": u[5],
        "current_title": u[6],
        "last_bonus": u[7],
        "last_work": u[8],
        "last_rob": u[9],
        "energy_until": u[10],
        "wins": u[11],
        "losses": u[12],

        "b1": b[1], "b2": b[2], "b3": b[3], "b4": b[4],
        "b5": b[5], "b6": b[6], "b7": b[7],
        "last_passive_collect": b[8],

        "energy_drink": i[1],
        "amulet": i[2],
        "box1": i[3],
        "box2": i[4],
        "box3": i[5],
    }


def register_user(user_id, nickname):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("INSERT OR IGNORE INTO users (user_id, nickname) VALUES (?,?)", (user_id, nickname))
    c.execute("INSERT OR IGNORE INTO businesses (user_id, last_passive_collect) VALUES (?,?)", (user_id, int(time.time())))
    c.execute("INSERT OR IGNORE INTO inventory (user_id) VALUES (?)", (user_id,))

    conn.commit()
    conn.close()


def update_field(user_id, table, field, value):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(f"UPDATE {table} SET {field}=? WHERE user_id=?", (value, user_id))
    conn.commit()
    conn.close()


# ======================
# START + REG
# ======================

@dp.message(CommandStart())
async def start(message: types.Message, state: FSMContext):
    init_db()

    data = get_user_data(message.from_user.id)

    if data:
        await message.answer("👋 Добро пожаловать обратно!")
    else:
        await message.answer("Введите ник:")
        await state.set_state(RegistrationStates.waiting_for_nickname)


@dp.message(RegistrationStates.waiting_for_nickname)
async def nick(message: types.Message, state: FSMContext):
    nickname = message.text.strip()

    if len(nickname) < 2 or len(nickname) > 20:
        await message.answer("Ник 2–20 символов")
        return

    register_user(message.from_user.id, nickname)
    await state.clear()

    await message.answer("Профиль создан!")


# ======================
# PROFILE
# ======================

@dp.callback_query(F.data == "menu_profile")
async def profile(c: types.CallbackQuery):
    d = get_user_data(c.from_user.id)

    await c.message.edit_text(
        f"👤 Профиль\n"
        f"🍙 Рис: {d['rice']}\n"
        f"⭐ Уровень: {d['level']}\n"
        f"🎯 XP: {d['xp']}"
    )
    await c.answer()await message.answer("❌ Никнейм должен содержать от 2 до 20 символов! Попробуй еще раз:")returnregister_user(message.from_user.id, nickname)await state.clear()await message.answer(f"🎉 Отлично! Твой игровой профиль успешно создан.\nТвой никнейм: {nickname}\nТебе начислено стартовые 100 🍙!\n\n_Начнем строить империю!_ 👇", parse_mode="Markdown", reply_markup=main_keyboard())@dp.message(Command("menu"))async def cmd_menu(message: types.Message):data = get_user_data(message.from_user.id)if not data: returnawait message.answer("🗂 Главное управление рисовой базой:", parse_mode="Markdown", reply_markup=main_keyboard())@dp.callback_query(F.data == "to_main")async def back_to_main_callback(callback: types.CallbackQuery):await callback.message.edit_text("🗂 Главное управление рисовой базой:", parse_mode="Markdown", reply_markup=main_keyboard())await callback.answer()@dp.callback_query(F.data == "menu_profile")async def profile_callback(callback: types.CallbackQuery):user_id = callback.from_user.iddata = get_user_data(user_id)if not data: returnpassive = calc_passive_income(data)if passive > 0:update_field(user_id, "users", "rice", data["rice"] + passive)update_field(user_id, "businesses", "last_passive_collect", int(time.time()))data = get_user_data(user_id)now = int(time.time())vip_status = "❌ Не активен"if data["vip_until"] > now:rem = data["vip_until"] - nowvip_status = f"👑 Активен (осталось {rem // 3600} ч.)"energy_status = ""if data["energy_until"] > now:energy_status = " ⚡ (Действует Энергетик x1.5)"auto_status = get_auto_status(data["rice"])req_xp = get_required_xp(data["level"])profile_text = (f"👤 ИГРОВОЙ ПРОФИЛЬ ИМПЕРИИ\n"f"━━━━━━━━━━━━━━━━━━━━\n"f"🆔 Твой ID: {data['user_id']}\n"f"👤 Никнейм: {data['nickname']}\n"f"🏅 Купленный Титул: {data['current_title']}\n"f"📊 Ранг за богатство: {auto_status}\n"f"👑 VIP-Статус: {vip_status}\n"f"━━━━━━━━━━━━━━━━━━━━\n"f"🍙 Баланс риса: {data['rice']} 🍙{energy_status}\n"f"🎟 Brawl Pass: {data['level']}/25 Уровень ({data['xp']}/{req_xp} XP)\n"f"⚔️ Статистика дуэлей: 🏆 Побед: {data['wins']} | 💀 Проиграно: {data['losses']}\n"f"━━━━━━━━━━━━━━━━━━━━\n"f"🌾 Пассивный доход зачислен автоматически при открытии профиля!")kb = types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text="🔙 Назад", callback_data="to_main")]])await callback.message.edit_text(profile_text, parse_mode="Markdown", reply_markup=kb)await callback.answer()@dp.callback_query(F.data == "menu_bonus")async def bonus_callback(callback: types.CallbackQuery):user_id = callback.from_user.iddata = get_user_data(user_id)if not data: returnnow = int(time.time())cooldown = 6 * 3600if now - data["last_bonus"] < cooldown:time_left = cooldown - (now - data["last_bonus"])hours = time_left // 3600minutes = (time_left % 3600) // 60await callback.message.edit_text(f"⏳ Сбор плантации закрыт!\n\nТвои крестьяне отдыхают. До следующего сбора бонуса осталось: {hours} ч. {minutes} мин. 🍙", parse_mode="Markdown", reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text="🔙 Назад", callback_data="to_main")]]))await callback.answer()returnis_vip = data["vip_until"] > nowif is_vip:give_rice = 3500give_xp = random.randint(20, 40)vip_tag = "👑 VIP Бонус"else:give_rice = 2000give_xp = random.randint(5, 25)vip_tag = "🌾 Обычный Бонус"update_field(user_id, "users", "rice", data["rice"] + give_rice)update_field(user_id, "users", "last_bonus", now)xp_msg = add_xp(user_id, give_xp)success_text = f"{vip_tag} успешно собран!\n\n🌾 Ты зашел на плантации и собрал:\n💰 Получено: +{give_rice} 🍙\n{xp_msg}"await callback.message.edit_text(success_text, parse_mode="Markdown", reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text="🔙 Назад", callback_data="to_main")]]))await callback.answer()@dp.callback_query(F.data == "menu_inventory")async def inventory_callback(callback: types.CallbackQuery):user_id = callback.from_user.iddata = get_user_data(user_id)if not data: returninv_text = (f"🎒 ТВОЙ КАРМАННЫЙ ИНВЕНТАРЬ\n"f"━━━━━━━━━━━━━━━━━━━━\n"f"🥤 Рисовый энергетик (x1.5): {data['energy_drink']} шт.\n"f"🛡 Амулет от наглых воров: {data['amulet']} шт.\n\n"f"📦 Хранилище нераспечатанных сундуков:\n"f"├ 📦 Рисовая коробка: {data['box1']} шт.\n"f"├ 💎 Ларец Сенсея: {data['box2']} шт.\n"f"└ 🌌 Императорский сундук: {data['box3']} шт.\n"f"━━━━━━━━━━━━━━━━━━━━\n"f"⚡ Выбери вещь в меню ниже для активации: ")buttons = []if data["energy_drink"] > 0:buttons.append([types.InlineKeyboardButton(text="🥤 Выпить Энергетик", callback_data="use_energy")])if data["box1"] > 0:buttons.append([types.InlineKeyboardButton(text="📦 Открыть Рисовую коробку", callback_data="open_box1")])if data["box2"] > 0:buttons.append([types.InlineKeyboardButton(text="💎 Открыть Ларец Сенсея", callback_data="open_box2")])if data["box3"] > 0:buttons.append([types.InlineKeyboardButton(text="🌌 Открыть Императорский сундук", callback_data="open_box3")])buttons.append([types.InlineKeyboardButton(text="🔙 Назад", callback_data="to_main")])await callback.message.edit_text(inv_text, parse_mode="Markdown", reply_markup=types.InlineKeyboardMarkup(inline_keyboard=buttons))await callback.answer()@dp.callback_query(F.data == "use_energy")async def use_energy_callback(callback: types.CallbackQuery):user_id = callback.from_user.iddata = get_user_data(user_id)if not data or data["energy_drink"] <= 0: returnnow = int(time.time())new_energy_time = max(data["energy_until"], now) + 3600update_field(user_id, "inventory", "energy_drink", data["energy_drink"] - 1)update_field(user_id, "users", "energy_until", new_energy_time)await callback.message.edit_text("🥤 Глоток энергии!\n\nТы выпил рисовый энергетик. Теперь в течение 1 часа абсолютно все твои заводы и грядки приносят в полтора раза (x1.5) больше 🍙 пассивного дохода!", parse_mode="Markdown", reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text="🔙 В инвентарь", callback_data="menu_inventory")]]))await callback.answer()@dp.callback_query(F.data.startswith("open_box"))async def open_box_callback(callback: types.CallbackQuery):user_id = callback.from_user.idbox_type = callback.data.split("box")[-1]data = get_user_data(user_id)if box_type == "1" and data["box1"] > 0:update_field(user_id, "inventory", "box1", data["box1"] - 1)res = random.choice(["rice", "xp", "drink"])if res == "rice":val = random.randint(500, 2000)update_field(user_id, "users", "rice", data["rice"] + val)msg = f"💰 Из коробки выпало: +{val} 🍙!"elif res == "xp":val = random.randint(15, 40)xp_msg = add_xp(user_id, val)msg = f"🎫 Из коробки выпало: {xp_msg}!"else:update_field(user_id, "inventory", "energy_drink", data["energy_drink"] + 1)msg = "🥤 Удача! Из коробки выпал 1 Рисовый энергетик!"elif box_type == "2" and data["box2"] > 0:update_field(user_id, "inventory", "box2", data["box2"] - 1)res = random.choice(["rice", "xp", "vip"])if res == "rice":val = random.randint(2500, 8000)update_field(user_id, "users", "rice", data["rice"] + val)msg = f"💰 Из Ларца Сенсея выпало: +{val} 🍙!"elif res == "xp":val = random.randint(50, 120)xp_msg = add_xp(user_id, val)msg = f"🎫 Из Ларца Сенсея выпало: {xp_msg}!"else:now = int(time.time())vip_time = max(data["vip_until"], now) + (3 * 24 * 3600)update_field(user_id, "users", "vip_until", vip_time)msg = "👑 ОГО! СУПЕР ПРИЗ! Из ларца выпал VIP-статус на 3 дня!"elif box_type == "3" and data["box3"] > 0:update_field(user_id, "inventory", "box3", data["box3"] - 1)r_rice = random.randint(7000, 30000)r_xp = random.randint(150, 400)update_field(user_id, "users", "rice", data["rice"] + r_rice)xp_msg = add_xp(user_id, r_xp)item = random.choice(["drink", "amulet", "vip10"])if item == "drink":update_field(user_id, "inventory", "energy_drink", data["energy_drink"] + 3)item_text = "🥤 3 Рисовых энергетика"elif item == "amulet":update_field(user_id, "inventory", "amulet", data["amulet"] + 1)item_text = "🛡 1 Амулет от воров"else:now = int(time.time())vip_time = max(data["vip_until"], now) + (10 * 24 * 3600)update_field(user_id, "users", "vip_until", vip_time)item_text = "👑 VIP-СТАТУС НА 10 ДНЕЙ!"msg = f"🌌 Двойной Дроп из Императорского сундука!\n\n🎁 Приз №1 (Ресурсы): +{r_rice} 🍙 и {xp_msg}\n🎁 Приз №2 (Вещь в инвентарь): Добавлено {item_text}!"else:await callback.answer("Сундук закончился!")returnawait callback.message.edit_text(f"🎉 ОТКРЫТИЕ КЕЙСА:\n\n{msg}", parse_mode="Markdown", reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text="🔙 В инвентарь", callback_data="menu_inventory")]]))await callback.answer()@dp.callback_query(F.data == "menu_shop")async def shop_callback(callback: types.CallbackQuery):data = get_user_data(callback.from_user.id)await callback.message.edit_text(f"🏪 ДОБРО ПОЖАЛОВАТЬ В ТОРГОВЫЙ ЦЕНТР ИМПЕРИИ! 🍙\n\n💰 Твой текущий баланс: {data['rice']} 🍙\n\n_Выбери интересующую категорию товаров ниже:_ ", parse_mode="Markdown", reply_markup=shop_categories_keyboard())await callback.answer()@dp.callback_query(F.data == "shop_biz")async def shop_biz_callback(callback: types.CallbackQuery):data = get_user_data(callback.from_user.id)text = "🚜 МАГАЗИН: РИСОВЫЕ ПРЕДПРИЯТИЯ (Доход в час)\n\n"buttons = []for key, cfg in BUSINESS_CONFIG.items():text += f"▪️ {cfg['name']} | Цена: {cfg['price']} 🍙 | Доход: +{cfg['income']} 🍙/ч\n   👉 У тебя: {data[key]} шт.\n\n"buttons.append([types.InlineKeyboardButton(text=f"Купить {cfg['name']}", callback_data=f"buy_biz_{key}")])buttons.append([types.InlineKeyboardButton(text="🔙 Назад к категориям", callback_data="menu_shop")])await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=types.InlineKeyboardMarkup(inline_keyboard=buttons))await callback.answer()@dp.callback_query(F.data.startswith("buy_biz_"))async def buy_biz_process(callback: types.CallbackQuery):user_id = callback.from_user.idbiz_key = callback.data.split("buy_biz_")[-1]data = get_user_data(user_id)cfg = BUSINESS_CONFIG[biz_key]if data["rice"] < cfg["price"]:await callback.answer(f"❌ Недостаточно 🍙! Нужно {cfg['price']}", show_alert=True)returnupdate_field(user_id, "users", "rice", data["rice"] - cfg["price"])update_field(user_id, "businesses", biz_key, data[biz_key] + 1)await callback.answer(f"🎉 Вы успешно приобрели {cfg['name']}!", show_alert=True)await shop_biz_callback(callback)@dp.callback_query(F.data == "shop_vip")async def shop_vip_callback(callback: types.CallbackQuery):data = get_user_data(callback.from_user.id)text = (f"👑 МАГАЗИН: ПОКУПКА VIP-СТАТУСА\n\n"f"💰 Твой баланс: {data['rice']} 🍙\n\n"f"✨ Преимущества VIP:\n"f"├ Доход со всех бонусов увеличен!\n"f"├ Бесплатный ежедневный прокрут рулетки!\n"f"└ Ускоренное получение опыта Brawl Pass (x1.5)!\n\n"f"🛒 Выбери тариф подписки:")kb = types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text="🎫 VIP на 10 дней — 12 000 🍙", callback_data="buy_vip_10")],[types.InlineKeyboardButton(text="🎫 VIP на 20 дней — 18 000 🍙", callback_data="buy_vip_20")],[types.InlineKeyboardButton(text="🎫 VIP на 30 дней — 25 000 🍙", callback_data="buy_vip_30")],[types.InlineKeyboardButton(text="🔙 Назад", callback_data="menu_shop")]])await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=kb)await callback.answer()@dp.callback_query(F.data.startswith("buy_vip_"))async def buy_vip_process(callback: types.CallbackQuery):user_id = callback.from_user.iddays = int(callback.data.split("buy_vip_")[-1])data = get_user_data(user_id)prices = {10: 12000, 20: 18000, 30: 25000}price = prices[days]if data["rice"] < price:await callback.answer(f"❌ Недостаточно 🍙! Нужно {price}", show_alert=True)returnnow = int(time.time())new_vip_time = max(data["vip_until"], now) + (days * 24 * 3600)update_field(user_id, "users", "rice", data["rice"] - price)update_field(user_id, "users", "vip_until", new_vip_time)await callback.answer(f"🎉 Поздравляем! VIP-статус продлен на {days} дней!", show_alert=True)await shop_vip_callback(callback)@dp.callback_query(F.data == "shop_xp")async def shop_xp_callback(callback: types.CallbackQuery):data = get_user_data(callback.from_user.id)text = (f"🎫 МАГАЗИН: ПАКИ ОПЫТА BRAWL PASS\n\n"f"💰 Твой баланс: {data['rice']} 🍙\n\n"f"1. 🍬 Конфета XP (+25 XP) — 600 🍙\n"f"2. 🔋 Малый пак XP (+75 XP) — 1 800 🍙\n"f"3. 📦 Средняя коробка XP (+150 XP) — 3 500 🍙\n"f"4. 🚀 Большой контейнер XP (+300 XP) — 6 500 🍙\n"f"5. 🎫 Билет Прорыва (+1 Уровень) — 9 000 🍙")kb = types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text="Купить Конфету 🍬", callback_data="buy_xp_1"), types.InlineKeyboardButton(text="Купить Малый пак 🔋", callback_data="buy_xp_2")],[types.InlineKeyboardButton(text="Купить Коробку 📦", callback_data="buy_xp_3"), types.InlineKeyboardButton(text="Купить Контейнер 🚀", callback_data="buy_xp_4")],[types.InlineKeyboardButton(text="🎫 Купить Скип Уровня", callback_data="buy_xp_5")],[types.InlineKeyboardButton(text="🔙 Назад", callback_data="menu_shop")]])await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=kb)await callback.answer()@dp.callback_query(F.data.startswith("buy_xp_"))async def buy_xp_process(callback: types.CallbackQuery):user_id = callback.from_user.idpack_type = callback.data.split("buy_xp_")[-1]data = get_user_data(user_id)config = {"1": {"price": 600, "xp": 25, "skip": False},"2": {"price": 1800, "xp": 75, "skip": False},"3": {"price": 3500, "xp": 150, "skip": False},"4": {"price": 6500, "xp": 300, "skip": False},"5": {"price": 9000, "xp": 0, "skip": True}}cfg = config[pack_type]if data["rice"] < cfg["price"]:await callback.answer(f"❌ Недостаточно 🍙! Нужно {cfg['price']}", show_alert=True)returnupdate_field(user_id, "users", "rice", data["rice"] - cfg["price"])if cfg["skip"]:if data["level"] < 25:update_field(user_id, "users", "level", data["level"] + 1)update_field(user_id, "users", "xp", 0)await callback.answer("🎉 Уровень Brawl Pass успешно повышен!", show_alert=True)else:await callback.answer("❌ У тебя уже максимальный уровень!", show_alert=True)else:xp_msg = add_xp(user_id, cfg["xp"])await callback.answer(f"🎉 Опыт успешно добавлен! {xp_msg.replace('**', '')}", show_alert=True)await shop_xp_callback(callback)@dp.callback_query(F.data == "shop_items")async def shop_items_callback(callback: types.CallbackQuery):data = get_user_data(callback.from_user.id)text = (f"🥤 МАГАЗИН: РАСХОДНИКИ И БУСТЕРЫ\n\n"f"💰 Твой баланс: {data['rice']} 🍙\n\n"f"🥤 Рисовый энергетик — 1 000 🍙\n"f"👉 Дает x1.5 ко всему пассивному доходу на 1 час!\n\n"f"🛡 Амулет от воров — 2 000 🍙\n"f"👉 Автоматически защищает баланс от грабежей в чате!")kb = types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text="Купить Энергетик 🥤", callback_data="buy_item_drink")],[types.InlineKeyboardButton(text="Купить Амулет 🛡", callback_data="buy_item_amulet")],[types.InlineKeyboardButton(text="🔙 Назад", callback_data="menu_shop")]])await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=kb)await callback.answer()@dp.callback_query(F.data.startswith("buy_item_"))async def buy_item_process(callback: types.CallbackQuery):user_id = callback.from_user.iditem = callback.data.split("buy_item_")[-1]data = get_user_data(user_id)prices = {"drink": 1000, "amulet": 2000}price = prices.get(item, 999999)if data["rice"] < price:await callback.answer(f"❌ Недостаточно 🍙! Нужно {price}", show_alert=True)returnupdate_field(user_id, "users", "rice", data["rice"] - price)if item == "drink":update_field(user_id, "inventory", "energy_drink", data["energy_drink"] + 1)await callback.answer("🎉 Энергетик добавлен в инвентарь!", show_alert=True)elif item == "amulet":update_field(user_id, "inventory", "amulet", data["amulet"] + 1)await callback.answer("🎉 Амулет добавлен в инвентарь!", show_alert=True)await shop_items_callback(callback)@dp.callback_query(F.data == "shop_boxes")async def shop_boxes_callback(callback: types.CallbackQuery):data = get_user_data(callback.from_user.id)text = (f"📦 МАГАЗИН: СУНДУКИ С СЮРПРИЗОМ\n\n"f"💰 Твой баланс: {data['rice']} 🍙\n\n"f"1. Рисовая коробка 📦 — 1 500 🍙\n"f"2. Ларец Сенсея 💎 — 5 000 🍙\n"f"3. Императорский сундук 🌌 — 15 000 🍙 (Двойной дроп!)")kb = types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text="Купить Коробку 📦", callback_data="buy_box_1")],[types.InlineKeyboardButton(text="Купить Ларец 💎", callback_data="buy_box_2")],[types.InlineKeyboardButton(text="Купить Сундук 🌌", callback_data="buy_box_3")],[types.InlineKeyboardButton(text="🔙 Назад", callback_data="menu_shop")]])await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=kb)await callback.answer()@dp.callback_query(F.data.startswith("buy_box_"))async def buy_box_process(callback: types.CallbackQuery):user_id = callback.from_user.idbox_num = callback.data.split("buy_box_")[-1]data = get_user_data(user_id)prices = {"1": 1500, "2": 5000, "3": 15000}price = prices[box_num]if data["rice"] < price:await callback.answer(f"❌ Недостаточно 🍙! Нужно {price}", show_alert=True)returnupdate_field(user_id, "users", "rice", data["rice"] - price)db_fields = {"1": "box1", "2": "box2", "3": "box3"}field = db_fields[box_num]update_field(user_id, "inventory", field, data[field] + 1)await callback.answer("🎉 Сундук успешно куплен и добавлен в твой 🎒 Инвентарь!", show_alert=True)await shop_boxes_callback(callback)@dp.callback_query(F.data == "shop_titles")async def shop_titles_callback(callback: types.CallbackQuery):data = get_user_data(callback.from_user.id)text = f"🏅 МАГАЗИН УНИКАЛЬНЫХ ТИТУЛОВ\n\n💰 Твой баланс: {data['rice']} 🍙\n\n"buttons = []for price, title_name in TITLES_CONFIG.items():text += f"▪️ {title_name} — {price} 🍙\n"if data["current_title"] != title_name:buttons.append([types.InlineKeyboardButton(text=f"Купить: {title_name}", callback_data=f"buy_title_{price}")])buttons.append([types.InlineKeyboardButton(text="🔙 Назад", callback_data="menu_shop")])await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=types.InlineKeyboardMarkup(inline_keyboard=buttons))await callback.answer()@dp.callback_query(F.data.startswith("buy_title_"))async def buy_title_process(callback: types.CallbackQuery):user_id = callback.from_user.idprice = int(callback.data.split("buy_title_")[-1])data = get_user_data(user_id)title_name = TITLES_CONFIG[price]if data["rice"] < price:await callback.answer(f"❌ Недостаточно 🍙! Нужно {price}", show_alert=True)returnupdate_field(user_id, "users", "rice", data["rice"] - price)update_field(user_id, "users", "current_title", title_name)await callback.answer(f"🎉 Поздравляем! Твой новый титул: {title_name}", show_alert=True)await shop_titles_callback(callback)@dp.callback_query(F.data == "menu_games")async def games_menu_callback(callback: types.CallbackQuery):await callback.message.edit_text("🎮 ИГРОВОЙ ЦЕНТР РИСОВОЙ ИМПЕРИИ\n\n🎪 Здесь ты можешь испытать удачу и заработать кучу 🍙 и XP!\n\n📜 Доступные команды в чате:\n🎰 /casino [ставка] — классический автомат 50/50\n🎲 /dice [ставка] [1-6] — угадай число кубика (x5 призов!)\n📊 /trade [ставка] [вверх/вниз] — угадай курс риса\n⚔️ /duel [ID игрока] [ставка] — вызвать соперника на дуэль\n🎯 /darts [ID игрока] [ставка] — соревнование по дартсу\n🌾 /work — отправиться работать на плантации\n🥷 /rob [ID игрока] — попробовать ограбить богача\n\n👇 А также эксклюзивное колесо удачи: ",parse_mode="Markdown",reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text="🎡 Крутить Рулетку", callback_data="play_roulette")],[types.InlineKeyboardButton(text="🔙 Главное Меню", callback_data="to_main")]]))await callback.answer()@dp.callback_query(F.data == "play_roulette")async def roulette_process(callback: types.CallbackQuery):user_id = callback.from_user.iddata = get_user_data(user_id)if not data: returnnow = int(time.time())is_vip = data["vip_until"] > nowprice = 0 if is_vip else 500if not is_vip and data["rice"] < price:await callback.answer("❌ Обычная рулетка стоит 500 🍙! У тебя нет столько средств.", show_alert=True)returnif not is_vip:update_field(user_id, "users", "rice", data["rice"] - price)win_type = random.choice(["rice", "xp", "lose"])if win_type == "rice":amount = random.randint(100, 2500)update_field(user_id, "users", "rice", get_user_data(user_id)["rice"] + amount)msg = f"🎉 УДАЧА! Колесо остановилось на мешке с рисом! Награда: +{amount} 🍙"elif win_type == "xp":amount = random.randint(20, 60)xp_msg = add_xp(user_id, amount)msg = f"⚡ ОПЫТ! Колесо начислило тебе очки активности! {xp_msg}"else:msg = "😢 НЕ ПОВЕЗЛО! Стрелка остановилась на пустом поле. Попробуй еще раз!"await callback.message.edit_text(f"🎡 КОЛЕСО УДАЧИ\n\n{msg}",parse_mode="Markdown",reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text="🎡 Крутить снова", callback_data="play_roulette")],[types.InlineKeyboardButton(text="🔙 В меню игр", callback_data="menu_games")]]))await callback.answer()@dp.message(Command("casino"))async def cmd_casino(message: types.Message):user_id = message.from_user.iddata = get_user_data(user_id)if not data: returnargs = message.text.split()if len(args) < 2 or not args[1].isdigit():await message.answer("🎰 Укажи ставку! Пример: /casino 50", parse_mode="Markdown")returnbet = int(args[1])if bet <= 0 or data["rice"] < bet:await message.answer("❌ Неверная ставка или у тебя нет столько 🍙!")returnif random.choice([True, False]):update_field(user_id, "users", "rice", data["rice"] + bet)xp_msg = add_xp(user_id, random.randint(2, 8))await message.answer(f"🎰 ПОБЕДА! Твоя ставка сыграла. Получено +{bet} 🍙{xp_msg}", parse_mode="Markdown")else:update_field(user_id, "users", "rice", data["rice"] - bet)await message.answer(f"🎰 ПРОИГРЫШ! Автомат забрал твои {bet} 🍙. Не унывай!")@dp.message(Command("dice"))async def cmd_dice(message: types.Message):user_id = message.from_user.iddata = get_user_data(user_id)if not data: returnargs = message.text.split()if len(args) < 3 or not args[1].isdigit() or not args[2].isdigit():await message.answer("🎲 Правильный формат: /dice [ставка] [число от 1 до 6]", parse_mode="Markdown")returnbet = int(args[1])guess = int(args[2])if bet <= 0 or data["rice"] < bet or guess < 1 or guess > 6:await message.answer("❌ Ошибка в ставке или числе (нужно от 1 до 6)!")returnbot_dice = random.randint(1, 6)if guess == bot_dice:win = bet * 5update_field(user_id, "users", "rice", data["rice"] + win)xp_msg = add_xp(user_id, random.randint(5, 15))await message.answer(f"🎲 ДЖЕКПОТ! Выпало число {bot_dice}! Ты угадал и забрал +{win} 🍙 (x5 к ставке)!{xp_msg}", parse_mode="Markdown")else:update_field(user_id, "users", "rice", data["rice"] - bet)await message.answer(f"🎲 МИМО! Выпало число {bot_dice}, а ты ставил на {guess}. Ставка {bet} 🍙 потеряна.")@dp.message(Command("trade"))async def cmd_trade(message: types.Message):user_id = message.from_user.iddata = get_user_data(user_id)if not data: returnargs = message.text.split()if len(args) < 3 or not args[1].isdigit() or args[2].lower() not in ["вверх", "вниз"]:await message.answer("📊 Формат биржи: /trade [ставка] [вверх / вниз]", parse_mode="Markdown")returnbet = int(args[1])direction = args[2].lower()if bet <= 0 or data["rice"] < bet:await message.answer("❌ Проблема со ставкой!")returnmarket = random.choice(["вверх", "вниз"])if direction == market:update_field(user_id, "users", "rice", data["rice"] + bet)xp_msg = add_xp(user_id, random.randint(3, 9))await message.answer(f"📈 БИРЖА РИСА: Курс пошел {market}! Прогноз верный: +{bet} 🍙{xp_msg}", parse_mode="Markdown")else:update_field(user_id, "users", "rice", data["rice"] - bet)await message.answer(f"📉 БИРЖА РИСА: Курс резко пошел {market}. Твоя сделка в -{bet} 🍙 закрылась в минус.")@dp.message(Command("work"))async def cmd_work(message: types.Message):user_id = message.from_user.iddata = get_user_data(user_id)if not data: returnnow = int(time.time())if now - data["last_work"] < 7200:rem = 7200 - (now - data["last_work"])await message.answer(f"⏳ Твоя спина ещё болит от прошлой смены! Отдыхать осталось {rem // 60} мин.")returnearned = random.randint(150, 400)xp_earned = random.randint(5, 12)update_field(user_id, "users", "rice", data["rice"] + earned)update_field(user_id, "users", "last_work", now)xp_msg = add_xp(user_id, xp_earned)texts = [f"🌾 Ты по колено в грязи собирал рис на плантациях... Заработано +{earned} 🍙!{xp_msg}",f"🚜 Ты весь день чинил сломанный трактор, но хозяин щедро заплатил: +{earned} 🍙!{xp_msg}",f"🧺 Ты упаковывал мешки риса на экспорт. Твой труд вознагражден: +{earned} 🍙!{xp_msg}"]await message.answer(random.choice(texts), parse_mode="Markdown")@dp.message(Command("rob"))async def cmd_rob(message: types.Message):user_id = message.from_user.iddata = get_user_data(user_id)if not data: returnargs = message.text.split()if len(args) < 2 or not args[1].isdigit():await message.answer("🥷 Кого грабим? Напиши ID игрока: /rob [ID]")returntarget_id = int(args[1])target_data = get_user_data(target_id)if not target_data or target_id == user_id:await message.answer("❌ Такой игрок не найден в базе Империи!")returnnow = int(time.time())if now - data["last_rob"] < 14400:await message.answer("❌ Полиция всё ещё ищет тебя! Снизь активность на пару часов.")returnif target_data["amulet"] > 0:update_field(target_id, "inventory", "amulet", target_data["amulet"] - 1)straf = int(data["rice"] * 0.15)update_field(user_id, "users", "rice", data["rice"] - straf)update_field(target_id, "users", "rice", target_data["rice"] + straf)update_field(user_id, "users", "last_rob", now)await message.answer(f"🛡 ОХРАНА! У игрока был активирован Амулет от воров! Твой план провалился, ты пойман и выплатил штраф жертве: -{straf} 🍙.")returnif random.random() < 0.40:stolen = int(target_data["rice"] * random.uniform(0.1, 0.3))if stolen <= 0: stolen = 10update_field(user_id, "users", "rice", data["rice"] + stolen)update_field(target_id, "users", "rice", target_data["rice"] - stolen)update_field(user_id, "users", "last_rob", now)await message.answer(f"🥷 УСПЕШНЫЙ НАЛЕТ! Ты тихо пробрался на склады {target_data['nickname']} и украл +{stolen} 🍙!", parse_mode="Markdown")else:straf = random.randint(200, 1000)if data["rice"] < straf: straf = data["rice"]update_field(user_id, "users", "rice", data["rice"] - straf)update_field(user_id, "users", "last_rob", now)await message.answer(f"🥷 ПРОФАН! Тебя поймали с поличным при попытке ограбления. Пришлось отдать страже штраф: -{straf} 🍙.")@dp.message(Command("duel"))async def cmd_duel(message: types.Message):user_id = message.from_user.iddata = get_user_data(user_id)if not data: returnargs = message.text.split()if len(args) < 3 or not args[1].isdigit() or not args[2].isdigit():await message.answer("⚔️ Бросить вызов: /duel [ID оппонента] [ставка]")returntarget_id = int(args[1])bet = int(args[2])target_data = get_user_data(target_id)if not target_data or target_id == user_id or bet <= 0 or data["rice"] < bet or target_data["rice"] < bet:await message.answer("❌ Ошибка! Неверный ID или у кого-то из вас не хватает 🍙 для ставки.")returnp1_text = data["nickname"]p2_text = target_data["nickname"]fight_scenarios = [f"⚔️ ДУЭЛЬ! {p1_text} забросал соперника гнилым рисом... Но {p2_text} ловко увернулся и нанес сокрушительный удар мешком зерна!",f"⚔️ ДУЭЛЬ! {p2_text} поскользнулся на рисовом зернышке, и {p1_text} мгновенно обезоружил его точным выпадом!"]await message.answer("⚔️ Скрещиваются рисовые мечи, бой начался...")await asyncio.sleep(2)if random.choice([True, False]):update_field(user_id, "users", "rice", data["rice"] + bet)update_field(target_id, "users", "rice", target_data["rice"] - bet)update_field(user_id, "users", "wins", data["wins"] + 1)update_field(target_id, "users", "losses", target_data["losses"] + 1)xp_msg = add_xp(user_id, random.randint(10, 20))await message.answer(f"{random.choice(fight_scenarios)}\n\n🏆 Победитель: {p1_text}! Куш: +{bet} 🍙{xp_msg}", parse_mode="Markdown")else:update_field(user_id, "users", "rice", data["rice"] - bet)update_field(target_id, "users", "rice", target_data["rice"] + bet)update_field(user_id, "users", "losses", data["losses"] + 1)update_field(target_id, "users", "wins", target_data["wins"] + 1)xp_msg = add_xp(target_id, random.randint(10, 20))await message.answer(f"{random.choice(fight_scenarios)}\n\n🏆 Победитель: {p2_text}! Куш: +{bet} 🍙", parse_mode="Markdown")@dp.message(Command("darts"))async def cmd_darts(message: types.Message):await cmd_duel(message)async def main():init_db()print("🚀 Рисовая Империя успешно запущена и готова к заливке на GitHub!")await dp.start_polling(bot)if name == "main":asyncio.run(main())