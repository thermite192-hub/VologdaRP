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
    "loader":        {"name": "Грузчик",            "min_level": 1,  "pay_min": 120,   "pay_max": 280,   "cooldown": 8},
    "cashier":       {"name": "Кассир",             "min_level": 2,  "pay_min": 250,   "pay_max": 480,   "cooldown": 9},
    "courier":       {"name": "Курьер",             "min_level": 3,  "pay_min": 320,   "pay_max": 580,   "cooldown": 9},
    "driver":        {"name": "Водитель",           "min_level": 4,  "pay_min": 400,   "pay_max": 750,   "cooldown": 10},
    "seller":        {"name": "Продавец",           "min_level": 5,  "pay_min": 500,   "pay_max": 900,   "cooldown": 10},
    "manager":       {"name": "Менеджер",           "min_level": 7,  "pay_min": 700,   "pay_max": 1300,  "cooldown": 11},
    "engineer":      {"name": "Инженер",            "min_level": 9,  "pay_min": 950,   "pay_max": 1800,  "cooldown": 12},
    "programmer":    {"name": "Программист",        "min_level": 10, "pay_min": 1200,  "pay_max": 2400,  "cooldown": 12},
    "director":      {"name": "Директор",           "min_level": 15, "pay_min": 2500,  "pay_max": 5000,  "cooldown": 14},
    "oligarch_work": {"name": "Совет директоров",   "min_level": 25, "pay_min": 8000,  "pay_max": 18000, "cooldown": 18},
}

# Бизнесы: available_in — в каких городах можно купить
BUSINESSES = {
    # Вологда и малые города
    "kiosk":       {"name": "Киоск",               "price": 5_000,       "income": 90,     "available_in": ["vologda", "kazan", "ekb", "ufa"]},
    "shop":        {"name": "Магазин",             "price": 25_000,      "income": 380,    "available_in": ["vologda", "kazan", "ekb", "ufa", "spb"]},
    "cafe":        {"name": "Кафе",                "price": 90_000,      "income": 1_400,  "available_in": ["vologda", "kazan", "ekb", "spb", "moscow"]},
    "auto_service":{"name": "Автосервис",          "price": 180_000,     "income": 2_800,  "available_in": ["vologda", "ekb", "kazan", "spb"]},
    "restaurant":  {"name": "Ресторан",            "price": 280_000,     "income": 4_500,  "available_in": ["kazan", "ekb", "spb", "moscow", "istanbul"]},
    "car_wash":    {"name": "Автомойка",           "price": 450_000,     "income": 7_200,  "available_in": ["ekb", "spb", "moscow", "istanbul", "berlin"]},
    "hotel":       {"name": "Гостиница",           "price": 1_200_000,   "income": 18_000, "available_in": ["spb", "moscow", "istanbul", "dubai", "berlin"]},
    "factory":     {"name": "Завод",               "price": 3_500_000,   "income": 45_000, "available_in": ["ekb", "moscow", "berlin", "london"]},
    "it_company":  {"name": "IT-компания",         "price": 8_000_000,   "income": 95_000, "available_in": ["moscow", "berlin", "london", "newyork"]},
    "bank":        {"name": "Банк",                "price": 25_000_000,  "income": 280_000,"available_in": ["moscow", "london", "newyork", "monaco"]},
    "holding":     {"name": "Холдинг",             "price": 80_000_000,  "income": 850_000,"available_in": ["london", "newyork", "monaco", "dubai"]},
    "oil_company": {"name": "Нефтяная компания",   "price": 300_000_000, "income": 2_800_000,"available_in": ["moscow", "dubai", "london"]},
    "tech_park":   {"name": "Технопарк",           "price": 45_000_000,  "income": 520_000,"available_in": ["moscow", "berlin", "newyork"]},
    "casino":      {"name": "Казино",              "price": 120_000_000, "income": 1_400_000,"available_in": ["monaco", "dubai", "macau"]},
    "space_port":  {"name": "Космодром",           "price": 900_000_000, "income": 9_500_000,"available_in": ["dubai", "newyork", "monaco"]},
}

