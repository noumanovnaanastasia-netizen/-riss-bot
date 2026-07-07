import asyncio
import sqlite3
import random
import time
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

# --- СЕРДЦЕ БОТА: ГЛАВНЫЕ НАСТРОЙКИ ---
TOKEN = "8962500881:AAGpPIMnGIZQErV2gI7kXDKxzE6UPchoDbw"  # 👈 Вставь сюда токен от @BotFather
ADMIN_IDS = [7303801260]   # 👈 Замени 123456789 на свой реальный Telegram ID

bot = Bot(token=TOKEN)
dp = Dispatcher()
router = Router()

# --- СОСТОЯНИЯ ДЛЯ РЕГИСТРАЦИИ И МИНИ-ИГР ---
class GameStates(StatesGroup):
    wait_nickname = State()
    wait_detective = State()

# --- ПОДКЛЮЧЕНИЕ И НАСТРОЙКА БАЗЫ ДАННЫХ ---
conn = sqlite3.connect("game.db", check_same_thread=False)
cursor = conn.cursor()

# Создаем единую таблицу пользователей со всеми необходимыми полями
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    tg_id INTEGER PRIMARY KEY,
    nickname TEXT,
    money INTEGER DEFAULT 0,
    level INTEGER DEFAULT 0,
    xp INTEGER DEFAULT 0,
    job TEXT DEFAULT 'Безработный',
    job_start_time INTEGER DEFAULT 0,
    house TEXT DEFAULT 'Бомж 🪵',
    business TEXT DEFAULT 'Нет бизнеса',
    vip_days INTEGER DEFAULT 0,
    title TEXT DEFAULT 'Нет титула',
    is_banned INTEGER DEFAULT 0
)
""")
conn.commit()

print("Часть 1 успешно загружена. База данных создана и проверена!")
# --- КЛАВИАТУРА ГЛАВНОГО МЕНЮ (Reply-кнопки внизу экрана) ---
def get_main_menu():
    kb = [
        [KeyboardButton(text="👤 Профиль"), KeyboardButton(text="💼 Работа")],
        [KeyboardButton(text="🏠 Недвижимость"), KeyboardButton(text="📊 Бизнес")],
        [KeyboardButton(text="🎲 Мини-игры"), KeyboardButton(text="🛒 Магазин")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

# --- ПРОГРЕССИВНАЯ СЕТКА ОПЫТА (Твоя формула расчета) ---
def get_required_xp(level: int) -> int:
    if level < 10:
        return 50
    elif level < 20:
        return 100
    elif level < 30:
        return 150
    elif level < 40:
        return 200
    elif level < 50:
        return 250
    else:
        return 300

# --- КОМАНДА /RULES (ПРАВИЛА ИГРЫ) ---
@router.message(Command("rules"))
async def cmd_rules(message: Message):
    # Фильтр бана: если игрок заблокирован, правила ему тоже не показываем
    user_id = message.from_user.id
    cursor.execute("SELECT is_banned FROM users WHERE tg_id = ?", (user_id,))
    res = cursor.fetchone()
    if res and res[0] == 1:
        await message.answer("⛔ **ДОСТУП ОГРАНИЧЕН** ⛔\n\nВы были заблокированы администрацией за нарушение правил игры!")
        return

    rules_text = (
        "📖 **ПРАВИЛА ИГРЫ «МИНИ-ЖИЗНЬ»**\n\n"
        "1. 👶 **Рождение:** Игра начинается с 0 лет. Придумай крутой никнейм при старте!\n"
        "2. 💼 **Работа:** Устраивайся на работу через «Центр занятости». Чтобы сменить профессию, сначала нажми кнопку «Уволися».\n"
        "3. ⏳ **Смены:** Не забывай вовремя завершать смены, чтобы забирать баксы и опыт (XP).\n"
        "4. 📈 **Прокачка:** Накапливай XP, чтобы расти по годам жизни. Чем ты старше — тем круче доступные работы и бизнесы!\n"
        "5. 🏠 **Пассивный доход:** Покупай жилье, чтобы умножать весь свой доход, и открывай бизнесы, которые приносят баксы автоматически.\n"
        "6. 🎲 **Риск:** Играй в мини-игры с умом. Используй Счастливые амулеты и Страховые полисы из магазина.\n\n"
        "⛔ **Запрещено:** Использование багов и накрутка баланса. За нарушение — бан персонажа!"
    )
    await message.answer(rules_text, parse_mode="Markdown")

print("Часть 2 успешно загружена. Главное меню и формула опыта готовы!")
# --- КОМАНДА /START И ПРОВЕРКА РЕГИСТРАЦИИ ---
@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    
    # Проверяем, не забанен ли пользователь
    cursor.execute("SELECT is_banned FROM users WHERE tg_id = ?", (user_id,))
    ban_res = cursor.fetchone()
    if ban_res and ban_res[0] == 1:
        await message.answer("⛔ **ДОСТУП ОГРАНИЧЕН** ⛔\n\nВы были заблокированы администрацией за нарушение правил игры!")
        return
        
    # Ищем игрока в базе
    cursor.execute("SELECT nickname FROM users WHERE tg_id = ?", (user_id,))
    user = cursor.fetchone()
    
    if user is None:
        # Если игрока нет, запускаем процесс ввода никнейма (FSM состояние)
        await message.answer("👶 **Добро пожаловать в «Мини-Жизнь»!**\n\nВы только что родились в этом виртуальном мире. Пожалуйста, введите ваш будущий игровой никнейм (от 2 до 20 символов):", parse_mode="Markdown")
        await state.set_state(GameStates.wait_nickname)
    else:
        # Если игрок уже есть, выдаем главное меню
        await message.answer(f"👋 **С возвращением, {user[0]}!** Рады видеть вас в игре. Чем займемся сегодня?", reply_markup=get_main_menu(), parse_mode="Markdown")

# --- ОБРАБОТКА ВВОДА НИКНЕЙМА ---
@router.message(GameStates.wait_nickname)
async def process_nickname(message: Message, state: FSMContext):
    user_id = message.from_user.id
    nickname = message.text.strip()
    
    # Валидация длины имени персонажа
    if len(nickname) < 2 or len(nickname) > 20:
        await message.answer("❌ Никнейм должен содержать от 2 до 20 символов. Пожалуйста, попробуйте другой вариант:")
        return
        
    # Заносим нового игрока в базу данных с начальными параметрами
    cursor.execute(
        "INSERT INTO users (tg_id, nickname) VALUES (?, ?)",
        (user_id, nickname)
    )
    conn.commit()
    
    # Сбрасываем ожидание ввода текста
    await state.clear()
    await message.answer(
        f"🎉 **Ура! Ваш игровой паспорт успешно создан!**\n\nДобро пожаловать во взрослую жизнь, **{nickname}**! Используйте кнопки внизу экрана, чтобы управлять своей судьбой.",
        reply_markup=get_main_menu(),
        parse_mode="Markdown"
    )

# --- КНОПКА «👤 ПРОФИЛЬ» (ПАСПОРТ ГРАЖДАНИНА) ---
@router.message(F.text == "👤 Профиль")
async def show_profile(message: Message):
    user_id = message.from_user.id
    
    # Фильтр бана
    cursor.execute("SELECT is_banned FROM users WHERE tg_id = ?", (user_id,))
    ban_res = cursor.fetchone()
    if ban_res and ban_res[0] == 1:
        await message.answer("⛔ **ДОСТУП ОГРАНИЧЕН** ⛔\n\nВы были заблокированы администрацией за нарушение правил игры!")
        return
        
    cursor.execute("SELECT nickname, money, level, xp, job, house, business, vip_days, title FROM users WHERE tg_id = ?", (user_id,))
    user = cursor.fetchone()
    
    if user is None:
        await message.answer("❌ Вы еще не зарегистрированы в игре! Напишите /start для создания персонажа.")
        return
        
    nickname, money, level, xp, job, house, business, vip_days, title = user
    req_xp = get_required_xp(level)
    
    # Красивое отображение VIP статуса
    vip_status = f"⭐ Активен ({vip_days} дн.)" if vip_days > 0 else "Нет VIP-статуса ❌"
    
    profile_text = (
        f"📋 **ПАСПОРТ ГРАЖДАНИНА** 📋\n\n"
        f"👤 **Никнейм:** {nickname}\n"
        f"🏅 **Звание:** {title}\n"
        f"🎂 **Возраст (Уровень):** {level} лет\n"
        f"📊 **Опыт (XP):** {xp}/{req_xp}\n"
        f"💵 **Баланс:** ${money:,}\n\n"
        f"👔 **Работа:** {job}\n"
        f"🏠 **Жилье:** {house}\n"
        f"💼 **Бизнес:** {business}\n"
        f"👑 **VIP-статус:** {vip_status}"
    )
    await message.answer(profile_text, parse_mode="Markdown")

print("Часть 3 успешно загружена. Система профилей и приветствия работает!")
# --- СПИСОК ВСЕХ РАБОТ (КОНФИГУРАЦИЯ БАЛАНСА) ---
# Структура: ID: {"name": Название, "level": Нужный возраст, "time": Время в сек, "money": Доход, "xp": Опыт}
JOBS_DATA = {
    "leaflets": {"name": "🍏 Расклейщик листовок", "level": 0, "time": 180, "money": 120, "xp": 15},
    "warehouse": {"name": "📦 Сортировщик на складе", "level": 0, "time": 360, "money": 250, "xp": 25},
    "kitchen": {"name": "🍔 Помощник на кухне", "level": 0, "time": 600, "money": 450, "xp": 45},
    "courier": {"name": "🚴 Курьер на самокате", "level": 5, "time": 1200, "money": 1200, "xp": 70},
    "windows": {"name": "🧼 Мойщик окон", "level": 5, "time": 1500, "money": 1800, "xp": 95},
    "barista": {"name": "☕ Бариста в кофейне", "level": 14, "time": 2700, "money": 4500, "xp": 120},
    "tester": {"name": "👨‍💻 Тестировщик игр", "level": 14, "time": 3600, "money": 6500, "xp": 160},
    "coder": {"name": "💻 Младший кодер", "level": 21, "time": 5400, "money": 15000, "xp": 250},
    "sales": {"name": "📈 Менеджер по продажам", "level": 21, "time": 4320, "money": 22000, "xp": 350},
    "director": {"name": "🏢 Директор филиала", "level": 30, "time": 5400, "money": 65000, "xp": 500},
    "banker": {"name": "🏦 Управляющий банком", "level": 30, "time": 7200, "money": 90000, "xp": 700},
    "investor": {"name": "👑 Инвестор-советник", "level": 45, "time": 10800, "money": 250000, "xp": 1500},
    "mentor": {"name": "🧙‍♂️ Верховный Наставник", "level": 60, "time": 14400, "money": 850000, "xp": 3500}
}

# --- КНОПКА «💼 РАБОТА» (БИРЖА ТРУДА) ---
@router.message(F.text == "💼 Работа")
async def show_job_menu(message: Message):
    user_id = message.from_user.id
    
    # Проверяем бан
    cursor.execute("SELECT is_banned FROM users WHERE tg_id = ?", (user_id,))
    ban_res = cursor.fetchone()
    if ban_res and ban_res == 1:
        await message.answer("⛔ **ДОСТУП ОГРАНИЧЕН** ⛔\n\nВы были заблокированы администрацией за нарушение правил игры!")
        return
        
    cursor.execute("SELECT job, job_start_time, level FROM users WHERE tg_id = ?", (user_id,))
    user = cursor.fetchone()
    
    if user is None:
        await message.answer("❌ Вы не зарегистрированы! Напишите /start")
        return
        
    current_job, job_start_time, level = user
    inline_kb = []
    
    if current_job == "Безработный":
        status_text = "💼 Сейчас вы **Безработный**.\n\nЗагляните в Центр занятости, чтобы устроиться на свою первую работу и начать зарабатывать баксы!"
        inline_kb.append([InlineKeyboardButton(text="🏢 Центр занятости", callback_data="job_vacancy_list")])
    else:
        # Пытаемся найти ID текущей работы по ее названию
        job_id = None
        for j_id, j_info in JOBS_DATA.items():
            if j_info["name"] == current_job:
                job_id = j_id
                break
                
        if job_id:
            job_info = JOBS_DATA[job_id]
            if job_start_time == 0:
                status_text = f"👔 Ваша текущая должность: **{current_job}**.\n\nВы готовы выйти на рабочую смену? Нажмите кнопку ниже, чтобы запустить таймер!"
                inline_kb.append([InlineKeyboardButton(text="🚀 Начать смену", callback_data=f"job_start_{job_id}")])
            else:
                elapsed_time = int(time.time()) - job_start_time
                remaining_time = job_info["time"] - elapsed_time
                
                if remaining_time > 0:
                    mins = remaining_time // 60
                    secs = remaining_time % 60
                    status_text = f"⏳ Вы усердно трудитесь на должности:\n**{current_job}**.\n\nДо конца смены осталось: **{mins} мин. {secs} сек.**"
                    inline_kb.append([InlineKeyboardButton(text="🔄 Обновить время", callback_data="job_refresh")])
                else:
                    status_text = f"🎉 Отличные новости! Ваша смена на должности **{current_job}** официально завершена.\n\nПора забрать свои баксы и опыт!"
                    inline_kb.append([InlineKeyboardButton(text="💰 Забрать зарплату", callback_data=f"job_finish_{job_id}")])
                    
        # Кнопка увольнения доступна всегда, когда есть работа
        inline_kb.append([InlineKeyboardButton(text="❌ Уволиться с работы", callback_data="job_resign")])
        
    reply_markup = InlineKeyboardMarkup(inline_keyboard=inline_kb)
    await message.answer(status_text, reply_markup=reply_markup, parse_mode="Markdown")
# --- ОТКРЫТИЕ СПИСКА ДОСТУПНЫХ ВАКАНСИЙ ---
@router.callback_query(F.data == "job_vacancy_list")
async def show_vacancies(callback: CallbackQuery):
    user_id = callback.from_user.id
    cursor.execute("SELECT level, job FROM users WHERE tg_id = ?", (user_id,))
    level, current_job = cursor.fetchone()
    
    if current_job != "Безработный":
        await callback.answer("❌ Нельзя устроиться! Сначала вручную нажмите кнопку «Уволиться».", show_alert=True)
        return
        
    text = "🏢 **ЦЕНТР ЗАНЯТОСТИ** 🏢\n\nДоступные вакансии для вашего текущего возраста:\n"
    inline_kb = []
    
    for j_id, j_info in JOBS_DATA.items():
        time_text = f"{j_info['time'] // 60} мин" if j_info['time'] >= 60 else f"{j_info['time']} сек"
        if level >= j_info["level"]:
            text += f"\n✅ **{j_info['name']}**\n└ Время: {time_text} | ЗП: ${j_info['money']:,} | +{j_info['xp']} XP\n"
            inline_kb.append([InlineKeyboardButton(text=f"Устроиться: {j_info['name']}", callback_data=f"job_take_{j_id}")])
        else:
            text += f"\n🔒 *{j_info['name']}* (Доступно с {j_info['level']} лет)\n"
            
    inline_kb.append([InlineKeyboardButton(text="🔙 Назад", callback_data="job_refresh")])
    reply_markup = InlineKeyboardMarkup(inline_keyboard=inline_kb)
    
    await callback.message.edit_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    await callback.answer()

# --- ОБРАБОТКА ДЕЙСТВИЙ РАБОТЫ ---
@router.callback_query(F.data.startswith("job_"))
async def process_job_callback(callback: CallbackQuery):
    user_id = callback.from_user.id
    action = callback.data.split("_")
    
    # 1. Обновление меню / кнопка Назад
    if action[1] == "refresh":
        await show_job_menu(callback.message)
        await callback.answer()
        
    # 2. Ручное увольнение (Очищает должность и обнуляет таймер)
    elif action[1] == "resign":
        cursor.execute("UPDATE users SET job = 'Безработный', job_start_time = 0 WHERE tg_id = ?", (user_id,))
        conn.commit()
        await callback.answer("❌ Вы успешно уволились! Теперь вы безработный.", show_alert=True)
        await show_job_menu(callback.message)
        
    # 3. Устройство на выбранную должность
    elif action[1] == "take":
        job_id = action[2]
        job_info = JOBS_DATA[job_id]
        
        cursor.execute("UPDATE users SET job = ?, job_start_time = 0 WHERE tg_id = ?", (job_info["name"], user_id))
        conn.commit()
        await callback.answer(f"🎉 Вы успешно приняты на должность: {job_info['name']}!")
        await show_job_menu(callback.message)
        
    # 4. Старт рабочей смены
    elif action[1] == "start":
        current_time = int(time.time())
        cursor.execute("UPDATE users SET job_start_time = ? WHERE tg_id = ?", (current_time, user_id))
        conn.commit()
        await callback.answer("🚀 Смена начата! Время пошло.", show_alert=True)
        await show_job_menu(callback.message)
        
    # 5. Завершение смены, расчет зарплаты, множителей и опыта
    elif action[1] == "finish":
        job_id = action[2]
        job_info = JOBS_DATA[job_id]
        
        cursor.execute("SELECT job_start_time, money, xp, level, house, title FROM users WHERE tg_id = ?", (user_id,))
        job_start_time, current_money, current_xp, current_level, house, title = cursor.fetchone()
        
        elapsed_time = int(time.time()) - job_start_time
        if elapsed_time < job_info["time"]:
            await callback.answer("❌ Рановато! Вы еще не отработали положенное время.", show_alert=True)
            return
            
        # Рассчитываем множитель недвижимости
        multiplier = 1.0
        if "хостеле" in house: multiplier = 1.1
        elif "студия" in house: multiplier = 1.25
        elif "двушки" in house: multiplier = 1.4
        elif "дома" in house: multiplier = 1.65
        elif "особняка" in house: multiplier = 2.0
        elif "пентхауса" in house: multiplier = 2.5
        
        # Дополнительный бонус +5% к ЗП за звание [Менеджер] из кейсов
        title_bonus = 1.0
        if title == "[Менеджер]":
            title_bonus = 1.05
            
        final_money = int(job_info["money"] * multiplier * title_bonus)
        new_money = current_money + final_money
        new_xp = current_xp + job_info["xp"]
        
        # Расчет повышения «годов жизни» по твоей сетке опыта
        req_xp = get_required_xp(current_level)
        leveled_up = False
        
        while new_xp >= req_xp:
            new_xp -= req_xp
            current_level += 1
            req_xp = get_required_xp(current_level)
            leveled_up = True
            
        # Обнуляем job_start_time, чтобы можно было работать снова
        cursor.execute(
            "UPDATE users SET money = ?, xp = ?, level = ?, job_start_time = 0 WHERE tg_id = ?",
            (new_money, new_xp, current_level, user_id)
        )
        conn.commit()
        
        congratulations = (
            f"💰 **СМЕНА УСПЕШНО ЗАВЕРШЕНА!** 💰\n\n"
            f"💵 Заработано: **${final_money:,}** (Жилье: x{multiplier})\n"
            f"📈 Получено опыта: **+{job_info['xp']} XP**"
        )
        if leveled_up:
            congratulations += f"\n\n🎉 **УРА! ВЫ ПОВЗРОСЛЕЛИ!** 🎉\nТеперь ваш возраст составляет: **{current_level} лет**! Открылись новые возможности."
            
        await callback.message.answer(congratulations, parse_mode="Markdown")
        await show_job_menu(callback.message)
        await callback.answer()
# --- СПИСОК ВСЕЙ НЕДВИЖИМОСТИ (КОНФИГУРАЦИЯ БАЛАНСА) ---
# Структура: ID: {"name": Название, "price": Стоимость, "mult": Множитель, "status": Текст для базы}
HOUSES_DATA = {
    "hostel": {"name": "🛏️ Место в хостеле", "price": 1500, "mult": 1.1, "status": "Житель хостела 🏨"},
    "studio": {"name": "🔑 Студия на окраине", "price": 12000, "mult": 1.25, "status": "Своя студия 🏢"},
    "two_room": {"name": "🚪 Двухкомнатная квартира", "price": 45000, "mult": 1.4, "status": "Обладатель двушки 🏙️"},
    "cottage": {"name": "🏡 Загородный коттедж", "price": 180000, "mult": 1.65, "status": "Владелец дома 🌳"},
    "mansion": {"name": "🏰 Огромный особняк", "price": 750000, "mult": 2.0, "status": "Хозяин особняка 🏛️"},
    "penthouse": {"name": "🏙️ Пентхаус в Сити", "price": 3500000, "mult": 2.5, "status": "Владелец пентхауса 💎"}
}

# --- КНОПКА «🏠 НЕДВИЖИМОСТЬ» (ГЛАВНОЕ МЕНЮ ЖИЛЬЯ) ---
@router.message(F.text == "🏠 Недвижимость")
async def show_house_menu(message: Message):
    user_id = message.from_user.id
    
    # Проверяем бан
    cursor.execute("SELECT is_banned FROM users WHERE tg_id = ?", (user_id,))
    ban_res = cursor.fetchone()
    if ban_res and ban_res == 1:
        await message.answer("⛔ **ДОСТУП ОГРАНИЧЕН** ⛔\n\nВы были заблокированы администрацией за нарушение правил игры!")
        return
        
    cursor.execute("SELECT house, title FROM users WHERE tg_id = ?", (user_id,))
    user = cursor.fetchone()
    
    if user is None:
        await message.answer("❌ Вы не зарегистрированы! Напишите /start")
        return
        
    current_house, title = user
    
    # Рассчитываем текущий множитель для вывода на экран
    current_mult = 1.0
    for h_info in HOUSES_DATA.values():
        if h_info["status"] == current_house:
            current_mult = h_info["mult"]
            break
            
    text = (
        f"🏠 **ВАШ ЖИЛИЩНЫЙ СТАТУС** 🏠\n\n"
        f"📍 Текущее жилье: **{current_house}**\n"
        f"📈 Множитель всего дохода: **x{current_mult}**\n\n"
        f"Хотите переехать в место получше и поднять свои доходы на работе? Загляните в наше агентство недвижимости!"
    )
    
    inline_kb = [[InlineKeyboardButton(text="🏢 Риелторское агентство", callback_data="house_market")]]
    reply_markup = InlineKeyboardMarkup(inline_keyboard=inline_kb)
    await message.answer(text, reply_markup=reply_markup, parse_mode="Markdown")

# --- ПОКАЗ МАГАЗИНА НЕДВИЖИМОСТИ ---
@router.callback_query(F.data == "house_market")
async def show_house_market(callback: CallbackQuery):
    user_id = callback.from_user.id
    cursor.execute("SELECT house, title FROM users WHERE tg_id = ?", (user_id,))
    current_house, title = cursor.fetchone()
    
    text = "🏢 **АГЕНТСТВО НЕДВИЖИМОСТИ** 🏢\n\nПокупка элитного жилья навсегда увеличивает твой активный доход на работе!\n"
    inline_kb = []
    
    for h_id, h_info in HOUSES_DATA.items():
        # Скидка 5% для титулов из кейса Средняк
        discount = 1.0
        if title in ["[Стильный]", "[Красавчик]"]:
            discount = 0.95
            
        final_price = int(h_info["price"] * discount)
        discount_text = " *(Скидка 5% за титул!)*" if discount < 1.0 else ""
        
        if h_info["status"] == current_house:
            text += f"\n🏠 **{h_info['name']}**\n└ 🎖️ **КУПЛЕНО** | Множитель: x{h_info['mult']}\n"
        else:
            text += f"\n🛒 **{h_info['name']}**\n└ Цена: ${final_price:,}{discount_text} | Множитель: x{h_info['mult']}\n"
            inline_kb.append([InlineKeyboardButton(text=f"Купить: {h_info['name']}", callback_data=f"house_buy_{h_id}")])
            
    inline_kb.append([InlineKeyboardButton(text="🔙 Назад в меню", callback_data="house_refresh")])
    reply_markup = InlineKeyboardMarkup(inline_keyboard=inline_kb)
    
    await callback.message.edit_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    await callback.answer()

# --- ОБРАБОТКА ПОКУПКИ ЖИЛЬЯ ---
@router.callback_query(F.data.startswith("house_"))
async def process_house_callback(callback: CallbackQuery):
    user_id = callback.from_user.id
    action = callback.data.split("_")
    
    if action[1] == "refresh":
        await show_house_menu(callback.message)
        await callback.answer()
        return
        
    if action[1] == "buy":
        house_id = action[2]
        house_info = HOUSES_DATA[house_id]
        
        cursor.execute("SELECT money, house, title FROM users WHERE tg_id = ?", (user_id,))
        money, current_house, title = cursor.fetchone()
        
        if current_house == house_info["status"]:
            await callback.answer("❌ У вас уже куплено это жилье!", show_alert=True)
            return
            
        # Применяем скидку 5% при проверке баланса за нужные титулы
        discount = 1.0
        if title in ["[Стильный]", "[Красавчик]"]:
            discount = 0.95
        final_price = int(house_info["price"] * discount)
        
        if money < final_price:
            await callback.answer(f"❌ Недостаточно баксов! Вам требуется ${final_price:,}", show_alert=True)
            return
            
        # Списываем баксы и обновляем жилье
        new_money = money - final_price
        cursor.execute(
            "UPDATE users SET money = ?, house = ? WHERE tg_id = ?",
            (new_money, house_info["status"], user_id)
        )
        conn.commit()
        
        await callback.answer(f"🎉 Поздравляем! Вы успешно приобрели: {house_info['name']}!", show_alert=True)
        await show_house_market(callback)
# --- СПИСОК ВСЕХ БИЗНЕСОВ (КОНФИГУРАЦИЯ БАЛАНСА) ---
# Структура: ID: {"name": Название, "level": Возраст для покупки, "price": Цена, "income": Доход в минуту}
BUSINESS_DATA = {
    "popcorn": {"name": "🍿 Ларек с попкорном", "level": 10, "price": 5000, "income": 100},
    "coffee": {"name": "☕ Кофейная точка (to-go)", "level": 15, "price": 20000, "income": 350},
    "carwash": {"name": "🧼 Автомойка", "level": 18, "price": 65000, "income": 900},
    "pizza": {"name": "🍕 Сеть пиццерий", "level": 25, "price": 300000, "income": 4500},
    "club": {"name": "🖥️ Компьютерный клуб", "level": 30, "price": 950000, "income": 15000},
    "factory": {"name": "🏭 Завод смартфонов", "level": 35, "price": 2500000, "income": 45000},
    "hotels": {"name": "🏨 Сеть отелей", "level": 45, "price": 8000000, "income": 160000},
    "space": {"name": "🚀 Космическая корпорация", "level": 50, "price": 25000000, "income": 600000}
}

# --- КНОПКА «📊 БИЗНЕС» (ГЛАВНОЕ МЕНЮ БИЗНЕСА) ---
@router.message(F.text == "📊 Бизнес")
async def show_business_menu(message: Message):
    user_id = message.from_user.id
    
    # Проверяем бан
    cursor.execute("SELECT is_banned FROM users WHERE tg_id = ?", (user_id,))
    ban_res = cursor.fetchone()
    if ban_res and ban_res == 1:
        await message.answer("⛔ **ДОСТУП ОГРАНИЧЕН** ⛔\n\nВы были заблокированы администрацией за нарушение правил игры!")
        return
        
    # Поле job_start_time временно хранит метку времени последнего сбора прибыли
    cursor.execute("SELECT business, job_start_time, money, title, house FROM users WHERE tg_id = ?", (user_id,))
    user = cursor.fetchone()
    
    if user is None:
        await message.answer("❌ Вы не зарегистрированы! Напишите /start")
        return
        
    current_business, last_collect_time, money, title, house = user
    inline_kb = []
    
    if current_business == "Нет бизнеса":
        text = "💼 **ВАШ ПАССИВНЫЙ БИЗНЕС** 💼\n\nУ вас пока нет коммерческих предприятий. Вы можете открыть свое первое дело в нашем каталоге!"
        inline_kb.append([InlineKeyboardButton(text="🛒 Каталог бизнесов", callback_data="biz_catalog")])
    else:
        biz_id = None
        for b_id, b_info in BUSINESS_DATA.items():
            if b_info["name"] == current_business:
                biz_id = b_id
                break
                
        if biz_id:
            biz_info = BUSINESS_DATA[biz_id]
            current_time = int(time.time())
            
            if last_collect_time == 0:
                last_collect_time = current_time
                cursor.execute("UPDATE users SET job_start_time = ? WHERE tg_id = ?", (current_time, user_id))
                conn.commit()
                
            elapsed_seconds = current_time - last_collect_time
            elapsed_minutes = elapsed_seconds // 60
            
            # Бонусы за звания
            title_bonus = 1.0
            if title in ["[Бизнесмен]", "[Акула Бизнеса]"]:
                title_bonus = 1.1
            elif title == "[💎 Король Сливок]":
                title_bonus = 1.2
                
            # Бонусы за жилье
            house_multiplier = 1.0
            if "хостеле" in house: house_multiplier = 1.1
            elif "студия" in house: house_multiplier = 1.25
            elif "двушки" in house: house_multiplier = 1.4
            elif "дома" in house: house_multiplier = 1.65
            elif "особняка" in house: house_multiplier = 2.0
            elif "пентхауса" in house: house_multiplier = 2.5
            
            final_income_per_min = int(biz_info["income"] * title_bonus * house_multiplier)
            accumulated_money = elapsed_minutes * final_income_per_min
            
            text = (
                f"💼 **ВАШ ПАССИВНЫЙ БИЗНЕС** 💼\n\n"
                f"🏬 Предприятие: **{current_business}**\n"
                f"💰 Базовый доход: ${biz_info['income']:,} / мин.\n"
                f"📈 С учетом всех бонусов: **${final_income_per_min:,} / мин.**\n\n"
                f"⏳ Накопилось прибыли за {elapsed_minutes} мин:\n**${accumulated_money:,}**"
            )
            
            if accumulated_money > 0:
                inline_kb.append([InlineKeyboardButton(text="💵 Забрать прибыль", callback_data="biz_collect")])
            else:
                inline_kb.append([InlineKeyboardButton(text="🔄 Обновить таймер", callback_data="biz_refresh")])
                
        inline_kb.append([InlineKeyboardButton(text="🛒 Каталог бизнесов", callback_data="biz_catalog")])
        
    reply_markup = InlineKeyboardMarkup(inline_keyboard=inline_kb)
    await message.answer(text, reply_markup=reply_markup, parse_mode="Markdown")
# --- ПОКАЗ КАТАЛОГА ПРЕДПРИЯТИЙ ---
@router.callback_query(F.data == "biz_catalog")
async def show_business_catalog(callback: CallbackQuery):
    user_id = callback.from_user.id
    cursor.execute("SELECT level, business FROM users WHERE tg_id = ?", (user_id,))
    level, current_business = cursor.fetchone()
    
    text = "🏬 **КАТАЛОГ ПРЕДПРИЯТИЙ** 🏬\n\nПокупка нового бизнеса автоматически заменяет старый. Деньги капают каждую минуту!\n"
    inline_kb = []
    
    for b_id, b_info in BUSINESS_DATA.items():
        if level >= b_info["level"]:
            if b_info["name"] == current_business:
                text += f"\n📊 **{b_info['name']}**\n└ 🎖️ **ВАШ БИЗНЕС** | Доход: ${b_info['income']:,}/мин.\n"
            else:
                text += f"\n🛒 **{b_info['name']}**\n└ Цена: ${b_info['price']:,} | Доход: ${b_info['income']:,}/мин.\n"
                inline_kb.append([InlineKeyboardButton(text=f"Купить: {b_info['name']}", callback_data=f"biz_buy_{b_id}")])
        else:
            text += f"\n🔒 *{b_info['name']}* (Доступно с {b_info['level']} лет)\n"
            
    inline_kb.append([InlineKeyboardButton(text="🔙 Назад", callback_data="biz_refresh")])
    reply_markup = InlineKeyboardMarkup(inline_keyboard=inline_kb)
    
    await callback.message.edit_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    await callback.answer()

# --- ОБРАБОТКА ДЕЙСТВИЙ БИЗНЕСА ---
@router.callback_query(F.data.startswith("biz_"))
async def process_business_callback(callback: CallbackQuery):
    user_id = callback.from_user.id
    action = callback.data.split("_")
    
    if action[1] == "refresh":
        await show_business_menu(callback.message)
        await callback.answer()
        return
        
    # Сбор накопленной пассивной прибыли
    if action[1] == "collect":
        cursor.execute("SELECT business, job_start_time, money, title, house FROM users WHERE tg_id = ?", (user_id,))
        current_business, last_collect_time, current_money, title, house = cursor.fetchone()
        
        if current_business == "Нет бизнеса" or last_collect_time == 0:
            await callback.answer("❌ У вас нет активного бизнеса!", show_alert=True)
            return
            
        biz_id = None
        for b_id, b_info in BUSINESS_DATA.items():
            if b_info["name"] == current_business:
                biz_id = b_id
                break
                
        if biz_id:
            biz_info = BUSINESS_DATA[biz_id]
            current_time = int(time.time())
            elapsed_minutes = (current_time - last_collect_time) // 60
            
            if elapsed_minutes < 1:
                await callback.answer("❌ Прошло меньше одной минуты с последнего сбора!", show_alert=True)
                return
                
            title_bonus = 1.0
            if title in ["[Бизнесмен]", "[Акула Бизнеса]"]: title_bonus = 1.1
            elif title == "[💎 Король Сливок]": title_bonus = 1.2
            
            house_multiplier = 1.0
            if "хостеле" in house: house_multiplier = 1.1
            elif "студия" in house: house_multiplier = 1.25
            elif "двушки" in house: house_multiplier = 1.4
            elif "дома" in house: house_multiplier = 1.65
            elif "особняка" in house: house_multiplier = 2.0
            elif "пентхауса" in house: house_multiplier = 2.5
            
            final_income = int(biz_info["income"] * title_bonus * house_multiplier)
            total_profit = elapsed_minutes * final_income
            
            new_money = current_money + total_profit
            cursor.execute("UPDATE users SET money = ?, job_start_time = ? WHERE tg_id = ?", (new_money, current_time, user_id))
            conn.commit()
            
            await callback.answer(f"💵 Вы успешно собрали чистую прибыль: +${total_profit:,}!", show_alert=True)
            await show_business_menu(callback.message)
            
    # Покупка бизнеса
    elif action[1] == "buy":
        biz_id = action[2]
        biz_info = BUSINESS_DATA[biz_id]
        
        cursor.execute("SELECT money, business FROM users WHERE tg_id = ?", (user_id,))
        money, current_business = cursor.fetchone()
        
        if current_business == biz_info["name"]:
            await callback.answer("❌ Вы уже владеете этим предприятием!", show_alert=True)
            return
            
        if money < biz_info["price"]:
            await callback.answer(f"❌ Недостаточно баксов! Стоимость бизнеса: ${biz_info['price']:,}", show_alert=True)
            return
            
        new_money = money - biz_info["price"]
        current_time = int(time.time())
        
        cursor.execute(
            "UPDATE users SET money = ?, business = ?, job_start_time = ? WHERE tg_id = ?",
            (new_money, biz_info["name"], current_time, user_id)
        )
        conn.commit()
        
        await callback.answer(f"🎉 Поздравляем! Вы успешно открыли предприятие: {biz_info['name']}!", show_alert=True)
        await show_business_catalog(callback)
# --- ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ ДЛЯ ПОИСКА ИГРОКА (ПО ID ИЛИ НИКНЕЙМУ) ---
def find_user_tg_id(target: str) -> int:
    # Если ввели чистые цифры, значит это Telegram ID
    if target.isdigit():
        return int(target)
    # Иначе ищем игрока в базе данных по его никнейму
    cursor.execute("SELECT tg_id FROM users WHERE nickname = ?", (target,))
    result = cursor.fetchone()
    return result[0] if result else None

# --- КОМАНДА ВЫДАЧИ / ЗАБОРА БАКСОВ ---
# Формат: /givemoney [ID или Никнейм] [Сумма] (чтобы забрать, пиши сумму с минусом)
@router.message(Command("givemoney"))
async def admin_give_money(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
        
    args = message.text.split()
    if len(args) < 3:
        await message.answer("❌ Формат: `/givemoney [ID или Никнейм] [Сумма]` (чтобы забрать, укажи сумму с минусом)", parse_mode="Markdown")
        return
        
    target, amount_str = args[1], args[2]
    target_id = find_user_tg_id(target)
    
    if not target_id:
        await message.answer("❌ Игрок с таким ID или никнеймом не найден в базе данных!")
        return
        
    try:
        amount = int(amount_str)
    except ValueError:
        await message.answer("❌ Сумма должна быть целым числом!")
        return
        
    cursor.execute("SELECT money, nickname FROM users WHERE tg_id = ?", (target_id,))
    user_data = cursor.fetchone()
    current_money, nickname = user_data
    
    new_money = max(0, current_money + amount) # Баланс игрока не может уйти в минус
    cursor.execute("UPDATE users SET money = ? WHERE tg_id = ?", (new_money, target_id))
    conn.commit()
    
    action_text = "выдано" if amount > 0 else "забрано"
    await message.answer(f"✅ Игроку **{nickname}** (ID: {target_id}) {action_text} ${abs(amount):,}.\n💵 Новый баланс: ${new_money:,}", parse_mode="Markdown")

# --- КОМАНДА ВЫДАЧИ / ЗАБОРА ОПЫТА (XP) ---
# Формат: /givexp [ID или Никнейм] [Кол-во XP] (чтобы забрать, пиши с минусом)
@router.message(Command("givexp"))
async def admin_give_xp(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
        
    args = message.text.split()
    if len(args) < 3:
        await message.answer("❌ Формат: `/givexp [ID или Никнейм] [Кол-во XP]`", parse_mode="Markdown")
        return
        
    target, xp_str = args[1], args[2]
    target_id = find_user_tg_id(target)
    
    if not target_id:
        await message.answer("❌ Игрок с таким ID или никнеймом не найден!")
        return
        
    try:
        xp_to_add = int(xp_str)
    except ValueError:
        await message.answer("❌ Количество XP должно быть целым числом!")
        return
        
    cursor.execute("SELECT xp, level, nickname FROM users WHERE tg_id = ?", (target_id,))
    current_xp, current_level, nickname = cursor.fetchone()
    
    new_xp = current_xp + xp_to_add
    leveled_up = False
    
    # Если забираем опыт и уходим в минус ниже нуля
    if new_xp < 0:
        if current_level > 0:
            current_level -= 1
            new_xp = get_required_xp(current_level) + new_xp # Переносим остаток минуса на прошлый уровень
            new_xp = max(0, new_xp)
        else:
            new_xp = 0
            
    # Если выдаем опыт и повышаем «годы жизни» по нашей формуле из Части 2
    req_xp = get_required_xp(current_level)
    while new_xp >= req_xp:
        new_xp -= req_xp
        current_level += 1
        req_xp = get_required_xp(current_level)
        leveled_up = True
        
    cursor.execute("UPDATE users SET xp = ?, level = ? WHERE tg_id = ?", (new_xp, current_level, target_id))
    conn.commit()
    
    status_text = f"✅ Изменен опыт игрока **{nickname}**.\n📊 Новый возраст: **{current_level} лет** | Опыт: **{new_xp}/{req_xp} XP**"
    if leveled_up:
        status_text += "\n🎉 Возраст игрока был успешно увеличен!"
    await message.answer(status_text, parse_mode="Markdown")

# --- КОМАНДА ВЫДАЧИ / ЗАБОРА VIP ---
# Формат: /givevip [ID или Никнейм] [Кол-во дней] (0 — чтобы полностью забрать)
@router.message(Command("givevip"))
async def admin_give_vip(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
        
    args = message.text.split()
    if len(args) < 3:
        await message.answer("❌ Формат: `/givevip [ID или Никнейм] [Дни]` (0 — чтобы полностью забрать)", parse_mode="Markdown")
        return
        
    target, days_str = args[1], args[2]
    target_id = find_user_tg_id(target)
    
    if not target_id:
        await message.answer("❌ Игрок не найден!")
        return
        
    try:
        days = max(0, int(days_str))
    except ValueError:
        await message.answer("❌ Количество дней должно быть целым числом!")
        return
        
    cursor.execute("SELECT nickname FROM users WHERE tg_id = ?", (target_id,))
    nickname = cursor.fetchone()[0]
    
    cursor.execute("UPDATE users SET vip_days = ? WHERE tg_id = ?", (days, target_id))
    conn.commit()
    
    if days > 0:
        await message.answer(f"👑 Игроку **{nickname}** успешно выдан VIP-статус на **{days} дней**!", parse_mode="Markdown")
    else:
        await message.answer(f"❌ У игрока **{nickname}** успешно забран VIP-статус.", parse_mode="Markdown")

# --- СИСТЕМА БАНОВ (БЛОКИРОВКА / РАЗБЛОКИРОВКА) ---
# Команда блокировки: /ban [ID или Никнейм]
@router.message(Command("ban"))
async def admin_ban_user(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
        
    args = message.text.split()
    if len(args) < 2:
        await message.answer("❌ Формат: `/ban [ID или Никнейм]`", parse_mode="Markdown")
        return
        
    target = args[1]
    target_id = find_user_tg_id(target)
    
    if not target_id:
        await message.answer("❌ Игрок не найден!")
        return
        
    if target_id == message.from_user.id:
        await message.answer("❌ Вы не можете заблокировать саму себя!")
        return
        
    cursor.execute("SELECT nickname FROM users WHERE tg_id = ?", (target_id,))
    nickname = cursor.fetchone()[0]
    
    cursor.execute("UPDATE users SET is_banned = 1 WHERE tg_id = ?", (target_id,))
    conn.commit()
    
    await message.answer(f"⛔ Игрок **{nickname}** (ID: {target_id}) успешно **ЗАБЛОКИРОВАН** в игре за нарушения!", parse_mode="Markdown")

# Команда разблокировки: /unban [ID или Никнейм]
@router.message(Command("unban"))
async def admin_unban_user(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
        
    args = message.text.split()
    if len(args) < 2:
        await message.answer("❌ Формат: `/unban [ID или Никнейм]`", parse_mode="Markdown")
        return
        
    target = args[1]
    target_id = find_user_tg_id(target)
    
    if not target_id:
        await message.answer("❌ Игрок не найден!")
        return
        
    cursor.execute("SELECT nickname FROM users WHERE tg_id = ?", (target_id,))
    nickname = cursor.fetchone()[0]
    
    cursor.execute("UPDATE users SET is_banned = 0 WHERE tg_id = ?", (target_id,))
    conn.commit()
    
    await message.answer(f"🔓 Игрок **{nickname}** (ID: {target_id}) успешно **РАЗБЛОКИРОВАН**!", parse_mode="Markdown")
# --- СЛОВАРЬ КУЛДАУНОВ ДЛЯ РУЛЕТКИ ---
ROULETTE_COOLDOWNS = {}

# --- КНОПКА «🎲 МИНИ-ИГРЫ» (МЕНЮ РАЗВЛЕЧЕНИЙ) ---
@router.message(F.text == "🎲 Мини-игры")
async def show_games_menu(message: Message):
    user_id = message.from_user.id
    
    cursor.execute("SELECT is_banned FROM users WHERE tg_id = ?", (user_id,))
    ban_res = cursor.fetchone()
    if ban_res and ban_res[0] == 1:
        await message.answer("⛔ **ДОСТУП ОГРАНИЧЕН**\n\nВы заблокированы!")
        return
        
    text = (
        "🎲 **ЗОНА РАЗВЛЕЧЕНИЙ И АЗАРТА** 🎲\n\n"
        "Испытайте свою удачу или разомните мозги!\n\n"
        "🎡 *Ежедневная рулетка* доступна бесплатно раз в 24 часа."
    )
    
    inline_kb = [
        [InlineKeyboardButton(text="🎡 Ежедневная рулетка", callback_data="game_roulette")],
        [InlineKeyboardButton(text="🎰 Казино (Слоты)", callback_data="game_slots_menu"), InlineKeyboardButton(text="🎲 Угадай кубик", callback_data="game_dice_menu")],
        [InlineKeyboardButton(text="🏴‍☠️ Напёрстки", callback_data="game_thimbles_menu")],
        [InlineKeyboardButton(text="📈 Трейдинг (Биржа)", callback_data="game_trading_menu"), InlineKeyboardButton(text="💣 Минное поле", callback_data="game_mines_menu")],
        [InlineKeyboardButton(text="🕵️‍♂️ Детектив-Шифровальщик", callback_data="game_detective_start")]
    ]
    await message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=inline_kb), parse_mode="Markdown")

# --- 1. ЕЖЕДНЕВНАЯ РУЛЕТКА ---
@router.callback_query(F.data == "game_roulette")
async def process_roulette(callback: CallbackQuery):
    user_id = callback.from_user.id
    current_time = int(time.time())
    
    cursor.execute("SELECT title FROM users WHERE tg_id = ?", (user_id,))
    title = cursor.fetchone()[0]
    
    cooldown_time = 43200 if title == "[🕰️ Бессмертный]" else 86400
    if user_id in ROULETTE_COOLDOWNS:
        passed = current_time - ROULETTE_COOLDOWNS[user_id]
        if passed < cooldown_time:
            rem = cooldown_time - passed
            await callback.answer(f"⏳ Доступно через {rem // 3600} ч. {(rem % 3600) // 60} мин.", show_alert=True)
            return

    ROULETTE_COOLDOWNS[user_id] = current_time
    win_roll = random.randint(1, 100)
    bonus_chance = 5 if title == "[Везучий]" else 0
    
    if win_roll <= (50 - bonus_chance):
        prize_text = "💨 Рулетка оказалась пустой! Повезет завтра."
    elif win_roll <= 80:
        win_money = random.randint(200, 1500)
        cursor.execute("UPDATE users SET money = money + ? WHERE tg_id = ?", (win_money, user_id))
        prize_text = f"💵 Вы выиграли: **${win_money:,}**!"
    elif win_roll <= 95:
        cursor.execute("UPDATE users SET level = level + 1 WHERE tg_id = ?", (user_id,))
        prize_text = "🎂 Рулетка дарит вам **+1 Год Жизни**!"
    else:
        cursor.execute("UPDATE users SET vip_days = vip_days + 1 WHERE tg_id = ?", (user_id,))
        prize_text = "👑 Вы выиграли **1 день VIP-статуса**!"
        
    conn.commit()
    await callback.message.edit_text(f"🎡 **КОЛЕСО ФОРТУНЫ КРУТИТСЯ...** 🎡\n\n{prize_text}", parse_mode="Markdown")
    await callback.answer()
# --- 2. КАЗИНО (СЛОТЫ) ---
@router.callback_query(F.data == "game_slots_menu")
async def slots_menu(callback: CallbackQuery):
    text = "🎰 **КАЗИНО «ОЛИМП»** 🎰\n\nИспытай удачу! Сделай ставку кнопками ниже.\nМинимальная ставка — $100."
    inline_kb = [
        [InlineKeyboardButton(text="💵 $100", callback_data="slots_play_100"), InlineKeyboardButton(text="💵 $500", callback_data="slots_play_500")],
        [InlineKeyboardButton(text="💵 $2,000", callback_data="slots_play_2000"), InlineKeyboardButton(text="💵 $10,000", callback_data="slots_play_10000")],
        [InlineKeyboardButton(text="🔙 Назад в меню", callback_data="game_back")]
    ]
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=inline_kb), parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data.startswith("slots_play_"))
async def play_slots(callback: CallbackQuery):
    user_id = callback.from_user.id
    bet = int(callback.data.split("_")[2])
    
    cursor.execute("SELECT money FROM users WHERE tg_id = ?", (user_id,))
    money = cursor.fetchone()[0]
    
    if money < bet:
        await callback.answer(f"❌ Недостаточно баксов! Нужно ${bet:,}", show_alert=True)
        return
        
    cursor.execute("UPDATE users SET money = money - ? WHERE tg_id = ?", (bet, user_id))
    conn.commit()
    
    msg = await callback.message.answer_dice(emoji="🎰")
    await callback.message.delete()
    await asyncio.sleep(2.5)
    
            # Выигрышные значения для ТГ-слотов: 1, 22, 43, 64 (три в ряд)
    if msg.dice.value in:
        win_amount = bet * 5
        cursor.execute("UPDATE users SET money = money + ? WHERE tg_id = ?", (win_amount, user_id))
        conn.commit()
        await msg.reply(f"🎉 **ДЖЕКПОТ!** Вы выиграли **${win_amount:,}**!", parse_mode="Markdown")
    elif msg.dice.value in: # Хорошие комбинации (две одинаковые)
        win_amount = bet * 2
        cursor.execute("UPDATE users SET money = money + ? WHERE tg_id = ?", (win_amount, user_id))
        conn.commit()
        await msg.reply(f"💵 **ВЫИГРЫШ!** Вы получили **${win_amount:,}**!", parse_mode="Markdown")
    else:
        await msg.reply(f"📉 Мимо! Ставка ${bet:,} потеряна.", parse_mode="Markdown")

# --- 3. УГАДАЙ КУБИК ---
@router.callback_query(F.data == "game_dice_menu")
async def dice_menu(callback: CallbackQuery):
    text = "🎲 **КОСТИ НА БАКСЫ** 🎲\n\nСтавка: $500 баксов. Выберите число от 1 до 6. Угадаете — выигрыш умножится на **x3**!"
    inline_kb = [
        [InlineKeyboardButton(text="1️⃣", callback_data="dice_bet_1"), InlineKeyboardButton(text="2️⃣", callback_data="dice_bet_2"), InlineKeyboardButton(text="3️⃣", callback_data="dice_bet_3")],
        [InlineKeyboardButton(text="4️⃣", callback_data="dice_bet_4"), InlineKeyboardButton(text="5️⃣", callback_data="dice_bet_5"), InlineKeyboardButton(text="6️⃣", callback_data="dice_bet_6")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="game_back")]
    ]
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=inline_kb), parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data.startswith("dice_bet_"))
async def play_dice(callback: CallbackQuery):
    user_id = callback.from_user.id
    chosen_num = int(callback.data.split("_")[2])
    bet = 500
    
    cursor.execute("SELECT money FROM users WHERE tg_id = ?", (user_id,))
    money = cursor.fetchone()[0]
    
    if money < bet:
        await callback.answer("❌ Недостаточно баксов! Нужно $500.", show_alert=True)
        return
        
    cursor.execute("UPDATE users SET money = money - ? WHERE tg_id = ?", (bet, user_id))
    conn.commit()
    
    msg = await callback.message.answer_dice(emoji="🎲")
    await callback.message.delete()
    await asyncio.sleep(2.5)
    
    if msg.dice.value == chosen_num:
        win_money = bet * 3
        cursor.execute("UPDATE users SET money = money + ? WHERE tg_id = ?", (win_money, user_id))
        conn.commit()
        await msg.reply(f"🎉 **ПОБЕДА!** Выпало число {msg.dice.value}! Вы выиграли **${win_money:,}**!", parse_mode="Markdown")
    else:
        await msg.reply(f"📉 Выпало число {msg.dice.value}. Вы ставили на {chosen_num}. Ставка потеряна!", parse_mode="Markdown")

# --- 4. НАПЁРСТКИ ---
@router.callback_query(F.data == "game_thimbles_menu")
async def thimbles_menu(callback: CallbackQuery):
    text = "🏴‍☠️ **НАПЁРСТКИ** 🏴‍☠️\n\nСтавка: $1,000 баксов. Угадай, под каким напёрстком шарик, и забери **$2,500** (коэффициент x2.5)!"
    inline_kb = [
        [InlineKeyboardButton(text="🥛 №1", callback_data="thim_1"), InlineKeyboardButton(text="🥛 №2", callback_data="thim_2"), InlineKeyboardButton(text="🥛 №3", callback_data="thim_3")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="game_back")]
    ]
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=inline_kb), parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data.startswith("thim_"))
async def play_thimbles(callback: CallbackQuery):
    user_id = callback.from_user.id
    chosen_cup = int(callback.data.split("_")[1])
    bet = 1000
    
    cursor.execute("SELECT money FROM users WHERE tg_id = ?", (user_id,))
    money = cursor.fetchone()[0]
    
    if money < bet:
        await callback.answer("❌ Недостаточно баксов! Нужно $1,000.", show_alert=True)
        return
        
    cursor.execute("UPDATE users SET money = money - ? WHERE tg_id = ?", (bet, user_id))
    conn.commit()
    
    winning_cup = random.randint(1, 3)
    if chosen_cup == winning_cup:
        win_money = int(bet * 2.5)
        cursor.execute("UPDATE users SET money = money + ? WHERE tg_id = ?", (win_money, user_id))
        conn.commit()
        result_text = f"🎉 **ВЫ УГАДАЛИ!** Шарик под напёрстком №{winning_cup}!\n💰 Выигрыш: **${win_money:,}**"
    else:
        result_text = f"📉 **ПРОИГРЫШ!** Напёрсток №{chosen_cup} пуст. Шарик был под №{winning_cup}."
        
    inline_kb = [[InlineKeyboardButton(text="🔄 Играть еще раз", callback_data="game_thimbles_menu")], [InlineKeyboardButton(text="🔙 В меню игр", callback_data="game_back")]]
    await callback.message.edit_text(result_text, reply_markup=InlineKeyboardMarkup(inline_keyboard=inline_kb), parse_mode="Markdown")
    await callback.answer()

# --- ОБЩАЯ КНОПКА ВОЗВРАТА В МЕНЮ ИГР ---
@router.callback_query(F.data == "game_back")
async def game_back_callback(callback: CallbackQuery):
    await show_games_menu(callback.message)
    await callback.message.delete()
    await callback.answer()
# --- 5. ТРЕЙДИНГ (БИРЖА) ---
@router.callback_query(F.data == "game_trading_menu")
async def trading_menu(callback: CallbackQuery):
    text = (
        "📈 **БИРЖА ТРЕЙДИНГА** 📈\n\n"
        "Ставка: $1,000 баксов. Угадайте, куда двинется график валюты в следующую секунду!\n"
        "📈 Вверх или 📉 Вниз?\n\n"
        "При победе вы получаете **$1,800** (коэффициент x1.8).\n"
        "Если у вас есть Страховой полис, при проигрыше вам вернется 50% ставки!"
    )
    inline_kb = [
        [InlineKeyboardButton(text="📈 Вверх", callback_data="trade_up"), InlineKeyboardButton(text="📉 Вниз", callback_data="trade_down")],
        [InlineKeyboardButton(text="🔙 Назад в меню", callback_data="game_back")]
    ]
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=inline_kb), parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data.startswith("trade_"))
async def play_trading(callback: CallbackQuery):
    user_id = callback.from_user.id
    player_guess = callback.data.split("_")[1] # Получаем 'up' или 'down'
    bet = 1000
    
    cursor.execute("SELECT money, title, house FROM users WHERE tg_id = ?", (user_id,))
    money, title, house = cursor.fetchone()
    
    if money < bet:
        await callback.answer("❌ Недостаточно баксов для торгов! Нужно $1,000.", show_alert=True)
        return
        
    # Списываем ставку на биржу
    cursor.execute("UPDATE users SET money = money - ? WHERE tg_id = ?", (bet, user_id))
    conn.commit()
    
    # Случайный исход рынка (50 на 50)
    market_result = random.choice(["up", "down"])
    market_emoji = "📈 ВВЕРХ" if market_result == "up" else "📉 ВНИЗ"
    
    if player_guess == market_result:
        # Победа на бирже
        win_money = int(bet * 1.8)
        cursor.execute("UPDATE users SET money = money + ? WHERE tg_id = ?", (win_money, user_id))
        conn.commit()
        result_text = f"🎉 **УСПЕШНАЯ СДЕЛКА!**\nГрафик пошел {market_emoji}!\n💰 Вы заработали на прогнозе: **${win_money:,}**"
    else:
        # Проигрыш на бирже. Проверяем наличие страховки (из таблицы недвижимости/магазина)
        # Мы используем временную логику проверки предметов через проверку звания и страховки
        returned_money = 0
        insurance_used = False
        
        # Твое условие: звание [⚡ Пророк Трейдинга] возвращает 15% ставки
        if title == "[⚡ Пророк Трейдинга]":
            returned_money = int(bet * 0.15)
            result_text = f"📉 **СДЕЛКА В МИНУС!**\nГрафик пошел {market_emoji}.\n🛡️ Благодаря званию `[⚡ Пророк Трейдинга]` вам вернулось **${returned_money}**!"
        else:
            # Обычный проигрыш
            result_text = f"📉 **СДЕЛКА В МИНУС!**\nГрафик пошел {market_emoji}.\nВы потеряли ставку в $1,000."
            
        if returned_money > 0:
            cursor.execute("UPDATE users SET money = money + ? WHERE tg_id = ?", (returned_money, user_id))
            conn.commit()
            
    inline_kb = [
        [InlineKeyboardButton(text="🔄 Торговать еще", callback_data="game_trading_menu")],
        [InlineKeyboardButton(text="🔙 В меню игр", callback_data="game_back")]
    ]
    await callback.message.edit_text(result_text, reply_markup=InlineKeyboardMarkup(inline_keyboard=inline_kb), parse_mode="Markdown")
    await callback.answer()
# --- ХРАНИЛИЩЕ СОСТОЯНИЙ ДЛЯ ИГРЫ «МИННОЕ ПОЛЕ» ---
# Структура: user_id: {"step": текущий_шаг, "mines": [индексы_мин]}
MINES_SESSIONS = {}
MINES_MULTIPLIERS = [1.2, 1.5, 2.0, 3.0, 5.0, 8.0, 15.0]

# --- 6. МИННОЕ ПОЛЕ (ГЛАВНОЕ МЕНЮ И СТАРТ) ---
@router.callback_query(F.data == "game_mines_menu")
async def mines_menu(callback: CallbackQuery):
    text = (
        "💣 **МИННОЕ ПОЛЕ (САПЁР)** 💣\n\n"
        "Ставка: $1,000 баксов. Перед вами поле 3х3, на котором скрыто ровно 2 мины.\n\n"
        "Каждая открытая безопасная клетка увеличивает ваш выигрыш!\n"
        "Вы можете **забрать деньги в любой момент** до взрыва!"
    )
    inline_kb = [
        [InlineKeyboardButton(text="🚀 Начать игру ($1,000)", callback_data="mines_start_game")],
        [InlineKeyboardButton(text="🔙 Назад в меню", callback_data="game_back")]
    ]
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=inline_kb), parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data == "mines_start_game")
async def mines_start_game(callback: CallbackQuery):
    user_id = callback.from_user.id
    bet = 1000
    
    cursor.execute("SELECT money FROM users WHERE tg_id = ?", (user_id,))
    money = cursor.fetchone()[0]
    
    if money < bet:
        await callback.answer("❌ Недостаточно баксов! Нужно $1,000.", show_alert=True)
        return
        
    cursor.execute("UPDATE users SET money = money - ? WHERE tg_id = ?", (bet, user_id))
    conn.commit()
    
    # Генерируем 2 случайные мины на поле из 9 клеток (0-8)
    all_cells = list(range(9))
    mine_cells = random.sample(all_cells, 2)
    
    # Сохраняем сессию игрока
    MINES_SESSIONS[user_id] = {"step": 0, "mines": mine_cells, "opened": []}
    
    await render_mines_field(callback, user_id, "💣 **МИННОЕ ПОЛЕ** 💣\n\nИгра началась! Выберите любую клетку:")
    await callback.answer()

# --- ФУНКЦИЯ ОТРИСОВКИ КНОПОК ПОЛЯ 3х3 ---
async def render_mines_field(callback: CallbackQuery, user_id: int, text: str):
    session = MINES_SESSIONS[user_id]
    current_step = session["step"]
    opened = session["opened"]
    
    # Текущий множитель
    mult = MINES_MULTIPLIERS[current_step] if current_step < len(MINES_MULTIPLIERS) else MINES_MULTIPLIERS[-1]
    current_win = int(1000 * mult)
    
    inline_kb = []
    row = []
    
    for i in range(9):
        if i in opened:
            row.append(InlineKeyboardButton(text="💎", callback_data="mines_empty"))
        else:
            row.append(InlineKeyboardButton(text="❓", callback_data=f"mines_click_{i}"))
            
        if len(row) == 3:
            inline_kb.append(row)
            row = []
            
    # Добавляем кнопку сбора прибыли, если сделан хотя бы 1 шаг
    status_text = text + f"\n\n📈 Текущий множитель: **x{mult}**\n💰 Возможный выигрыш: **${current_win:,}**"
    
    if current_step > 0:
        inline_kb.append([InlineKeyboardButton(text=f"💰 Забрать ${current_win:,}", callback_data="mines_cashout")])
    else:
        inline_kb.append([InlineKeyboardButton(text="🏳️ Сдаться", callback_data="game_back")])
        
    await callback.message.edit_text(status_text, reply_markup=InlineKeyboardMarkup(inline_keyboard=inline_kb), parse_mode="Markdown")

# --- ОБРАБОТКА КЛИКА ПО КЛЕТКЕ ---
@router.callback_query(F.data.startswith("mines_click_"))
async def mines_click(callback: CallbackQuery):
    user_id = callback.from_user.id
    if user_id not in MINES_SESSIONS:
        await callback.answer("❌ Сессия игры не найдена. Начните заново.", show_alert=True)
        return
        
    cell_idx = int(callback.data.split("_")[2])
    session = MINES_SESSIONS[user_id]
    
    # Наступил на мину
    if cell_idx in session["mines"]:
        del MINES_SESSIONS[user_id] # Удаляем сессию
        
        inline_kb = [[InlineKeyboardButton(text="🔄 Играть еще раз", callback_data="game_mines_menu")], [InlineKeyboardButton(text="🔙 В меню игр", callback_data="game_back")]]
        await callback.message.edit_text("💥 **БА-БАХ! Вы наступили на мину!** 💥\n\nСтавка $1,000 баксов полностью сгорела.", reply_markup=InlineKeyboardMarkup(inline_keyboard=inline_kb))
        await callback.answer()
        return
        
    # Клетка безопасна
    session["opened"].append(cell_idx)
    session["step"] += 1
    
    # Если открыл все безопасные клетки (9 - 2 мины = 7 шагов)
    if session["step"] == 7:
        win_money = int(1000 * MINES_MULTIPLIERS[-1])
        cursor.execute("UPDATE users SET money = money + ? WHERE tg_id = ?", (win_money, user_id))
        conn.commit()
        del MINES_SESSIONS[user_id]
        
        inline_kb = [[InlineKeyboardButton(text="🔙 В меню игр", callback_data="game_back")]]
        await callback.message.edit_text(f"🏆 **НЕВЕРОЯТНО!** Вы прошли всё минное поле без единой ошибки!\n💰 Ваш мега-выигрыш: **${win_money:,}**!", reply_markup=InlineKeyboardMarkup(inline_keyboard=inline_kb))
    else:
        await render_mines_field(callback, user_id, "✅ Безопасно! Двигаемся дальше:")
    await callback.answer()

# --- КНОПКА КЭШАУТА (ЗАБРАТЬ ПРИБЫЛЬ) ---
@router.callback_query(F.data == "mines_cashout")
async def mines_cashout(callback: CallbackQuery):
    user_id = callback.from_user.id
    if user_id not in MINES_SESSIONS:
        return
        
    session = MINES_SESSIONS[user_id]
    current_step = session["step"]
    
    # Берем множитель предыдущего успешного шага
    mult = MINES_MULTIPLIERS[current_step - 1]
    win_money = int(1000 * mult)
    
    cursor.execute("UPDATE users SET money = money + ? WHERE tg_id = ?", (win_money, user_id))
    conn.commit()
    del MINES_SESSIONS[user_id] # Закрываем сессию
    
    inline_kb = [[InlineKeyboardButton(text="🔄 Играть еще раз", callback_data="game_mines_menu")], [InlineKeyboardButton(text="🔙 В меню игр", callback_data="game_back")]]
    await callback.message.edit_text(f"💰 **ВЫ ЗАБРАЛИ ДЕНЬГИ!** 💰\n\nВаша интуиция вас не подвела. Выигрыш **${win_money:,}** успешно зачислен на баланс!", reply_markup=InlineKeyboardMarkup(inline_keyboard=inline_kb))
    await callback.answer()

# Заглушка для пустых кликов по уже открытым кристаллам
@router.callback_query(F.data == "mines_empty")
async def mines_empty(callback: CallbackQuery):
    await callback.answer("💎 Эта клетка уже открыта!")
# --- ПОЛНАЯ БАЗА ШИФРОВ ДЛЯ ДЕТЕКТИВА (35 НАБОРОВ БУКВ) ---
DETECTIVE_WORDS = [
    {"letters": "Р, О, Т, К, А", "answers": ["карта", "крот", "ток", "кот", "рот"]},
    {"letters": "Е, Т, С, О, Т", "answers": ["тесто", "тост", "сет"]},
    {"letters": "А, К, Л, О, Ш", "answers": ["школа", "шок", "лак", "кол"]},
    {"letters": "И, К, Н, Г, А", "answers": ["книга", "гиря", "ранг"]},
    {"letters": "З, О, Б, А, Р", "answers": ["образ", "забор", "роза", "бор"]},
    {"letters": "О, Л, С, О, В", "answers": ["слово", "соло", "вол"]},
    {"letters": "У, Р, К, А, Р", "answers": ["рукав", "рука", "рак"]},
    {"letters": "И, М, Ф, Л, Ь", "answers": ["фильм", "миф", "ил"]},
    {"letters": "Е, В, Д, О, Р", "answers": ["ведро", "двор", "вор"]},
    {"letters": "А, К, Ч, Р, У", "answers": ["ручка", "рак", "чудо"]},
    {"letters": "М, З, И, А", "answers": ["зима", "мир", "зал"]},
    {"letters": "О, П, И, Р, Т", "answers": ["пирог", "порт", "пир", "рот"]},
    {"letters": "О, Н, К, И", "answers": ["кино", "кон", "ион"]},
    {"letters": "Е, Б, Х, Л", "answers": ["хлеб", "бег", "лес"]},
    {"letters": "Р, И, Г, А", "answers": ["игра", "граф", "шаг"]},
    {"letters": "Т, О, С, Л", "answers": ["стол", "стул", "лот"]},
    {"letters": "А, М, П, Л, А", "answers": ["лампа", "плато", "мама"]},
    {"letters": "О, К, Р, Е, В", "answers": ["вечер", "кров", "век", "рок"]},
    {"letters": "А, З, Г, А, К", "answers": ["загадка", "газ", "зал"]},
    {"letters": "А, Т, Р, С, Т", "answers": ["старт", "торт", "трасса"]},
    {"letters": "Е, В, Т, Е, Р", "answers": ["ветер", "веер", "век"]},
    {"letters": "О, Т, К, О, П", "answers": ["поток", "кот", "пот", "ток"]},
    {"letters": "А, О, К, Е, О", "answers": ["океан", "окно", "кок"]},
    {"letters": "И, Н, Л, И, Я", "answers": ["линия", "имя", "лик"]},
    {"letters": "А, Г, О, В, Н", "answers": ["вагон", "нога", "гол", "вол"]},
    {"letters": "О, Р, М, Ф, А", "answers": ["форма", "море", "ром"]},
    {"letters": "А, Н, П, Ц, И", "answers": ["птица", "пан", "цена"]},
    {"letters": "О, К, Л, О, С", "answers": ["сокол", "колос", "сок", "лок"]},
    {"letters": "А, К, С, М, А", "answers": ["маска", "мак", "сам"]},
    {"letters": "Е, Р, З, О", "answers": ["озеро", "зоря", "роз"]},
    {"letters": "О, К, Л, А, Б", "answers": ["бокал", "бал", "лоб", "бак"]},
    {"letters": "У, К, Т, А, Ш", "answers": ["шутка", "шум", "так", "акт"]},
    {"letters": "И, Р, Ф, А, Ц", "answers": ["цифра", "фарт", "царь"]},
    {"letters": "А, Р, Т, А, Г", "answers": ["гитара", "тара", "град"]},
    {"letters": "О, П, Л, А, С, Т", "answers": ["пальто", "пласт", "пол", "стол"]}
]

# --- ЗАПУСК ДЕТЕКТИВА ---
@router.callback_query(F.data == "game_detective_start")
async def start_detective(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    
    # Выбираем случайное слово из базы
    puzzle = random.choice(DETECTIVE_WORDS)
    await state.update_data(current_puzzle=puzzle)
    
    text = (
        "🕵️‍♂️ **ДЕТЕКТИВ-ШИФРОВАЛЬЩИК** 🕵️‍♂️\n\n"
        "Преступник зашифровал важную улику! Составьте существующее русское слово из этих букв:\n"
        f"➡️ **{puzzle['letters']}**\n\n"
        "🔥 Награда за успех: **$1,000 баксов** и **+80 XP**!\n"
        "Введите ответ текстом в чат."
    )
    
    inline_kb = [[InlineKeyboardButton(text="🤷‍♂️ Не знаю (Пропустить)", callback_data="game_detective_skip")]]
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=inline_kb), parse_mode="Markdown")
    await state.set_state(GameStates.wait_detective)
    await callback.answer()

# --- КНОПКА ПРОПУСКА СЛОВА ---
@router.callback_query(F.data == "game_detective_skip")
async def skip_detective(callback: CallbackQuery, state: FSMContext):
    await callback.answer("🔄 Меняем шифр...")
    await start_detective(callback, state)

# --- ПРОВЕРКА ОТВЕТА ИГРОКА ---
@router.message(GameStates.wait_detective)
async def check_detective_answer(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user_answer = message.text.strip().lower()
    
    data = await state.get_data()
    puzzle = data.get("current_puzzle")
    
    if not puzzle:
        await state.clear()
        return

    if user_answer in puzzle["answers"]:
        # Игрок угадал слово
        cursor.execute("SELECT money, xp, level FROM users WHERE tg_id = ?", (user_id,))
        money, current_xp, current_level = cursor.fetchone()
        
        new_money = money + 1000
        new_xp = current_xp + 80
        
        # Расчет левелапа
        req_xp = get_required_xp(current_level)
        leveled_up = False
        while new_xp >= req_xp:
            new_xp -= req_xp
            current_level += 1
            req_xp = get_required_xp(current_level)
            leveled_up = True
            
        cursor.execute("UPDATE users SET money = ?, xp = ?, level = ? WHERE tg_id = ?", (new_money, new_xp, current_level, user_id))
        conn.commit()
        
        congratulations = (
            f"🎉 **ПОТРЯСАЮЩЕ!** Слово «{user_answer.upper()}» найдено в базе улик!\n\n"
            f"💰 Награда: **+$1,000 баксов**\n"
            f"📈 Опыт: **+80 XP**"
        )
        if leveled_up:
            congratulations += f"\n\n🎉 **ПОЗДРАВЛЯЕМ!** Вы повзрослели! Новый возраст: **{current_level} лет**!"
            
        inline_kb = [[InlineKeyboardButton(text="🕵️‍♂️ Сыграть еще раз", callback_data="game_detective_start")], [InlineKeyboardButton(text="🔙 К меню игр", callback_data="game_back")]]
        await message.answer(congratulations, reply_markup=InlineKeyboardMarkup(inline_keyboard=inline_kb), parse_mode="Markdown")
        await state.clear()
    else:
        inline_kb = [[InlineKeyboardButton(text="🤷‍♂️ Сдаться (Пропустить)", callback_data="game_detective_skip")]]
        await message.answer("❌ Такое слово не найдено в базе улик преступника! Подумайте еще или пропустите шифр:", reply_markup=InlineKeyboardMarkup(inline_keyboard=inline_kb))
# --- КНОПКА «🛒 МАГАЗИН» (ГЛАВНОЕ МЕНЮ ПОКУПОК) ---
@router.message(F.text == "🛒 Магазин")
async def show_shop_menu(message: Message):
    user_id = message.from_user.id
    
    # Проверяем бан
    cursor.execute("SELECT is_banned FROM users WHERE tg_id = ?", (user_id,))
    ban_res = cursor.fetchone()
    if ban_res and ban_res == 1:
        await message.answer("⛔ **ДОСТУП ОГРАНИЧЕН**\n\nВы заблокированы!")
        return
        
    text = (
        "🛒 **ИГРОВОЙ СУПЕРМАРКЕТ** 🛒\n\n"
        "Здесь вы можете приобрести полезные бустеры, VIP-подписку или испытать удачу в кейсах с уникальными титулами!"
    )
    
    inline_kb = [
        [InlineKeyboardButton(text="⚡ Бустеры и Лотерея", callback_data="shop_boosters"), InlineKeyboardButton(text="👑 VIP-Услуги", callback_data="shop_vip")],
        [InlineKeyboardButton(text="🧰 Открытие Кейсов", callback_data="shop_cases")]
    ]
    await message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=inline_kb), parse_mode="Markdown")

# --- ВТОРЫЕ МЕНЮ МАГАЗИНА (БУСТЕРЫ И VIP) ---
@router.callback_query(F.data == "shop_boosters")
async def shop_boosters(callback: CallbackQuery):
    text = (
        "⚡ **БУСТЕРЫ И ПОЛЕЗНЫЕ ТОВАРЫ** ⚡\n\n"
        "🔋 **Энергетик** — $400\n└ Обнуляет таймер работы (снимает КД смены).\n\n"
        "📚 **Курсы саморазвития** — $2,500\n└ Моментально дают вам **+150 XP**.\n\n"
        "🎟️ **Лотерейный билет** — $500\n└ Шанс выиграть случайный куш от $100 до $5,000!"
    )
    inline_kb = [
        [InlineKeyboardButton(text="🔋 Купить Энергетик", callback_data="buy_energy"), InlineKeyboardButton(text="📚 Купить Курсы", callback_data="buy_courses")],
        [InlineKeyboardButton(text="🎟️ Купить Лотерею", callback_data="buy_lottery")],
        [InlineKeyboardButton(text="🔙 Назад в магазин", callback_data="shop_main_back")]
    ]
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=inline_kb), parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data == "shop_vip")
async def shop_vip(callback: CallbackQuery):
    text = (
        "👑 **МАГАЗИН VIP-СТАТУСОВ** 👑\n\n"
        "VIP-статус дает уникальный значок ⭐ в паспорт, +20% к зарплате, +50% к пассивному бизнесу, КД рулетки 12 часов и доступ к секретному VIP-кейсу!\n\n"
        "• 🎫 **VIP на 10 дней** — $15,000\n"
        "• 💎 **VIP на 20 дней** — $28,000\n"
        "• 🔮 **VIP на 30 дней** — $40,000"
    )
    inline_kb = [
        [InlineKeyboardButton(text="🎫 VIP 10 дней", callback_data="buy_vip_10"), InlineKeyboardButton(text="💎 VIP 20 дней", callback_data="buy_vip_20")],
        [InlineKeyboardButton(text="🔮 VIP 30 дней", callback_data="buy_vip_30")],
        [InlineKeyboardButton(text="🔙 Назад в магазин", callback_data="shop_main_back")]
    ]
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=inline_kb), parse_mode="Markdown")
    await callback.answer()

# --- МЕНЮ ОТКРЫТИЯ КЕЙСОВ ---
@router.callback_query(F.data == "shop_cases")
async def shop_cases(callback: CallbackQuery):
    text = (
        "🧰 **МАГАЗИН КЕЙСОВ С ТИТУЛАМИ** 🧰\n\n"
        "Выбивайте крутые звания, которые дают реальные игровые бонусы к заработку!\n\n"
        "1. 📦 **Кейс «Бомж»** — $1,500\n└ Обычные титулы. Шанс на редкий `[Везучий]` (+5% к рулетке).\n\n"
        "2. 💼 **Кейс «Средняк»** — $8,000\n└ Титулы: `[Трудяга]` (-2 мин смены), `[Менеджер]` (+5% к ЗП), `[Стильный]` / `[Красавчик]` (скидка 5% на жилье).\n\n"
        "3. 💎 **Кейс «Мажор»** — $50,000\n└ Легендарные: `[Бизнесмен]` / `[Акула Бизнеса]` (+10% к бизнесу), `[Олигарх]` / `[Шейх]` (+$5,000 баксов ежедневно).\n\n"
        "4. 👑 **Кейс «VIP-Секрет»** — $35,000\n└ 🔒 *Доступен только для VIP!* Уникальные титулы: `[💎 Король Сливок]` (x1.2 ко всему доходу!), `[⚡ Пророк Трейдинга]` (возврат 15% на бирже), `[🕰️ Бессмертный]` (рулетка каждые 12 ч)."
    )
    inline_kb = [
        [InlineKeyboardButton(text="📦 Бомж", callback_data="open_case_1"), InlineKeyboardButton(text="💼 Средняк", callback_data="open_case_2")],
        [InlineKeyboardButton(text="💎 Мажор", callback_data="open_case_3"), InlineKeyboardButton(text="👑 VIP-Секрет", callback_data="open_case_4")],
        [InlineKeyboardButton(text="🔙 Назад в магазин", callback_data="shop_main_back")]
    ]
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=inline_kb), parse_mode="Markdown")
    await callback.answer()

# --- ЛОГИКА ОБРАБОТКИ ВСЕХ ПОКУПОК ---
@router.callback_query(F.data.startswith("buy_"))
async def process_shop_buys(callback: CallbackQuery):
    user_id = callback.from_user.id
    item = callback.data.split("_")
    
    cursor.execute("SELECT money, vip_days, level, xp FROM users WHERE tg_id = ?", (user_id,))
    money, current_vip, current_level, current_xp = cursor.fetchone()
    
    # Покупка Энергетика
    if item == "energy":
        if money < 400: await callback.answer("❌ Недостаточно баксов! Нужно $400.", show_alert=True); return
        cursor.execute("UPDATE users SET money = money - 400, job_start_time = 0 WHERE tg_id = ?", (user_id,))
        await callback.answer("🔋 Вы выпили энергетик! Таймер смены на работе успешно обнулен.", show_alert=True)
        
    # Покупка Курсов
    elif item == "courses":
        if money < 2500: await callback.answer("❌ Недостаточно баксов! Нужно $2,500.", show_alert=True); return
        new_money = money - 2500
        new_xp = current_xp + 150
        req_xp = get_required_xp(current_level)
        leveled_up = False
        while new_xp >= req_xp:
            new_xp -= req_xp
            current_level += 1
            req_xp = get_required_xp(current_level)
            leveled_up = True
        cursor.execute("UPDATE users SET money = ?, xp = ?, level = ? WHERE tg_id = ?", (new_money, new_xp, current_level, user_id))
        alert_text = f"📚 Вы прошли курсы и получили +150 XP!"
        if leveled_up: alert_text += f"\n🎉 Вы повзрослели! Новый возраст: {current_level} лет!"
        await callback.answer(alert_text, show_alert=True)
        
    # Покупка Лотереи
    elif item == "lottery":
        if money < 500: await callback.answer("❌ Недостаточно баксов! Нужно $500.", show_alert=True); return
        win = random.randint(100, 5000)
        cursor.execute("UPDATE users SET money = money - 500 + ? WHERE tg_id = ?", (win, user_id))
        await callback.answer(f"🎟️ Билет использован! Ваш выигрыш составил: ${win:,}!", show_alert=True)
        
    # Покупка VIP подписки
    elif item == "vip":
        days = int(item)
        prices = {10: 15000, 20: 28000, 30: 40000}
        price = prices[days]
        if money < price: await callback.answer(f"❌ Недостаточно баксов! Нужно ${price:,}", show_alert=True); return
        cursor.execute("UPDATE users SET money = money - ?, vip_days = vip_days + ? WHERE tg_id = ?", (price, days, user_id))
        await callback.answer(f"👑 Спасибо за покупку! VIP-статус успешно продлен на +{days} дней!", show_alert=True)
        await shop_vip(callback)
        
    conn.commit()
    await callback.answer()

# --- ЛОГИКА ОТКРЫТИЯ КЕЙСОВ С ТИТУЛАМИ ---
@router.callback_query(F.data.startswith("open_case_"))
async def process_case_opening(callback: CallbackQuery):
    user_id = callback.from_user.id
    case_num = int(callback.data.split("_")[-1])
    
    cursor.execute("SELECT money, vip_days FROM users WHERE tg_id = ?", (user_id,))
    money, vip_days = cursor.fetchone()
    
    # 1. Списки дропа по кейсам
    case_1_pool = ["[Бедолага]", "[Уличный]", "[Доширачник]", "[Везучий]"]
    case_2_pool = ["[Трудяга]", "[Менеджер]", "[Стильный]", "[Красавчик]"]
    case_3_pool = ["[Бизнесмен]", "[Акула Бизнеса]", "[Олигарх]", "[Шейх]"]
    case_4_pool = ["[💎 Король Сливок]", "[⚡ Пророк Трейдинга]", "[🕰️ Бессмертный]"]
    
    if case_num == 1:
        if money < 1500: await callback.answer("❌ Нужно $1,500!", show_alert=True); return
        new_money, title = money - 1500, random.choice(case_1_pool)
    elif case_num == 2:
        if money < 8000: await callback.answer("❌ Нужно $8,000!", show_alert=True); return
        new_money, title = money - 8000, random.choice(case_2_pool)
    elif case_num == 3:
        if money < 50000: await callback.answer("❌ Нужно $50,000!", show_alert=True); return
        new_money, title = money - 50000, random.choice(case_3_pool)
    elif case_num == 4:
        if vip_days <= 0: await callback.answer("🔒 Этот кейс доступен только гражданам с активным VIP-статусом!", show_alert=True); return
        if money < 35000: await callback.answer("❌ Нужно $35,000!", show_alert=True); return
        new_money, title = money - 35000, random.choice(case_4_pool)
        
    cursor.execute("UPDATE users SET money = ?, title = ? WHERE tg_id = ?", (new_money, title, user_id))
    conn.commit()
    
    await callback.answer(f"🧰 Кейс открыт!\n\n🎉 Вам выпало звание: {title}! Бонусы активированы.", show_alert=True)

# --- ВОЗВРАТ ИЗ ПОДМЕНЮ В КОРЕНЬ МАГАЗИНА ---
@router.callback_query(F.data == "shop_main_back")
async def shop_main_back(callback: CallbackQuery):
    await show_shop_menu(callback.message)
    await callback.message.delete()
    await callback.answer()

# --- ФИНАЛЬНЫЙ АСИНХРОННЫЙ ЗАПУСК СЕРДЦА БОТА ---
async def main():
    dp.include_router(router)
    print("🚀 [СИСТЕМА]: Игровой бот «Мини-Жизнь» успешно скомпилирован и запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())