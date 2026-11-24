import logging
import time
import json
import os
import random
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)

# ====================== НАСТРОЙКИ ======================
TOKEN = "СЮДА_ВСТАВЬ_ТОКЕН_ОТ_BOTFATHER"
ADMIN_ID = 123456789          # ← ОБЯЗАТЕЛЬНО ЗАМЕНИ НА СВОЙ ID
SAVE_FILE = "users.json"

# ====================== ДАННЫЕ ======================

JOBS = {
    "loader":        {"name": "Грузчик",            "min_level": 1,  "pay_min": 120,   "pay_max": 280,   "cooldown": 6},
    "cashier":       {"name": "Кассир",             "min_level": 2,  "pay_min": 250,   "pay_max": 480,   "cooldown": 7},
    "driver":        {"name": "Водитель",           "min_level": 4,  "pay_min": 400,   "pay_max": 750,   "cooldown": 8},
    "manager":       {"name": "Менеджер",           "min_level": 7,  "pay_min": 700,   "pay_max": 1300,  "cooldown": 9},
    "programmer":    {"name": "Программист",        "min_level": 10, "pay_min": 1200,  "pay_max": 2400,  "cooldown": 10},
    "director":      {"name": "Директор",           "min_level": 15, "pay_min": 2500,  "pay_max": 5000,  "cooldown": 12},
    "oligarch_work": {"name": "Совет директоров",   "min_level": 25, "pay_min": 8000,  "pay_max": 18000, "cooldown": 15},
}

BUSINESSES = {
    "kiosk":       {"name": "Киоск",               "price": 5_000,       "income": 90},
    "shop":        {"name": "Магазин",             "price": 25_000,      "income": 380},
    "cafe":        {"name": "Кафе",                "price": 90_000,      "income": 1_400},
    "restaurant":  {"name": "Ресторан",            "price": 280_000,     "income": 4_500},
    "car_wash":    {"name": "Автомойка",           "price": 450_000,     "income": 7_200},
    "hotel":       {"name": "Гостиница",           "price": 1_200_000,   "income": 18_000},
    "factory":     {"name": "Завод",               "price": 3_500_000,   "income": 45_000},
    "it_company":  {"name": "IT-компания",         "price": 8_000_000,   "income": 95_000},
    "bank":        {"name": "Банк",                "price": 25_000_000,  "income": 280_000},
    "holding":     {"name": "Холдинг",             "price": 80_000_000,  "income": 850_000},
    "oil_company": {"name": "Нефтяная компания",   "price": 300_000_000, "income": 2_800_000},
}

CARS = {
    "lada":       {"name": "Лада Гранта",         "price": 800_000},
    "solaris":    {"name": "Hyundai Solaris",     "price": 1_600_000},
    "camry":      {"name": "Toyota Camry",        "price": 3_800_000},
    "bmw5":       {"name": "BMW 5 Series",        "price": 7_500_000},
    "mercedes_s": {"name": "Mercedes S-Class",    "price": 15_000_000},
    "porsche":    {"name": "Porsche 911",         "price": 22_000_000},
    "lambo":      {"name": "Lamborghini Huracan", "price": 35_000_000},
    "bugatti":    {"name": "Bugatti Chiron",      "price": 180_000_000},
}

HOUSES = {
    "apartment": {"name": "Квартира-студия",         "price": 3_500_000},
    "flat":      {"name": "Трёхкомнатная квартира",  "price": 9_000_000},
    "townhouse": {"name": "Таунхаус",                "price": 18_000_000},
    "cottage":   {"name": "Коттедж",                 "price": 35_000_000},
    "mansion":   {"name": "Особняк",                 "price": 90_000_000},
    "villa":     {"name": "Вилла на море",           "price": 250_000_000},
    "castle":    {"name": "Замок",                   "price": 800_000_000},
}