CARS = {
    # Доступны почти везде, но премиум — в крупных городах
    "lada":       {"name": "Лада Гранта",         "price": 800_000,     "available_in": ["vologda", "ufa", "kazan", "ekb", "spb", "moscow"]},
    "solaris":    {"name": "Hyundai Solaris",     "price": 1_600_000,   "available_in": ["vologda", "kazan", "ekb", "spb", "moscow"]},
    "camry":      {"name": "Toyota Camry",        "price": 3_800_000,   "available_in": ["kazan", "ekb", "spb", "moscow", "istanbul"]},
    "bmw3":       {"name": "BMW 3 Series",        "price": 5_200_000,   "available_in": ["spb", "moscow", "berlin", "istanbul"]},
    "bmw5":       {"name": "BMW 5 Series",        "price": 7_500_000,   "available_in": ["moscow", "berlin", "london", "dubai"]},
    "mercedes_e": {"name": "Mercedes E-Class",    "price": 9_800_000,   "available_in": ["moscow", "berlin", "london", "dubai"]},
    "mercedes_s": {"name": "Mercedes S-Class",    "price": 15_000_000,  "available_in": ["moscow", "london", "dubai", "newyork", "monaco"]},
    "porsche":    {"name": "Porsche 911",         "price": 22_000_000,  "available_in": ["dubai", "london", "newyork", "monaco"]},
    "lambo":      {"name": "Lamborghini Huracan", "price": 35_000_000,  "available_in": ["dubai", "monaco", "newyork"]},
    "ferrari":    {"name": "Ferrari 488",         "price": 42_000_000,  "available_in": ["monaco", "dubai", "newyork"]},
    "bugatti":    {"name": "Bugatti Chiron",      "price": 180_000_000, "available_in": ["monaco", "dubai"]},
    "rolls":      {"name": "Rolls-Royce Phantom", "price": 55_000_000,  "available_in": ["london", "monaco", "dubai"]},
}

HOUSES = {
    "apartment": {"name": "Квартира-студия",         "price": 3_500_000,   "available_in": ["vologda", "ufa", "kazan", "ekb"]},
    "flat":      {"name": "Трёхкомнатная квартира",  "price": 9_000_000,   "available_in": ["vologda", "kazan", "ekb", "spb"]},
    "townhouse": {"name": "Таунхаус",                "price": 18_000_000,  "available_in": ["ekb", "spb", "moscow", "istanbul"]},
    "cottage":   {"name": "Коттедж",                 "price": 35_000_000,  "available_in": ["spb", "moscow", "berlin", "istanbul"]},
    "mansion":   {"name": "Особняк",                 "price": 90_000_000,  "available_in": ["moscow", "berlin", "london", "dubai"]},
    "villa":     {"name": "Вилла на море",           "price": 250_000_000, "available_in": ["dubai", "istanbul", "monaco"]},
    "penthouse": {"name": "Пентхаус",                "price": 180_000_000, "available_in": ["moscow", "london", "newyork", "dubai"]},
    "castle":    {"name": "Замок",                   "price": 800_000_000, "available_in": ["london", "monaco", "berlin"]},
    "island":    {"name": "Частный остров",          "price": 2_500_000_000,"available_in": ["monaco", "dubai"]},
}

YACHTS = {
    "small_yacht":   {"name": "Небольшая яхта",      "price": 45_000_000,  "available_in": ["spb", "istanbul", "dubai"]},
    "motor_yacht":   {"name": "Моторная яхта",       "price": 120_000_000, "available_in": ["istanbul", "dubai", "monaco"]},
    "luxury_yacht":  {"name": "Люксовая яхта",       "price": 350_000_000, "available_in": ["dubai", "monaco", "newyork"]},
    "mega_yacht":    {"name": "Мега-яхта",           "price": 900_000_000, "available_in": ["monaco", "dubai"]},
    "superyacht":    {"name": "Суперъяхта",          "price": 2_500_000_000,"available_in": ["monaco"]},
}

PLANES = {
    "cessna":        {"name": "Cessna",              "price": 80_000_000,  "available_in": ["moscow", "berlin", "dubai"]},
    "business_jet":  {"name": "Бизнес-джет",         "price": 280_000_000, "available_in": ["moscow", "london", "dubai", "newyork"]},
    "gulfstream":    {"name": "Gulfstream G650",     "price": 650_000_000, "available_in": ["london", "dubai", "newyork", "monaco"]},
    "private_boeing":{"name": "Частный Boeing",      "price": 1_800_000_000,"available_in": ["dubai", "newyork", "monaco"]},
    "airbus_acj":    {"name": "Airbus ACJ",          "price": 4_500_000_000,"available_in": ["monaco", "dubai"]},
    "helicopter":    {"name": "Вертолёт",            "price": 45_000_000,  "available_in": ["moscow", "spb", "dubai", "monaco"]},
}

