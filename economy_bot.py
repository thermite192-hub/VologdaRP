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
TOKEN = "9225027536:AAFe8GO3JGxINWax6R54lVb8HziDgLXW3e0"
ADMIN_ID = 6208939931          # ← ОБЯЗАТЕЛЬНО ЗАМЕНИ НА СВОЙ ID
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

BUSINESSES = {
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

# ====================== КРИПТОВАЛЮТА ======================

# Видеокарты: hashrate в единицах/час, цены в ₽
GPUS = {
    "rx580":      {"name": "RX 580 8GB",       "hashrate": 28,  "price_dns": 18_000,  "avito_min": 9_000,  "avito_max": 16_000},
    "gtx1660":    {"name": "GTX 1660 Super",   "hashrate": 32,  "price_dns": 25_000,  "avito_min": 14_000, "avito_max": 22_000},
    "rtx3060":    {"name": "RTX 3060",         "hashrate": 48,  "price_dns": 42_000,  "avito_min": 25_000, "avito_max": 38_000},
    "rtx3070":    {"name": "RTX 3070",         "hashrate": 62,  "price_dns": 65_000,  "avito_min": 38_000, "avito_max": 58_000},
    "rtx3080":    {"name": "RTX 3080",         "hashrate": 95,  "price_dns": 95_000,  "avito_min": 55_000, "avito_max": 85_000},
    "rtx3090":    {"name": "RTX 3090",         "hashrate": 120, "price_dns": 140_000, "avito_min": 80_000, "avito_max": 125_000},
    "rtx4070":    {"name": "RTX 4070",         "hashrate": 110, "price_dns": 110_000, "avito_min": 70_000, "avito_max": 100_000},
    "rtx4080":    {"name": "RTX 4080",         "hashrate": 145, "price_dns": 180_000, "avito_min": 110_000,"avito_max": 165_000},
    "rtx4090":    {"name": "RTX 4090",         "hashrate": 210, "price_dns": 280_000, "avito_min": 170_000,"avito_max": 250_000},
}

# Рамы для майнинг-фермы (слоты под видеокарты)
MINER_FRAMES = {
    "frame_6":   {"name": "Рама на 6 карт",   "slots": 6,  "price_dns": 12_000,  "avito_min": 6_000,  "avito_max": 11_000},
    "frame_8":   {"name": "Рама на 8 карт",   "slots": 8,  "price_dns": 18_000,  "avito_min": 10_000, "avito_max": 16_000},
    "frame_12":  {"name": "Рама на 12 карт",  "slots": 12, "price_dns": 28_000,  "avito_min": 15_000, "avito_max": 25_000},
    "frame_24":  {"name": "Рама на 24 карты", "slots": 24, "price_dns": 55_000,  "avito_min": 30_000, "avito_max": 48_000},
}

BASEMENT_PRICE = 350_000          # цена улучшения «подвал»
CRYPTO_RATE = 18                  # сколько ₽ даёт 1 единица крипты при продаже
CRYPTO_PER_HASH_HOUR = 0.45       # сколько крипты даёт 1 hashrate за 1 час

# ====================== КЛАВИАТУРА ======================

def main_keyboard():
    keyboard = [
        [KeyboardButton("💼 Работать"), KeyboardButton("📊 Профиль")],
        [KeyboardButton("🏪 Бизнесы"), KeyboardButton("🚗 Машины")],
        [KeyboardButton("🏠 Дома"), KeyboardButton("🚤 Яхты")],
        [KeyboardButton("✈️ Самолёты"), KeyboardButton("🌍 Город")],
        [KeyboardButton("💰 Доход"), KeyboardButton("🎁 Бонус")],
        [KeyboardButton("₿ Крипта"), KeyboardButton("🏆 Топ")],
        [KeyboardButton("📜 Статусы")],
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
            "pending_job": None,
            # === КРИПТА ===
            "crypto": 0.0,
            "basement": False,                    # есть ли подвал
            "gpus": [],                           # список {"gpu_id": str, "quality": "good"/"bad"/"dead", "hashrate": int}
            "frames": [],                         # список {"frame_id": str, "quality": ..., "slots": int, "installed": [индексы gpu]}
            "active_frame": None,                 # индекс активной рамы или None
            "last_crypto": time.time(),
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
        # крипта
        u.setdefault("crypto", 0.0)
        u.setdefault("basement", False)
        u.setdefault("gpus", [])
        u.setdefault("frames", [])
        u.setdefault("active_frame", None)
        u.setdefault("last_crypto", time.time())
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
    available = item.get("available_in")
    if not available:
        return True
    return location in available

def has_any_house(user):
    return any(v > 0 for v in user["houses"].values())

def get_total_hashrate(user):
    """Считает текущий hashrate активной рамы"""
    if user["active_frame"] is None:
        return 0
    frames = user.get("frames", [])
    if user["active_frame"] >= len(frames):
        return 0
    frame = frames[user["active_frame"]]
    total = 0
    for gpu_idx in frame.get("installed", []):
        if 0 <= gpu_idx < len(user["gpus"]):
            gpu = user["gpus"][gpu_idx]
            if gpu["quality"] != "dead":
                total += gpu["hashrate"]
    return total

def calculate_crypto_income(user):
    """Сколько крипты накопилось с last_crypto"""
    hashrate = get_total_hashrate(user)
    if hashrate <= 0:
        return 0.0
    now = time.time()
    hours = (now - user.get("last_crypto", now)) / 3600
    if hours < 0:
        hours = 0
    # максимум 24 часа за раз, чтобы не абузили
    hours = min(hours, 24)
    return round(hashrate * hours * CRYPTO_PER_HASH_HOUR, 2)

# ====================== ИГРОВЫЕ КОМАНДЫ ======================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id, update.effective_user.username, update.effective_user.full_name)
    if not user["registered"]:
        user["registered"] = True
        save_users()
        text = (
            f"Добро пожаловать, *{user['full_name']}*!\n"
            f"Ты начинаешь в *Вологде* с нуля.\n"
            f"Переезжай в другие города, открывай бизнесы, дома и транспорт.\n"
            f"Также доступен майнинг криптовалюты ₿!\n"
            f"Стань самым богатым!"
        )
        if is_admin(update.effective_user.id):
            text += "\n\n👑 Ты Создатель."
    else:
        loc = LOCATIONS[user["location"]]
        text = (
            f"С возвращением!\n"
            f"Статус: *{get_status(user)}*\n"
            f"Город: *{loc['name']}*\n"
            f"Деньги: *{user['money']:,} ₽*\n"
            f"Крипта: *{user.get('crypto', 0):.2f} ₿*"
        )
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=main_keyboard())

async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    if not user["registered"]:
        return await update.message.reply_text("Нажми /start")

    loc = LOCATIONS[user["location"]]
    passive = calculate_passive_income(user)
    hashrate = get_total_hashrate(user)
    pending_crypto = calculate_crypto_income(user)

    def fmt(items, data):
        lines = [f"• {data[k]['name']}: {v}" for k, v in items.items() if v > 0]
        return "\n".join(lines) if lines else "нет"

    basement = "✅ есть" if user.get("basement") else "❌ нет"
    text = (
        f"*Профиль*\n\n"
        f"Имя: {user['full_name']}\n"
        f"Статус: *{get_status(user)}*" + (" 👑" if user.get("is_admin") else "") + "\n"
        f"Уровень: *{user['level']}*\n"
        f"Город: *{loc['name']}* ({loc['country']}) ×{loc['multiplier']}\n"
        f"Деньги: *{user['money']:,} ₽*\n"
        f"Крипта: *{user.get('crypto', 0):.2f} ₿* (+{pending_crypto:.2f} ждёт сбора)\n"
        f"Хешрейт: *{hashrate}* H/ч\n"
        f"Подвал: {basement}\n"
        f"Пассив (бизнес): *{passive:,} ₽/час*\n"
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

    if now - last < 20 * 3600:
        left = int((20 * 3600 - (now - last)) / 3600)
        return await update.message.reply_text(f"Бонус ещё недоступен.\nОсталось примерно {left} ч.")

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
    text = "*🏆 Топ-10 игроков (по деньгам):*\n\n"
    for i, u in enumerate(sorted_users, 1):
        medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, f"{i}.")
        name = u.get("full_name", "Игрок")
        text += f"{medal} {name} — *{u['money']:,} ₽*\n"
    await update.message.reply_text(text, parse_mode="Markdown")

# ---------- МАГАЗИНЫ ----------

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
        f"Бизнесы в *{LOCATIONS[loc]['name']}*:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def cars_shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    loc = user["location"]
    available = [(k, v) for k, v in CARS.items() if item_available(v, loc)]
    if not available:
        return await update.message.reply_text("В этом городе нет машин. Переезжай!")
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
    # кнопка улучшения подвала
    if has_any_house(user) and not user.get("basement"):
        keyboard.append([InlineKeyboardButton(f"🔧 Улучшение «Подвал» — {BASEMENT_PRICE:,} ₽", callback_data="buy_basement")])
    elif user.get("basement"):
        keyboard.append([InlineKeyboardButton("✅ Подвал уже есть", callback_data="noop")])
    await update.message.reply_text(
        f"Дома в *{LOCATIONS[loc]['name']}*:\n(для майнинга нужен подвал)",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def yachts_shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    loc = user["location"]
    available = [(k, v) for k, v in YACHTS.items() if item_available(v, loc)]
    if not available:
        return await update.message.reply_text("Яхты доступны только в портовых и богатых городах.")
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
        return await update.message.reply_text("Самолёты доступны в крупных городах.")
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
        f"Переезд открывает новые бизнесы, дома и транспорт.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# ====================== КРИПТА МЕНЮ ======================

async def crypto_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    if not user["registered"]:
        return await update.message.reply_text("Сначала /start")

    hashrate = get_total_hashrate(user)
    pending = calculate_crypto_income(user)
    basement = "✅" if user.get("basement") else "❌"

    text = (
        f"*₿ Криптовалюта*\n\n"
        f"Баланс: *{user.get('crypto', 0):.2f} ₿*\n"
        f"Ожидает сбора: *{pending:.2f} ₿*\n"
        f"Текущий хешрейт: *{hashrate}* H/ч\n"
        f"Подвал: {basement}\n"
        f"Видеокарт: {len(user.get('gpus', []))}\n"
        f"Рам: {len(user.get('frames', []))}\n\n"
        f"1 ₿ ≈ {CRYPTO_RATE} ₽"
    )

    keyboard = [
        [InlineKeyboardButton("⛏ Собрать крипту", callback_data="crypto_collect")],
        [InlineKeyboardButton("🛒 DNS (официал)", callback_data="crypto_dns"),
         InlineKeyboardButton("📦 Авито (б/у)", callback_data="crypto_avito")],
        [InlineKeyboardButton("🖥 Мои видеокарты", callback_data="crypto_my_gpus")],
        [InlineKeyboardButton("🔧 Мои рамы / Установка", callback_data="crypto_frames")],
        [InlineKeyboardButton("💸 Продать крипту", callback_data="crypto_sell")],
        [InlineKeyboardButton("🏠 Купить подвал", callback_data="buy_basement")],
    ]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

def generate_minigame():
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

    # === Работа + мини-игра ===
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

        question, correct, options = generate_minigame()
        user["pending_job"] = {
            "job_id": job_id,
            "correct": correct,
            "started": now,
        }
        save_users()

        keyboard = [[InlineKeyboardButton(str(opt), callback_data=f"mg_{opt}")] for opt in options]
        await query.edit_message_text(
            f"Работа: *{job['name']}*\n\n"
            f"🧠 *Мини-игра*\n"
            f"Реши пример, чтобы получить полную зарплату:\n\n"
            f"*{question}*",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return

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
        if now - pending.get("started", 0) > 120:
            user["pending_job"] = None
            save_users()
            return await query.edit_message_text("Время на ответ истекло.")

        loc_mult = LOCATIONS[user["location"]]["multiplier"]
        base_pay = random.randint(job["pay_min"], job["pay_max"])
        pay = int(base_pay * loc_mult)

        user["last_work"] = now
        user["pending_job"] = None
        success = answer == pending["correct"]

        if success:
            user["money"] += pay
            level_up = ""
            if user["level"] < 100 and random.random() < 0.18:
                user["level"] += 1
                level_up = f"\n\n🎉 Уровень → *{user['level']}*!"
            save_users()
            await query.edit_message_text(
                f"✅ Верно! ({pending['correct']})\n\n"
                f"Работа: *{job['name']}*\n"
                f"Заработано: *{pay:,} ₽*\n"
                f"Баланс: *{user['money']:,} ₽*{level_up}",
                parse_mode="Markdown"
            )
        else:
            reduced = int(pay * random.uniform(0.25, 0.40))
            user["money"] += reduced
            save_users()
            await query.edit_message_text(
                f"❌ Неверно! Правильный ответ: *{pending['correct']}*\n\n"
                f"Работа: *{job['name']}*\n"
                f"Получено только: *{reduced:,} ₽*\n"
                f"Баланс: *{user['money']:,} ₽*",
                parse_mode="Markdown"
            )
        return

    # === Покупки обычных предметов ===
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
            if not item_available(item, user["location"]):
                return await query.edit_message_text("Этот предмет недоступен в твоём городе.")
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

    # === Подвал ===
    if data == "buy_basement":
        if user.get("basement"):
            return await query.edit_message_text("Подвал уже есть!")
        if not has_any_house(user):
            return await query.edit_message_text("Сначала купи хотя бы один дом.")
        if user["money"] < BASEMENT_PRICE:
            return await query.edit_message_text(f"Не хватает ({BASEMENT_PRICE:,} ₽)")
        user["money"] -= BASEMENT_PRICE
        user["basement"] = True
        save_users()
        await query.edit_message_text(
            f"✅ Подвал построен!\nТеперь можно устанавливать майнинг-рамы.\nОстаток: *{user['money']:,} ₽*",
            parse_mode="Markdown"
        )
        return

    if data == "noop":
        return await query.answer("Уже куплено", show_alert=False)

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
            f"Множитель: ×{loc['multiplier']}\n"
            f"Остаток: *{user['money']:,} ₽*",
            parse_mode="Markdown"
        )
        return

    # ==================== КРИПТА ====================

    # Сбор крипты
    if data == "crypto_collect":
        pending = calculate_crypto_income(user)
        if pending <= 0:
            return await query.edit_message_text("Нечего собирать. Установи видеокарты в раму и подожди.")
        user["crypto"] = round(user.get("crypto", 0) + pending, 2)
        user["last_crypto"] = time.time()
        save_users()
        await query.edit_message_text(
            f"⛏ Собрано: *{pending:.2f} ₿*\n"
            f"Всего крипты: *{user['crypto']:.2f} ₿*",
            parse_mode="Markdown"
        )
        return

    # Продать крипту
    if data == "crypto_sell":
        amount = user.get("crypto", 0)
        if amount < 1:
            return await query.edit_message_text("Мало крипты для продажи (минимум 1 ₿).")
        # продаём всё
        money = int(amount * CRYPTO_RATE)
        user["money"] += money
        user["crypto"] = 0.0
        save_users()
        await query.edit_message_text(
            f"💸 Продано *{amount:.2f} ₿* за *{money:,} ₽*\n"
            f"Баланс: *{user['money']:,} ₽*",
            parse_mode="Markdown"
        )
        return

    # DNS магазин
    if data == "crypto_dns":
        keyboard = []
        keyboard.append([InlineKeyboardButton("——— Видеокарты ———", callback_data="noop")])
        for gid, g in GPUS.items():
            keyboard.append([InlineKeyboardButton(
                f"{g['name']} — {g['price_dns']:,} ₽ ({g['hashrate']} H)",
                callback_data=f"buygpu_dns_{gid}"
            )])
        keyboard.append([InlineKeyboardButton("——— Рамы ———", callback_data="noop")])
        for fid, f in MINER_FRAMES.items():
            keyboard.append([InlineKeyboardButton(
                f"{f['name']} — {f['price_dns']:,} ₽ ({f['slots']} слотов)",
                callback_data=f"buyframe_dns_{fid}"
            )])
        keyboard.append([InlineKeyboardButton("« Назад", callback_data="crypto_back")])
        await query.edit_message_text(
            "*🛒 DNS — официальный магазин*\nВсё новое, качество отличное.\nЦены выше, но без сюрпризов.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return

    # Авито
    if data == "crypto_avito":
        keyboard = []
        keyboard.append([InlineKeyboardButton("——— Видеокарты (б/у) ———", callback_data="noop")])
        for gid, g in GPUS.items():
            keyboard.append([InlineKeyboardButton(
                f"{g['name']} — {g['avito_min']:,}–{g['avito_max']:,} ₽",
                callback_data=f"buygpu_avito_{gid}"
            )])
        keyboard.append([InlineKeyboardButton("——— Рамы (б/у) ———", callback_data="noop")])
        for fid, f in MINER_FRAMES.items():
            keyboard.append([InlineKeyboardButton(
                f"{f['name']} — {f['avito_min']:,}–{f['avito_max']:,} ₽",
                callback_data=f"buyframe_avito_{fid}"
            )])
        keyboard.append([InlineKeyboardButton("« Назад", callback_data="crypto_back")])
        await query.edit_message_text(
            "*📦 Авито — б/у рынок*\nЦены ниже, но:\n"
            "• 65% — нормальная карта\n"
            "• 25% — плохая (хешрейт −50%)\n"
            "• 10% — сразу мёртвая\n"
            "Покупаешь на свой страх и риск!",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return

    if data == "crypto_back":
        # просто возвращаем в меню крипты (через новое сообщение нельзя, поэтому текст)
        hashrate = get_total_hashrate(user)
        pending = calculate_crypto_income(user)
        basement = "✅" if user.get("basement") else "❌"
        text = (
            f"*₿ Криптовалюта*\n\n"
            f"Баланс: *{user.get('crypto', 0):.2f} ₿*\n"
            f"Ожидает сбора: *{pending:.2f} ₿*\n"
            f"Хешрейт: *{hashrate}* H/ч\n"
            f"Подвал: {basement}\n"
            f"Видеокарт: {len(user.get('gpus', []))}\n"
            f"Рам: {len(user.get('frames', []))}"
        )
        keyboard = [
            [InlineKeyboardButton("⛏ Собрать крипту", callback_data="crypto_collect")],
            [InlineKeyboardButton("🛒 DNS", callback_data="crypto_dns"),
             InlineKeyboardButton("📦 Авито", callback_data="crypto_avito")],
            [InlineKeyboardButton("🖥 Мои видеокарты", callback_data="crypto_my_gpus")],
            [InlineKeyboardButton("🔧 Мои рамы", callback_data="crypto_frames")],
            [InlineKeyboardButton("💸 Продать крипту", callback_data="crypto_sell")],
            [InlineKeyboardButton("🏠 Купить подвал", callback_data="buy_basement")],
        ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        return

    # Покупка видеокарты DNS
    if data.startswith("buygpu_dns_"):
        gid = data[11:]
        if gid not in GPUS:
            return
        g = GPUS[gid]
        price = g["price_dns"]
        if user["money"] < price:
            return await query.edit_message_text(f"Не хватает ({price:,} ₽)")
        user["money"] -= price
        user["gpus"].append({
            "gpu_id": gid,
            "quality": "good",
            "hashrate": g["hashrate"],
            "source": "dns"
        })
        save_users()
        await query.edit_message_text(
            f"✅ Куплено в DNS: *{g['name']}*\n"
            f"Качество: отличное\n"
            f"Хешрейт: {g['hashrate']} H\n"
            f"Остаток: *{user['money']:,} ₽*",
            parse_mode="Markdown"
        )
        return

    # Покупка видеокарты Авито
    if data.startswith("buygpu_avito_"):
        gid = data[13:]
        if gid not in GPUS:
            return
        g = GPUS[gid]
        price = random.randint(g["avito_min"], g["avito_max"])
        if user["money"] < price:
            return await query.edit_message_text(f"Не хватает (~{price:,} ₽)")
        user["money"] -= price

        roll = random.random()
        if roll < 0.10:          # 10% мёртвая
            quality = "dead"
            hr = 0
            qtext = "💀 МЁРТВАЯ (сразу не работает)"
        elif roll < 0.35:        # 25% плохая
            quality = "bad"
            hr = max(1, g["hashrate"] // 2)
            qtext = f"⚠️ Плохая (хешрейт {hr} вместо {g['hashrate']})"
        else:                    # 65% нормальная
            quality = "good"
            hr = g["hashrate"]
            qtext = f"✅ Нормальная ({hr} H)"

        user["gpus"].append({
            "gpu_id": gid,
            "quality": quality,
            "hashrate": hr,
            "source": "avito"
        })
        save_users()
        await query.edit_message_text(
            f"📦 Куплено на Авито: *{g['name']}*\n"
            f"Цена: {price:,} ₽\n"
            f"{qtext}\n"
            f"Остаток: *{user['money']:,} ₽*",
            parse_mode="Markdown"
        )
        return

    # Покупка рамы DNS
    if data.startswith("buyframe_dns_"):
        fid = data[13:]
        if fid not in MINER_FRAMES:
            return
        f = MINER_FRAMES[fid]
        price = f["price_dns"]
        if user["money"] < price:
            return await query.edit_message_text(f"Не хватает ({price:,} ₽)")
        if not user.get("basement"):
            return await query.edit_message_text("Сначала нужен подвал! Купи дом и улучшение «Подвал».")
        user["money"] -= price
        user["frames"].append({
            "frame_id": fid,
            "quality": "good",
            "slots": f["slots"],
            "installed": [],
            "source": "dns"
        })
        # если активной рамы нет — делаем эту активной
        if user["active_frame"] is None:
            user["active_frame"] = len(user["frames"]) - 1
        save_users()
        await query.edit_message_text(
            f"✅ Куплена рама: *{f['name']}*\n"
            f"Слотов: {f['slots']}\n"
            f"Остаток: *{user['money']:,} ₽*",
            parse_mode="Markdown"
        )
        return

    # Покупка рамы Авито
    if data.startswith("buyframe_avito_"):
        fid = data[15:]
        if fid not in MINER_FRAMES:
            return
        f = MINER_FRAMES[fid]
        price = random.randint(f["avito_min"], f["avito_max"])
        if user["money"] < price:
            return await query.edit_message_text(f"Не хватает (~{price:,} ₽)")
        if not user.get("basement"):
            return await query.edit_message_text("Сначала нужен подвал!")
        user["money"] -= price

        roll = random.random()
        if roll < 0.08:
            quality = "dead"
            slots = 0
            qtext = "💀 Рама сломана, слотов 0"
        elif roll < 0.30:
            quality = "bad"
            slots = max(1, f["slots"] - random.randint(1, 3))
            qtext = f"⚠️ Повреждённая (слотов {slots} вместо {f['slots']})"
        else:
            quality = "good"
            slots = f["slots"]
            qtext = f"✅ Нормальная ({slots} слотов)"

        user["frames"].append({
            "frame_id": fid,
            "quality": quality,
            "slots": slots,
            "installed": [],
            "source": "avito"
        })
        if user["active_frame"] is None and quality != "dead":
            user["active_frame"] = len(user["frames"]) - 1
        save_users()
        await query.edit_message_text(
            f"📦 Куплена рама на Авито: *{f['name']}*\n"
            f"Цена: {price:,} ₽\n"
            f"{qtext}\n"
            f"Остаток: *{user['money']:,} ₽*",
            parse_mode="Markdown"
        )
        return

    # Мои видеокарты
    if data == "crypto_my_gpus":
        gpus = user.get("gpus", [])
        if not gpus:
            return await query.edit_message_text("У тебя пока нет видеокарт.\nКупи в DNS или на Авито.")
        text = "*🖥 Твои видеокарты:*\n\n"
        keyboard = []
        for i, gpu in enumerate(gpus):
            gname = GPUS.get(gpu["gpu_id"], {}).get("name", gpu["gpu_id"])
            q = {"good": "✅", "bad": "⚠️", "dead": "💀"}.get(gpu["quality"], "?")
            text += f"{i+1}. {q} {gname} — {gpu['hashrate']} H ({gpu.get('source', '?')})\n"
            # кнопка продать
            sell_price = int(GPUS.get(gpu["gpu_id"], {}).get("price_dns", 10000) * 0.35)
            if gpu["quality"] == "dead":
                sell_price = 500
            elif gpu["quality"] == "bad":
                sell_price = int(sell_price * 0.5)
            keyboard.append([InlineKeyboardButton(
                f"Продать #{i+1} за ~{sell_price:,} ₽",
                callback_data=f"sellgpu_{i}"
            )])
        keyboard.append([InlineKeyboardButton("« Назад", callback_data="crypto_back")])
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        return

    # Продажа видеокарты
    if data.startswith("sellgpu_"):
        try:
            idx = int(data[8:])
        except:
            return
        gpus = user.get("gpus", [])
        if not (0 <= idx < len(gpus)):
            return await query.edit_message_text("Карта не найдена.")
        gpu = gpus[idx]
        base = GPUS.get(gpu["gpu_id"], {}).get("price_dns", 10000)
        if gpu["quality"] == "dead":
            price = 500
        elif gpu["quality"] == "bad":
            price = int(base * 0.18)
        else:
            price = int(base * 0.35)

        # убираем из установленных рам
        for frame in user.get("frames", []):
            if idx in frame.get("installed", []):
                frame["installed"] = [x for x in frame["installed"] if x != idx]
            # сдвигаем индексы выше
            frame["installed"] = [x - 1 if x > idx else x for x in frame["installed"]]

        user["gpus"].pop(idx)
        user["money"] += price
        save_users()
        await query.edit_message_text(
            f"Продано за *{price:,} ₽*\nОстаток: *{user['money']:,} ₽*",
            parse_mode="Markdown"
        )
        return

    # Мои рамы + установка
    if data == "crypto_frames":
        frames = user.get("frames", [])
        if not frames:
            return await query.edit_message_text("У тебя нет рам.\nКупи в DNS или на Авито (нужен подвал).")
        text = "*🔧 Твои рамы:*\n\n"
        keyboard = []
        for i, fr in enumerate(frames):
            fname = MINER_FRAMES.get(fr["frame_id"], {}).get("name", fr["frame_id"])
            active = " ⭐" if user.get("active_frame") == i else ""
            installed = len(fr.get("installed", []))
            text += (
                f"{i+1}. {fname}{active}\n"
                f"   Слотов: {installed}/{fr['slots']} | Качество: {fr['quality']}\n"
            )
            keyboard.append([
                InlineKeyboardButton(f"Установить карты в раму #{i+1}", callback_data=f"install_{i}"),
                InlineKeyboardButton(f"Сделать активной #{i+1}", callback_data=f"setactive_{i}")
            ])
            # продать раму
            sell_p = int(MINER_FRAMES.get(fr["frame_id"], {}).get("price_dns", 10000) * 0.3)
            if fr["quality"] != "good":
                sell_p = int(sell_p * 0.4)
            keyboard.append([InlineKeyboardButton(f"Продать раму #{i+1} (~{sell_p:,} ₽)", callback_data=f"sellframe_{i}")])
        keyboard.append([InlineKeyboardButton("« Назад", callback_data="crypto_back")])
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        return

    if data.startswith("setactive_"):
        try:
            idx = int(data[10:])
        except:
            return
        if 0 <= idx < len(user.get("frames", [])):
            user["active_frame"] = idx
            save_users()
            await query.edit_message_text(f"Рама #{idx+1} теперь активная. Хешрейт обновлён.")
        return

    if data.startswith("sellframe_"):
        try:
            idx = int(data[10:])
        except:
            return
        frames = user.get("frames", [])
        if not (0 <= idx < len(frames)):
            return
        fr = frames[idx]
        base = MINER_FRAMES.get(fr["frame_id"], {}).get("price_dns", 10000)
        price = int(base * 0.3)
        if fr["quality"] != "good":
            price = int(price * 0.4)
        # освобождаем карты (они остаются у игрока)
        user["frames"].pop(idx)
        if user.get("active_frame") == idx:
            user["active_frame"] = 0 if user["frames"] else None
        elif user.get("active_frame") is not None and user["active_frame"] > idx:
            user["active_frame"] -= 1
        user["money"] += price
        save_users()
        await query.edit_message_text(f"Рама продана за *{price:,} ₽*", parse_mode="Markdown")
        return

    # Установка карт в раму
    if data.startswith("install_"):
        try:
            fidx = int(data[8:])
        except:
            return
        frames = user.get("frames", [])
        if not (0 <= fidx < len(frames)):
            return
        frame = frames[fidx]
        if frame["quality"] == "dead" or frame["slots"] <= 0:
            return await query.edit_message_text("Эта рама нерабочая.")

        # свободные (не установленные ни в какую раму) карты
        used = set()
        for fr in frames:
            used.update(fr.get("installed", []))
        free_gpus = [i for i in range(len(user["gpus"])) if i not in used and user["gpus"][i]["quality"] != "dead"]

        if not free_gpus:
            return await query.edit_message_text("Нет свободных рабочих видеокарт.")

        free_slots = frame["slots"] - len(frame.get("installed", []))
        if free_slots <= 0:
            return await query.edit_message_text("В раме нет свободных слотов.")

        # ставим столько, сколько можно
        to_install = free_gpus[:free_slots]
        frame.setdefault("installed", []).extend(to_install)
        save_users()
        await query.edit_message_text(
            f"✅ Установлено {len(to_install)} видеокарт в раму #{fidx+1}.\n"
            f"Теперь слотов занято: {len(frame['installed'])}/{frame['slots']}\n"
            f"Хешрейт рамы: {get_total_hashrate(user)} H/ч"
        )
        return

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
        "₿ Крипта": crypto_menu,
    }
    handler = mapping.get(text)
    if handler:
        await handler(update, context)

# ====================== АДМИН ======================

async def admin_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return await update.message.reply_text("Нет доступа.")
    await update.message.reply_text(
        "*Админ-команды:*\n/setmoney /addmoney /setlevel\n/give <id> <сумма>\n/resetme /users\n/setcrypto <кол-во>",
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

async def set_crypto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    if not context.args: return await update.message.reply_text("Пример: /setcrypto 100")
    try:
        user = get_user(update.effective_user.id)
        user["crypto"] = float(context.args[0])
        save_users()
        await update.message.reply_text(f"Крипта: *{user['crypto']:.2f} ₿*", parse_mode="Markdown")
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
        "crypto": 0.0,
        "basement": False,
        "gpus": [],
        "frames": [],
        "active_frame": None,
        "last_crypto": time.time(),
    })
    save_users()
    await update.message.reply_text("Прогресс полностью сброшен. Ты снова в Вологде.")

async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    text = "*Игроки:*\n\n"
    for uid, u in users.items():
        mark = " 👑" if u.get("is_admin") else ""
        text += f"`{uid}` {u.get('full_name')}{mark} — {u['money']:,} ₽ | {u.get('crypto', 0):.1f}₿\n"
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
    app.add_handler(CommandHandler("crypto", crypto_menu))

    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, button_handler))

    app.add_handler(CommandHandler("admin", admin_help))
    app.add_handler(CommandHandler("setmoney", set_money))
    app.add_handler(CommandHandler("addmoney", add_money))
    app.add_handler(CommandHandler("setlevel", set_level))
    app.add_handler(CommandHandler("give", give_money))
    app.add_handler(CommandHandler("setcrypto", set_crypto))
    app.add_handler(CommandHandler("resetme", reset_me))
    app.add_handler(CommandHandler("users", list_users))

    print("Бот полностью запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()
