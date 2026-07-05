import asyncio
import time
import random

from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

# =========================
# ⚙️ НАСТРОЙКИ (ВСТАВЬ СЮДА)
# =========================
TOKEN = "8962500881:AAFDttMSkEzQcSGUjljScWX6VpSbew67g58"
ADMIN_ID = 810004621


bot = Bot(token=TOKEN)
dp = Dispatcher()
router = Router()


# =========================
# 🧠 ДАННЫЕ ПОЛЬЗОВАТЕЛЕЙ
# =========================
users = {}

def get_user(uid: int):
    if uid not in users:
        users[uid] = {
            "money": 0,
            "xp": 0,
            "level": 1,
            "job": "Безработный",
            "vip_until": 0,
        }
    return users[uid]


def level_bar(xp):
    need = 50
    cur = xp % need
    filled = int((cur / need) * 5)
    return "⬛" * filled + "⬜" * (5 - filled), cur, need


# =========================
# 📱 ГЛАВНОЕ МЕНЮ
# =========================
def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💼 Работа", callback_data="work")],
        [InlineKeyboardButton(text="🏪 Магазин", callback_data="shop")],
        [InlineKeyboardButton(text="🎮 Игры", callback_data="games")],
        [InlineKeyboardButton(text="🏠 Дома", callback_data="houses")],
        [InlineKeyboardButton(text="🎒 Инвентарь", callback_data="inv")],
        [InlineKeyboardButton(text="👤 Профиль", callback_data="profile")],
        [InlineKeyboardButton(text="🔐 Админ", callback_data="admin")]
    ])


# =========================
# /start
# =========================
@router.message(F.text == "/start")
async def start(message: Message):
    await message.answer(
        "👋 Добро пожаловать в LIFE GAME BOT!\n\n"
        "Ты начинаешь жизнь с нуля...\n"
        "Работай 💼, зарабатывай 💰, развивайся 📈\n\n"
        "Нажми кнопку ниже 👇",
        reply_markup=main_menu()
    )


# =========================
# 👤 ПРОФИЛЬ
# =========================
@router.callback_query(F.data == "profile")
async def profile(call: CallbackQuery):
    u = get_user(call.from_user.id)

    bar, cur, need = level_bar(u["xp"])
    vip = "✅ ACTIVE" if u["vip_until"] > time.time() else "❌ NO VIP"

    text = (
        f"👤 ПРОФИЛЬ\n\n"
        f"💰 Баланс: {u['money']} G\n"
        f"💼 Работа: {u['job']}\n\n"
        f"⭐ Level: {u['level']}\n"
        f"📊 XP: {cur}/{need}\n"
        f"{bar}\n\n"
        f"🎫 VIP: {vip}"
    )

    await call.message.edit_text(text, reply_markup=main_menu())


# =========================
# 💼 РАБОТА
# =========================
@router.callback_query(F.data == "work")
async def work(call: CallbackQuery):
    u = get_user(call.from_user.id)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚚 Доставщик +100G", callback_data="job_1")],
        [InlineKeyboardButton(text="👨‍💻 Программист +200G", callback_data="job_2")],
        [InlineKeyboardButton(text="❌ Уволиться", callback_data="job_leave")],
        [InlineKeyboardButton(text="⬅ Назад", callback_data="menu")]
    ])

    await call.message.edit_text(
        f"💼 РАБОТА\n\nТекущая: {u['job']}",
        reply_markup=kb
    )


@router.callback_query(F.data.startswith("job_"))
async def job(call: CallbackQuery):
    u = get_user(call.from_user.id)

    if call.data == "job_leave":
        u["job"] = "Безработный"
        await call.answer("Уволились")
        return

    if call.data == "job_1":
        u["job"] = "Доставщик"
        u["money"] += 100
        u["xp"] += 5

    if call.data == "job_2":
        u["job"] = "Программист"
        u["money"] += 200
        u["xp"] += 10

    await call.answer("Готово")