YACHTS = {
    "small_yacht":   {"name": "Небольшая яхта",      "price": 45_000_000},
    "motor_yacht":   {"name": "Моторная яхта",       "price": 120_000_000},
    "luxury_yacht":  {"name": "Люксовая яхта",       "price": 350_000_000},
    "mega_yacht":    {"name": "Мега-яхта",           "price": 900_000_000},
    "superyacht":    {"name": "Суперъяхта",          "price": 2_500_000_000},
}

PLANES = {
    "cessna":        {"name": "Cessna",              "price": 80_000_000},
    "business_jet":  {"name": "Бизнес-джет",         "price": 280_000_000},
    "gulfstream":    {"name": "Gulfstream G650",     "price": 650_000_000},
    "private_boeing":{"name": "Частный Boeing",      "price": 1_800_000_000},
    "airbus_acj":    {"name": "Airbus ACJ",          "price": 4_500_000_000},
}

LOCATIONS = {
    "ufa":      {"name": "Уфа",             "country": "Россия",         "price": 0,           "multiplier": 1.0},
    "kazan":    {"name": "Казань",          "country": "Россия",         "price": 150_000,     "multiplier": 1.1},
    "ekb":      {"name": "Екатеринбург",    "country": "Россия",         "price": 300_000,     "multiplier": 1.15},
    "spb":      {"name": "Санкт-Петербург", "country": "Россия",         "price": 800_000,     "multiplier": 1.25},
    "moscow":   {"name": "Москва",          "country": "Россия",         "price": 2_500_000,   "multiplier": 1.4},
    "dubai":    {"name": "Дубай",           "country": "ОАЭ",            "price": 8_000_000,   "multiplier": 1.7},
    "istanbul": {"name": "Стамбул",         "country": "Турция",         "price": 4_000_000,   "multiplier": 1.35},
    "berlin":   {"name": "Берлин",          "country": "Германия",       "price": 12_000_000,  "multiplier": 1.6},
    "london":   {"name": "Лондон",          "country": "Великобритания", "price": 25_000_000,  "multiplier": 1.85},
    "newyork":  {"name": "Нью-Йорк",        "country": "США",            "price": 40_000_000,  "multiplier": 2.1},
    "monaco":   {"name": "Монако",          "country": "Монако",         "price": 120_000_000, "multiplier": 2.5},
}

STATUSES = [
    {"name": "Нищий",            "min_money": 0},
    {"name": "Бедный",           "min_money": 15_000},
    {"name": "Средний класс",    "min_money": 150_000},
    {"name": "Обеспеченный",     "min_money": 800_000},
    {"name": "Богатый",          "min_money": 5_000_000},
    {"name": "Очень богатый",    "min_money": 25_000_000},
    {"name": "Миллионер",        "min_money": 100_000_000},
    {"name": "Мультимиллионер",  "min_money": 500_000_000},
    {"name": "Миллиардер",       "min_money": 2_000_000_000},
]

# ====================== КЛАВИАТУРА ======================