LOCATIONS = {
    "vologda":  {"name": "Вологда",          "country": "Россия",         "price": 0,           "multiplier": 1.0},
    "ufa":      {"name": "Уфа",              "country": "Россия",         "price": 80_000,      "multiplier": 1.05},
    "kazan":    {"name": "Казань",           "country": "Россия",         "price": 150_000,     "multiplier": 1.1},
    "ekb":      {"name": "Екатеринбург",     "country": "Россия",         "price": 300_000,     "multiplier": 1.15},
    "spb":      {"name": "Санкт-Петербург",  "country": "Россия",         "price": 800_000,     "multiplier": 1.25},
    "moscow":   {"name": "Москва",           "country": "Россия",         "price": 2_500_000,   "multiplier": 1.4},
    "istanbul": {"name": "Стамбул",          "country": "Турция",         "price": 4_000_000,   "multiplier": 1.35},
    "berlin":   {"name": "Берлин",           "country": "Германия",       "price": 12_000_000,  "multiplier": 1.6},
    "dubai":    {"name": "Дубай",            "country": "ОАЭ",            "price": 8_000_000,   "multiplier": 1.7},
    "london":   {"name": "Лондон",           "country": "Великобритания", "price": 25_000_000,  "multiplier": 1.85},
    "newyork":  {"name": "Нью-Йорк",         "country": "США",            "price": 40_000_000,  "multiplier": 2.1},
    "monaco":   {"name": "Монако",           "country": "Монако",         "price": 120_000_000, "multiplier": 2.5},
    "macau":    {"name": "Макао",            "country": "Китай",          "price": 55_000_000,  "multiplier": 2.0},
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
    {"name": "Олигарх",          "min_money": 10_000_000_000},
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
            "location": "vologda",
            "businesses": {k: 0 for k in BUSINESSES},
            "cars": {k: 0 for k in CARS},
            "houses": {k: 0 for k in HOUSES},
            "yachts": {k: 0 for k in YACHTS},
            "planes": {k: 0 for k in PLANES},
            "last_work": 0,
            "last_daily": 0,
            "daily_streak": 0,
            "is_admin": user_id == ADMIN_ID,
            # для мини-игры
            "pending_job": None,
        }
        save_users()
    else:
        u = users[user_id]
        for k in BUSINESSES: u["businesses"].setdefault(k, 0)
        for k in CARS: u["cars"].setdefault(k, 0)
        for k in HOUSES: u["houses"].setdefault(k, 0)
        for k in YACHTS: u.setdefault("yachts", {})[k] = u.get("yachts", {}).get(k, 0)
        for k in PLANES: u.setdefault("planes", {})[k] = u.get("planes", {}).get(k, 0)
        u.setdefault("location", "vologda")
        u.setdefault("last_work", 0)
        u.setdefault("last_daily", 0)
        u.setdefault("daily_streak", 0)
        u.setdefault("pending_job", None)
        # миграция старых игроков из уфы
        if u.get("location") == "ufa" and u.get("money", 0) == 0 and u.get("level", 1) == 1:
            u["location"] = "vologda"
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
    mult = LOCATIONS.get(user.get("location", "vologda"), LOCATIONS["vologda"])["multiplier"]
    return int(base * mult)

def item_available(item, location):
    """Проверяет, доступен ли предмет в текущем городе"""
    available = item.get("available_in")
    if not available:
        return True
    return location in available