# =========================
# 🎮 ИГРЫ
# =========================
@router.callback_query(F.data == "games")
async def games(call: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎲 Угадай число", callback_data="game_guess")],
        [InlineKeyboardButton(text="🎰 Казино", callback_data="game_casino")],
        [InlineKeyboardButton(text="⚠ Риск", callback_data="game_risk")],
        [InlineKeyboardButton(text="🕵️ Детектив", callback_data="game_detective")],
        [InlineKeyboardButton(text="🔤 Анаграмма", callback_data="game_word")],
        [InlineKeyboardButton(text="⬅ Назад", callback_data="menu")]
    ])

    await call.message.edit_text("🎮 ВЫБЕРИ ИГРУ:", reply_markup=kb)


# =========================
# 🎰 КАЗИНО
# =========================
@router.callback_query(F.data == "game_casino")
async def casino(call: CallbackQuery):
    u = get_user(call.from_user.id)

    if random.choice([True, False]):
        u["money"] += 200
        await call.message.edit_text("🎰 Вы выиграли +200G")
    else:
        u["money"] -= 100
        await call.message.edit_text("🎰 Вы проиграли -100G")


# =========================
# ⚠ РИСК
# =========================
@router.callback_query(F.data == "game_risk")
async def risk(call: CallbackQuery):
    u = get_user(call.from_user.id)

    r = random.randint(1, 100)

    if r < 40:
        u["money"] += 300
        await call.message.edit_text("⚠ УДАЧА +300G")
    else:
        u["money"] -= 200
        await call.message.edit_text("⚠ ПРОВАЛ -200G")


# =========================
# 🕵️ ДЕТЕКТИВ
# =========================
@router.callback_query(F.data == "game_detective")
async def detective(call: CallbackQuery):
    u = get_user(call.from_user.id)

    u["money"] += 150
    u["xp"] += 10

    await call.message.edit_text("🕵️ Дело раскрыто +150G")


# =========================
# 🔤 АНАМГРАММА
# =========================
@router.callback_query(F.data == "game_word")
async def word(call: CallbackQuery):
    u = get_user(call.from_user.id)

    u["money"] += 120
    u["xp"] += 8

    await call.message.edit_text("🔤 Слово угадано +120G")


# =========================
# 🏪 МАГАЗИН
# =========================
@router.callback_query(F.data == "shop")
async def shop(call: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎫 VIP", callback_data="buy_vip")],
        [InlineKeyboardButton(text="🏠 Квартира", callback_data="buy_house")],
        [InlineKeyboardButton(text="⚡ Энергетик", callback_data="buy_energy")],
        [InlineKeyboardButton(text="⬅ Назад", callback_data="menu")]
    ])

    await call.message.edit_text("🏪 МАГАЗИН", reply_markup=kb)


# =========================
# 🏠 ДОМА
# =========================
@router.callback_query(F.data == "houses")
async def houses(call: CallbackQuery):
    await call.message.edit_text("🏠 Дома будут расширены")


# =========================
# 🎒 ИНВЕНТАРЬ
# =========================
@router.callback_query(F.data == "inv")
async def inv(call: CallbackQuery):
    await call.message.edit_text("🎒 Инвентарь пуст")


# =========================
# 🔐 АДМИНКА
# =========================
@router.callback_query(F.data == "admin")
async def admin(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        await call.answer("Нет доступа", show_alert=True)
        return

    await call.message.edit_text(
        "🔐 АДМИНКА\n\n"
        "Доступ:\n"
        "/give_money\n"
        "/give_xp\n"
        "/give_vip"
    )


# =========================
# 🔙 МЕНЮ
# =========================
@router.callback_query(F.data == "menu")
async def menu(call: CallbackQuery):
    await call.message.edit_text("Главное меню", reply_markup=main_menu())


# =========================
# RUN
# =========================
async def main():
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())