def main_keyboard():
    keyboard = [
        [KeyboardButton("💼 Работать"), KeyboardButton("📊 Профиль")],
        [KeyboardButton("🏪 Бизнесы"), KeyboardButton("🚗 Машины")],
        [KeyboardButton("🏠 Дома"), KeyboardButton("🚤 Яхты")],
        [KeyboardButton("✈️ Самолёты"), KeyboardButton("🌍 Город")],
        [KeyboardButton("💰 Доход"), KeyboardButton("🎁 Бонус")],
        [KeyboardButton("🏆 Топ"), KeyboardButton("📜 Статусы")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# ====================== СОХРАНЕНИЕ ======================

def load_users():
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r", encoding="utf-8") as f:
                return {int(k): v for k, v in json.load(f).items()}
        except:
            return {}
    return {}

def save_users():
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

users = load_users()

def get_user(user_id: int, username=None, full_name=None):
    if user_id not in users:
        users[user_id] = {
            "registered": False,
            "username": username,
            "full_name": full_name or "Игрок",
            "money": 0,
            "level": 1,
            "location": "ufa",
            "businesses": {k: 0 for k in BUSINESSES},
            "cars": {k: 0 for k in CARS},
            "houses": {k: 0 for k in HOUSES},
            "yachts": {k: 0 for k in YACHTS},
            "planes": {k: 0 for k in PLANES},
            "last_work": 0,
            "last_daily": 0,
            "daily_streak": 0,
            "is_admin": user_id == ADMIN_ID,
        }
        save_users()
    else:
        u = users[user_id]
        for k in BUSINESSES: u["businesses"].setdefault(k, 0)
        for k in CARS: u["cars"].setdefault(k, 0)
        for k in HOUSES: u["houses"].setdefault(k, 0)
        for k in YACHTS: u.setdefault("yachts", {})[k] = u.get("yachts", {}).get(k, 0)
        for k in PLANES: u.setdefault("planes", {})[k] = u.get("planes", {}).get(k, 0)
        u.setdefault("location", "ufa")
        u.setdefault("last_work", 0)
        u.setdefault("last_daily", 0)
        u.setdefault("daily_streak", 0)
    return users[user_id]

def is_admin(uid): return uid == ADMIN_ID

def get_status(user):
    if user.get("is_admin"): return "👑 Создатель"
    money = user["money"]
    current = STATUSES[0]["name"]
    for s in STATUSES:
        if money >= s["min_money"]:
            current = s["name"]
        else:
            break
    return current

def calculate_passive_income(user):
    base = sum(BUSINESSES[k]["income"] * v for k, v in user["businesses"].items())
    mult = LOCATIONS.get(user.get("location", "ufa"), LOCATIONS["ufa"])["multiplier"]
    return int(base * mult)

# ====================== ИГРОВЫЕ КОМАНДЫ ======================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id, update.effective_user.username, update.effective_user.full_name)
    if not user["registered"]:
        user["registered"] = True
        save_users()
        text = f"Добро пожаловать, *{user['full_name']}*!\nТы начинаешь с нуля. Стань самым богатым!"
        if is_admin(update.effective_user.id):
            text += "\n\n👑 Ты Создатель."
    else:
        loc = LOCATIONS[user["location"]]
        text = f"С возвращением!\nСтатус: *{get_status(user)}*\nГород: *{loc['name']}*\nДеньги: *{user['money']:,} ₽*"
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=main_keyboard())

async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    if not user["registered"]:
        return await update.message.reply_text("Нажми /start")

    loc = LOCATIONS[user["location"]]
    passive = calculate_passive_income(user)

    def fmt(items, data):
        lines = [f"• {data[k]['name']}: {v}" for k, v in items.items() if v > 0]
        return "\n".join(lines) if lines else "нет"

    text = (
        f"*Профиль*\n\n"
        f"Имя: {user['full_name']}\n"
        f"Статус: *{get_status(user)}*" + (" 👑" if user.get("is_admin") else "") + "\n"
        f"Уровень: *{user['level']}*\n"
        f"Город: *{loc['name']}* ({loc['country']}) ×{loc['multiplier']}\n"
        f"Деньги: *{user['money']:,} ₽*\n"
        f"Пассив: *{passive:,} ₽/час*\n"
        f"Серия бонусов: *{user.get('daily_streak', 0)}*\n\n"
        f"*Бизнесы:*\n{fmt(user['businesses'], BUSINESSES)}\n\n"
        f"*Машины:*\n{fmt(user['cars'], CARS)}\n\n"
        f"*Дома:*\n{fmt(user['houses'], HOUSES)}\n\n"
        f"*Яхты:*\n{fmt(user.get('yachts', {}), YACHTS)}\n\n"
        f"*Самолёты:*\n{fmt(user.get('planes', {}), PLANES)}"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def statuses_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    text = "*Статусы:*\n\n"
    for s in STATUSES:
        mark = "✅" if user["money"] >= s["min_money"] else "🔒"
        text += f"{mark} {s['name']} — от {s['min_money']:,} ₽\n"
    text += f"\nТвой: *{get_status(user)}*"
    await update.message.reply_text(text, parse_mode="Markdown")

async def work_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    if not user["registered"]:
        return await update.message.reply_text("Сначала /start")

    keyboard = []
    for jid, job in JOBS.items():
        avail = user["level"] >= job["min_level"]
        mark = "✅" if avail else f"🔒{job['min_level']}ур"
        text = f"{job['name']} ({job['pay_min']}-{job['pay_max']}₽) {mark}"
        keyboard.append([InlineKeyboardButton(text, callback_data=f"job_{jid}")])
    await update.message.reply_text("Выбери работу:", reply_markup=InlineKeyboardMarkup(keyboard))

async def collect(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    if not user["registered"]:
        return await update.message.reply_text("Сначала /start")
    income = calculate_passive_income(user)
    if income == 0:
        return await update.message.reply_text("Нет бизнесов.")
    user["money"] += income
    save_users()
    await update.message.reply_text(f"Получено: *{income:,} ₽*\nБаланс: *{user['money']:,} ₽*", parse_mode="Markdown")

async def daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    if not user["registered"]:
        return await update.message.reply_text("Сначала /start")

    now = time.time()
    last = user.get("last_daily", 0)

    if now - last < 20 * 3600:  # 20 часов
        left = int((20 * 3600 - (now - last)) / 3600)
        return await update.message.reply_text(f"Бонус ещё недоступен.\nОсталось примерно {left} ч.")

    # Серия
    if now - last < 48 * 3600:
        user["daily_streak"] = user.get("daily_streak", 0) + 1
    else:
        user["daily_streak"] = 1

    streak = user["daily_streak"]
    base = 3000 + user["level"] * 400
    bonus = int(base * (1 + streak * 0.12))
    user["money"] += bonus
    user["last_daily"] = now
    save_users()

    await update.message.reply_text(
        f"🎁 Ежедневный бонус!\n"
        f"Серия: *{streak}*\n"
        f"Получено: *{bonus:,} ₽*\n"
        f"Баланс: *{user['money']:,} ₽*",
        parse_mode="Markdown"
    )

async def top_players(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not users:
        return await update.message.reply_text("Пока никто не играет.")

    sorted_users = sorted(users.values(), key=lambda x: x["money"], reverse=True)[:10]
    text = "*🏆 Топ-10 игроков:*\n\n"
    for i, u in enumerate(sorted_users, 1):
        medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, f"{i}.")
        name = u.get("full_name", "Игрок")
        text += f"{medal} {name} — *{u['money']:,} ₽*\n"
    await update.message.reply_text(text, parse_mode="Markdown")

# ---------- МАГАЗИНЫ ----------

async def shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    keyboard = [[InlineKeyboardButton(f"{v['name']} — {v['price']:,} ₽ (×{user['businesses'][k]})", callback_data=f"buybiz_{k}")] for k, v in BUSINESSES.items()]
    await update.message.reply_text("Бизнесы:", reply_markup=InlineKeyboardMarkup(keyboard))

async def cars_shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    keyboard = [[InlineKeyboardButton(f"{v['name']} — {v['price']:,} ₽ (×{user['cars'][k]})", callback_data=f"buycar_{k}")] for k, v in CARS.items()]
    await update.message.reply_text("Машины:", reply_markup=InlineKeyboardMarkup(keyboard))

async def houses_shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    keyboard = [[InlineKeyboardButton(f"{v['name']} — {v['price']:,} ₽ (×{user['houses'][k]})", callback_data=f"buyhouse_{k}")] for k, v in HOUSES.items()]
    await update.message.reply_text("Дома:", reply_markup=InlineKeyboardMarkup(keyboard))

async def yachts_shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    keyboard = [[InlineKeyboardButton(f"{v['name']} — {v['price']:,} ₽ (×{user.get('yachts', {}).get(k, 0)})", callback_data=f"buyyacht_{k}")] for k, v in YACHTS.items()]
    await update.message.reply_text("Яхты:", reply_markup=InlineKeyboardMarkup(keyboard))

async def planes_shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    keyboard = [[InlineKeyboardButton(f"{v['name']} — {v['price']:,} ₽ (×{user.get('planes', {}).get(k, 0)})", callback_data=f"buyplane_{k}")] for k, v in PLANES.items()]
    await update.message.reply_text("Самолёты:", reply_markup=InlineKeyboardMarkup(keyboard))

async def city_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    current = user["location"]
    keyboard = []
    for lid, loc in LOCATIONS.items():
        mark = " ✅" if lid == current else ""
        keyboard.append([InlineKeyboardButton(f"{loc['name']} ({loc['country']}) — {loc['price']:,} ₽{mark}", callback_data=f"moveto_{lid}")])
    await update.message.reply_text(f"Сейчас: *{LOCATIONS[current]['name']}*", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

# ---------- CALLBACK ----------

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = get_user(query.from_user.id)
    data = query.data

    if data.startswith("job_"):
        job_id = data[4:]
        job = JOBS.get(job_id)
        if not job: return
        if user["level"] < job["min_level"]:
            return await query.answer(f"Нужен {job['min_level']} уровень!", show_alert=True)
        now = time.time()
        if now - user["last_work"] < job["cooldown"]:
            left = int(job["cooldown"] - (now - user["last_work"]))
            return await query.answer(f"Подожди {left} сек.", show_alert=True)

        loc_mult = LOCATIONS[user["location"]]["multiplier"]
        pay = int(random.randint(job["pay_min"], job["pay_max"]) * loc_mult)
        user["last_work"] = now
        user["money"] += pay

        level_up = ""
        if user["level"] < 100 and random.random() < 0.17:
            user["level"] += 1
            level_up = f"\n\n🎉 Уровень → *{user['level']}*!"

        save_users()
        await query.edit_message_text(f"Работа: *{job['name']}*\nЗаработано: *{pay:,} ₽*\nБаланс: *{user['money']:,} ₽*{level_up}", parse_mode="Markdown")
        return

    # Покупки
    mapping = {
        "buybiz_": ("businesses", BUSINESSES),
        "buycar_": ("cars", CARS),
        "buyhouse_": ("houses", HOUSES),
        "buyyacht_": ("yachts", YACHTS),
        "buyplane_": ("planes", PLANES),
    }

    for prefix, (field, catalog) in mapping.items():
        if data.startswith(prefix):
            item_id = data[len(prefix):]
            if item_id not in catalog: return
            price = catalog[item_id]["price"]
            if user["money"] < price:
                return await query.edit_message_text(f"Не хватает ({price:,} ₽)")
            user["money"] -= price
            user[field][item_id] = user[field].get(item_id, 0) + 1
            save_users()
            await query.edit_message_text(f"Куплено: *{catalog[item_id]['name']}*\nОстаток: *{user['money']:,} ₽*", parse_mode="Markdown")
            return

    if data.startswith("moveto_"):
        loc_id = data[7:]
        if loc_id not in LOCATIONS or loc_id == user["location"]:
            return await query.edit_message_text("Ты уже здесь.")
        price = LOCATIONS[loc_id]["price"]
        if user["money"] < price:
            return await query.edit_message_text(f"Не хватает ({price:,} ₽)")
        user["money"] -= price
        user["location"] = loc_id
        save_users()
        loc = LOCATIONS[loc_id]
        await query.edit_message_text(f"Переехал в *{loc['name']}*\nМножитель: ×{loc['multiplier']}\nОстаток: *{user['money']:,} ₽*", parse_mode="Markdown")

# ---------- КНОПКИ СНИЗУ ----------

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    mapping = {
        "💼 Работать": work_menu,
        "📊 Профиль": status_cmd,
        "🏪 Бизнесы": shop,
        "🚗 Машины": cars_shop,
        "🏠 Дома": houses_shop,
        "🚤 Яхты": yachts_shop,
        "✈️ Самолёты": planes_shop,
        "🌍 Город": city_menu,
        "💰 Доход": collect,
        "🎁 Бонус": daily,
        "🏆 Топ": top_players,
        "📜 Статусы": statuses_list,
    }
    handler = mapping.get(text)
    if handler:
        await handler(update, context)

# ====================== АДМИН ======================

async def admin_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return await update.message.reply_text("Нет доступа.")
    await update.message.reply_text(
        "*Админ-команды:*\n/setmoney /addmoney /setlevel\n/give <id> <сумма>\n/resetme /users",
        parse_mode="Markdown"
    )

async def set_money(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    if not context.args: return await update.message.reply_text("Пример: /setmoney 10000000")
    try:
        user = get_user(update.effective_user.id)
        user["money"] = int(context.args[0])
        save_users()
        await update.message.reply_text(f"Баланс: *{user['money']:,} ₽*", parse_mode="Markdown")
    except: await update.message.reply_text("Ошибка")

async def add_money(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    if not context.args: return await update.message.reply_text("Пример: /addmoney 5000000")
    try:
        user = get_user(update.effective_user.id)
        user["money"] += int(context.args[0])
        save_users()
        await update.message.reply_text(f"Теперь: *{user['money']:,} ₽*", parse_mode="Markdown")
    except: await update.message.reply_text("Ошибка")

async def set_level(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    if not context.args: return await update.message.reply_text("Пример: /setlevel 30")
    try:
        user = get_user(update.effective_user.id)
        user["level"] = max(1, int(context.args[0]))
        save_users()
        await update.message.reply_text(f"Уровень: *{user['level']}*", parse_mode="Markdown")
    except: await update.message.reply_text("Ошибка")

async def give_money(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    if len(context.args) < 2: return await update.message.reply_text("Пример: /give 123456789 1000000")
    try:
        target, amount = int(context.args[0]), int(context.args[1])
        if target not in users: return await update.message.reply_text("Игрок не найден")
        users[target]["money"] += amount
        save_users()
        await update.message.reply_text(f"Выдано {amount:,} ₽")
    except: await update.message.reply_text("Ошибка")

async def reset_me(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    user = get_user(update.effective_user.id)
    user.update({
        "money": 0, "level": 1, "location": "ufa",
        "businesses": {k: 0 for k in BUSINESSES},
        "cars": {k: 0 for k in CARS},
        "houses": {k: 0 for k in HOUSES},
        "yachts": {k: 0 for k in YACHTS},
        "planes": {k: 0 for k in PLANES},
        "last_work": 0, "last_daily": 0, "daily_streak": 0
    })
    save_users()
    await update.message.reply_text("Прогресс полностью сброшен.")

async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    text = "*Игроки:*\n\n"
    for uid, u in users.items():
        mark = " 👑" if u.get("is_admin") else ""
        text += f"`{uid}` {u.get('full_name')}{mark} — {u['money']:,} ₽\n"
    await update.message.reply_text(text or "Пусто", parse_mode="Markdown")

# ====================== ЗАПУСК ======================

def main():
    logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status_cmd))
    app.add_handler(CommandHandler("statuses", statuses_list))
    app.add_handler(CommandHandler("work", work_menu))
    app.add_handler(CommandHandler("collect", collect))
    app.add_handler(CommandHandler("daily", daily))
    app.add_handler(CommandHandler("top", top_players))
    app.add_handler(CommandHandler("shop", shop))
    app.add_handler(CommandHandler("cars", cars_shop))
    app.add_handler(CommandHandler("houses", houses_shop))
    app.add_handler(CommandHandler("yachts", yachts_shop))
    app.add_handler(CommandHandler("planes", planes_shop))
    app.add_handler(CommandHandler("city", city_menu))

    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, button_handler))

    app.add_handler(CommandHandler("admin", admin_help))
    app.add_handler(CommandHandler("setmoney", set_money))
    app.add_handler(CommandHandler("addmoney", add_money))
    app.add_handler(CommandHandler("setlevel", set_level))
    app.add_handler(CommandHandler("give", give_money))
    app.add_handler(CommandHandler("resetme", reset_me))
    app.add_handler(CommandHandler("users", list_users))

    print("Бот полностью запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()