# ====================== ИГРОВЫЕ КОМАНДЫ ======================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id, update.effective_user.username, update.effective_user.full_name)
    if not user["registered"]:
        user["registered"] = True
        save_users()
        text = (
            f"Добро пожаловать, *{user['full_name']}*!\n"
            f"Ты начинаешь в *Вологде* с нуля.\n"
            f"Переезжай в другие города, чтобы открывать новые бизнесы, дома и транспорт.\n"
            f"Стань самым богатым!"
        )
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
    await update.message.reply_text(
        "Выбери работу:\n⚠️ После выбора будет мини-игра — нужно правильно ответить, чтобы получить полную зарплату!",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def collect(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    if not user["registered"]:
        return await update.message.reply_text("Сначала /start")
    income = calculate_passive_income(user)
    if income == 0:
        return await update.message.reply_text("Нет бизнесов. Купи бизнесы в доступных городах.")
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

# ---------- МАГАЗИНЫ (только доступные в текущем городе) ----------

async def shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    loc = user["location"]
    available = [(k, v) for k, v in BUSINESSES.items() if item_available(v, loc)]
    if not available:
        return await update.message.reply_text("В этом городе пока нет бизнесов для покупки. Переезжай!")
    keyboard = [
        [InlineKeyboardButton(
            f"{v['name']} — {v['price']:,} ₽ (×{user['businesses'][k]})",
            callback_data=f"buybiz_{k}"
        )] for k, v in available
    ]
    await update.message.reply_text(
        f"Бизнесы в *{LOCATIONS[loc]['name']}*:\n(доступны только в определённых городах)",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def cars_shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    loc = user["location"]
    available = [(k, v) for k, v in CARS.items() if item_available(v, loc)]
    if not available:
        return await update.message.reply_text("В этом городе нет машин. Переезжай в более крупный город!")
    keyboard = [
        [InlineKeyboardButton(
            f"{v['name']} — {v['price']:,} ₽ (×{user['cars'][k]})",
            callback_data=f"buycar_{k}"
        )] for k, v in available
    ]
    await update.message.reply_text(
        f"Машины в *{LOCATIONS[loc]['name']}*:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def houses_shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    loc = user["location"]
    available = [(k, v) for k, v in HOUSES.items() if item_available(v, loc)]
    if not available:
        return await update.message.reply_text("В этом городе нет домов. Переезжай!")
    keyboard = [
        [InlineKeyboardButton(
            f"{v['name']} — {v['price']:,} ₽ (×{user['houses'][k]})",
            callback_data=f"buyhouse_{k}"
        )] for k, v in available
    ]
    await update.message.reply_text(
        f"Дома в *{LOCATIONS[loc]['name']}*:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def yachts_shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    loc = user["location"]
    available = [(k, v) for k, v in YACHTS.items() if item_available(v, loc)]
    if not available:
        return await update.message.reply_text("Яхты доступны только в портовых и богатых городах (СПб, Стамбул, Дубай, Монако...).")
    keyboard = [
        [InlineKeyboardButton(
            f"{v['name']} — {v['price']:,} ₽ (×{user.get('yachts', {}).get(k, 0)})",
            callback_data=f"buyyacht_{k}"
        )] for k, v in available
    ]
    await update.message.reply_text(
        f"Яхты в *{LOCATIONS[loc]['name']}*:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def planes_shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    loc = user["location"]
    available = [(k, v) for k, v in PLANES.items() if item_available(v, loc)]
    if not available:
        return await update.message.reply_text("Самолёты и вертолёты доступны в крупных городах (Москва, Дубай, Лондон, Монако...).")
    keyboard = [
        [InlineKeyboardButton(
            f"{v['name']} — {v['price']:,} ₽ (×{user.get('planes', {}).get(k, 0)})",
            callback_data=f"buyplane_{k}"
        )] for k, v in available
    ]
    await update.message.reply_text(
        f"Авиация в *{LOCATIONS[loc]['name']}*:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def city_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    current = user["location"]
    keyboard = []
    for lid, loc in LOCATIONS.items():
        mark = " ✅" if lid == current else ""
        keyboard.append([InlineKeyboardButton(
            f"{loc['name']} ({loc['country']}) — {loc['price']:,} ₽{mark}",
            callback_data=f"moveto_{lid}"
        )])
    await update.message.reply_text(
        f"Сейчас: *{LOCATIONS[current]['name']}*\n\n"
        f"Переезд открывает новые бизнесы, дома и транспорт, которые доступны только в определённых городах.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# ---------- МИНИ-ИГРА ПРИ РАБОТЕ ----------

def generate_minigame():
    """Генерирует простой арифметический вопрос + варианты ответов"""
    a = random.randint(2, 12)
    b = random.randint(2, 12)
    op = random.choice(["+", "-", "*"])
    if op == "+":
        correct = a + b
        question = f"{a} + {b} = ?"
    elif op == "-":
        if a < b:
            a, b = b, a
        correct = a - b
        question = f"{a} − {b} = ?"
    else:
        correct = a * b
        question = f"{a} × {b} = ?"

    # генерируем 3 неправильных ответа
    wrongs = set()
    while len(wrongs) < 3:
        delta = random.randint(1, 8)
        w = correct + random.choice([-1, 1]) * delta
        if w != correct and w > 0:
            wrongs.add(w)
    options = list(wrongs) + [correct]
    random.shuffle(options)
    return question, correct, options

# ---------- CALLBACK ----------

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = get_user(query.from_user.id)
    data = query.data

    # === Выбор работы → запуск мини-игры ===
    if data.startswith("job_"):
        job_id = data[4:]
        job = JOBS.get(job_id)
        if not job:
            return
        if user["level"] < job["min_level"]:
            return await query.answer(f"Нужен {job['min_level']} уровень!", show_alert=True)
        now = time.time()
        if now - user["last_work"] < job["cooldown"]:
            left = int(job["cooldown"] - (now - user["last_work"]))
            return await query.answer(f"Подожди {left} сек.", show_alert=True)

        # Генерируем мини-игру
        question, correct, options = generate_minigame()
        user["pending_job"] = {
            "job_id": job_id,
            "correct": correct,
            "started": now,
        }
        save_users()

        keyboard = [
            [InlineKeyboardButton(str(opt), callback_data=f"mg_{opt}")]
            for opt in options
        ]
        await query.edit_message_text(
            f"Работа: *{job['name']}*\n\n"
            f"🧠 *Мини-игра*\n"
            f"Реши пример, чтобы получить полную зарплату:\n\n"
            f"*{question}*",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return

    # === Ответ на мини-игру ===
    if data.startswith("mg_"):
        pending = user.get("pending_job")
        if not pending:
            return await query.edit_message_text("Сессия работы устарела. Выбери работу заново.")

        try:
            answer = int(data[3:])
        except ValueError:
            return

        job = JOBS.get(pending["job_id"])
        if not job:
            user["pending_job"] = None
            save_users()
            return await query.edit_message_text("Ошибка работы.")

        now = time.time()
        # защита от слишком долгого ответа (2 минуты)
        if now - pending.get("started", 0) > 120:
            user["pending_job"] = None
            save_users()
            return await query.edit_message_text("Время на ответ истекло. Попробуй снова.")

        loc_mult = LOCATIONS[user["location"]]["multiplier"]
        base_pay = random.randint(job["pay_min"], job["pay_max"])
        pay = int(base_pay * loc_mult)

        correct = pending["correct"]
        success = answer == correct

        user["last_work"] = now
        user["pending_job"] = None

        if success:
            user["money"] += pay
            level_up = ""
            if user["level"] < 100 and random.random() < 0.18:
                user["level"] += 1
                level_up = f"\n\n🎉 Уровень → *{user['level']}*!"
            save_users()
            await query.edit_message_text(
                f"✅ Верно! ({correct})\n\n"
                f"Работа: *{job['name']}*\n"
                f"Заработано: *{pay:,} ₽*\n"
                f"Баланс: *{user['money']:,} ₽*{level_up}",
                parse_mode="Markdown"
            )
        else:
            # неправильный ответ — только 25-40% зарплаты
            reduced = int(pay * random.uniform(0.25, 0.40))
            user["money"] += reduced
            save_users()
            await query.edit_message_text(
                f"❌ Неверно! Правильный ответ: *{correct}*\n\n"
                f"Работа: *{job['name']}*\n"
                f"Получено только: *{reduced:,} ₽* (штраф за ошибку)\n"
                f"Баланс: *{user['money']:,} ₽*",
                parse_mode="Markdown"
            )
        return

    # === Покупки ===
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
            if item_id not in catalog:
                return
            item = catalog[item_id]
            # проверяем доступность в текущем городе
            if not item_available(item, user["location"]):
                return await query.edit_message_text("Этот предмет недоступен в твоём городе. Переезжай!")
            price = item["price"]
            if user["money"] < price:
                return await query.edit_message_text(f"Не хватает ({price:,} ₽)")
            user["money"] -= price
            user[field][item_id] = user[field].get(item_id, 0) + 1
            save_users()
            await query.edit_message_text(
                f"Куплено: *{item['name']}*\nОстаток: *{user['money']:,} ₽*",
                parse_mode="Markdown"
            )
            return

    # === Переезд ===
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
        await query.edit_message_text(
            f"Переехал в *{loc['name']}* ({loc['country']})\n"
            f"Множитель дохода: ×{loc['multiplier']}\n"
            f"Остаток: *{user['money']:,} ₽*\n\n"
            f"Теперь тебе доступны новые бизнесы, дома и транспорт этого города!",
            parse_mode="Markdown"
        )

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
        "money": 0, "level": 1, "location": "vologda",
        "businesses": {k: 0 for k in BUSINESSES},
        "cars": {k: 0 for k in CARS},
        "houses": {k: 0 for k in HOUSES},
        "yachts": {k: 0 for k in YACHTS},
        "planes": {k: 0 for k in PLANES},
        "last_work": 0, "last_daily": 0, "daily_streak": 0,
        "pending_job": None,
    })
    save_users()
    await update.message.reply_text("Прогресс полностью сброшен. Ты снова в Вологде.")

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
