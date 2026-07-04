import json
import time
import random
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = "8962500881:AAFDttMSkEzQcSGUjljScWX6VpSbew67g58"
DATA_FILE = "users.json"

# ---------------- LOAD DATA ----------------
try:
    with open(DATA_FILE, "r") as f:
        users = json.load(f)
except:
    users = {}

def save():
    with open(DATA_FILE, "w") as f:
        json.dump(users, f)

# ---------------- USER SYSTEM ----------------
def get_user(user_id):
    uid = str(user_id)

    if uid not in users:
        users[uid] = {
            "money": 1000,
            "xp": 0,
            "level": 1,
            "last_farm": 0
        }
        save()  # ✅ фикс: новый игрок сразу сохраняется

    return users[uid]

# ---------------- LEVEL SYSTEM ----------------
def add_xp(user):
    user["xp"] += 10

    if user["xp"] >= user["level"] * 100:
        user["xp"] = 0
        user["level"] += 1

# ---------------- COMMANDS ----------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    get_user(update.effective_user.id)

    await update.message.reply_text(
        "🌍 Mini Life Bot v2\n"
        "💰 Экономика активна\n"
        "Напиши /help"
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/balance\n"
        "/farm\n"
        "/dice\n"
        "/guess <1-6>\n"
        "/roulette\n"
        "/rice up/down <bet>\n"
        "/mine\n"
        "/delivery\n"
        "/business\n"
        "/profile"
    )

# ---------------- BALANCE ----------------
async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)

    await update.message.reply_text(
        f"💰 {user['money']}$\n"
        f"⭐ Level: {user['level']}\n"
        f"XP: {user['xp']}"
    )

# ---------------- FARM ----------------
async def farm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)

    now = time.time()

    if now - user["last_farm"] < 7200:
        await update.message.reply_text("⏳ Подожди 2 часа")
        return

    user["money"] += 1000
    user["last_farm"] = now

    add_xp(user)
    save()

    await update.message.reply_text("🌾 +1000$")

# ---------------- DICE ----------------
async def dice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)

    roll = random.randint(1, 6)

    if roll == 6:
        user["money"] += 500
        msg = "WIN +500$"
    else:
        user["money"] -= 100
        msg = "LOSE -100$"

    add_xp(user)
    save()

    await update.message.reply_text(f"🎲 {roll} → {msg}")

# ---------------- GUESS ----------------
async def guess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)

    if not context.args:
        await update.message.reply_text("Используй: /guess 1-6")
        return

    try:
        choice = int(context.args[0])
    except:
        await update.message.reply_text("❌ Введи число 1-6")
        return

    if choice < 1 or choice > 6:
        await update.message.reply_text("❌ Только 1-6")
        return

    target = random.randint(1, 6)

    if choice == target:
        user["money"] += 1000
        msg = "WIN +1000$"
    else:
        user["money"] -= 200
        msg = "LOSE -200$"

    add_xp(user)
    save()

    await update.message.reply_text(f"❓ Было {target} → {msg}")

# ---------------- ROULETTE ----------------
async def roulette(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)

    if random.choice([True, False]):
        user["money"] += 800
        msg = "WIN +800$"
    else:
        user["money"] -= 300
        msg = "LOSE -300$"

    add_xp(user)
    save()

    await update.message.reply_text(f"🎰 {msg}")

# ---------------- RICE MARKET ----------------
async def rice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)

    if len(context.args) < 2:
        await update.message.reply_text("Используй: /rice up 100")
        return

    direction = context.args[0]
    if direction not in ["up", "down"]:
        await update.message.reply_text("❌ up или down")
        return

    try:
        bet = int(context.args[1])
    except:
        await update.message.reply_text("❌ ставка числом")
        return

    if bet <= 0:
        await update.message.reply_text("❌ ставка > 0")
        return

    if user["money"] < bet:
        await update.message.reply_text("❌ нет денег")
        return

    result = random.choice(["up", "down"])

    if direction == result:
        user["money"] += bet * 2
        msg = f"WIN +{bet*2}$"
    else:
        user["money"] -= bet
        msg = f"LOSE -{bet}$"

    add_xp(user)
    save()

    await update.message.reply_text(f"📈 Было {result} → {msg}")

# ---------------- WORKS ----------------
async def mine(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)

    earn = random.randint(200, 800)
    user["money"] += earn

    add_xp(user)
    save()

    await update.message.reply_text(f"⛏ +{earn}$")

async def delivery(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)

    earn = random.randint(300, 1000)
    user["money"] += earn

    add_xp(user)
    save()

    await update.message.reply_text(f"🚚 +{earn}$")

async def business(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)

    earn = random.randint(500, 1500)
    user["money"] += earn

    add_xp(user)
    save()

    await update.message.reply_text(f"💼 +{earn}$")

# ---------------- PROFILE ----------------
async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)

    await update.message.reply_text(
        f"📄 PROFILE\n"
        f"💰 {user['money']}$\n"
        f"⭐ Level {user['level']}\n"
        f"XP {user['xp']}"
    )

# ---------------- MAIN ----------------
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("balance", balance))
    app.add_handler(CommandHandler("farm", farm))
    app.add_handler(CommandHandler("dice", dice))
    app.add_handler(CommandHandler("guess", guess))
    app.add_handler(CommandHandler("roulette", roulette))
    app.add_handler(CommandHandler("rice", rice))
    app.add_handler(CommandHandler("mine", mine))
    app.add_handler(CommandHandler("delivery", delivery))
    app.add_handler(CommandHandler("business", business))
    app.add_handler(CommandHandler("profile", profile))

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()