import logging
import time
import json
import os
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)

# ====================== НАСТРОЙКИ ======================
TOKEN = "СЮДА_ВСТАВЬ_ТОКЕН_ОТ_BOTFATHER"
ADMIN_ID = 123456789
SAVE_FILE = "users.json"

# ====================== ДАННЫЕ ======================

JOBS = {
    "loader":        {"name": "Грузчик",            "min_level": 1,  "pay_min": 180,   "pay_max": 320,   "cooldown": 10, "xp": 8,  "fatigue": 12},
    "cashier":       {"name": "Кассир",             "min_level": 2,  "pay_min": 280,   "pay_max": 480,   "cooldown": 11, "xp": 10, "fatigue": 10},
    "courier":       {"name": "Курьер",             "min_level": 3,  "pay_min": 350,   "pay_max": 620,   "cooldown": 11, "xp": 12, "fatigue": 15},
    "driver":        {"name": "Водитель",           "min_level": 4,  "pay_min": 450,   "pay_max": 780,   "cooldown": 12, "xp": 14, "fatigue": 14},
    "seller":        {"name": "Продавец",           "min_level": 5,  "pay_min": 550,   "pay_max": 950,   "cooldown": 12, "xp": 15, "fatigue": 11},
    "manager":       {"name": "Менеджер",           "min_level": 7,  "pay_min": 800,   "pay_max": 1400,  "cooldown": 13, "xp": 20, "fatigue": 9},
    "engineer":      {"name": "Инженер",            "min_level": 9,  "pay_min": 1100,  "pay_max": 2000,  "cooldown": 14, "xp": 25, "fatigue": 13},
    "programmer":    {"name": "Программист",        "min_level": 10, "pay_min": 1400,  "pay_max": 2800,  "cooldown": 14, "xp": 28, "fatigue": 12},
    "director":      {"name": "Директор",           "min_level": 15, "pay_min": 2800,  "pay_max": 5500,  "cooldown": 16, "xp": 40, "fatigue": 10},
    "oligarch_work": {"name": "Совет директоров",   "min_level": 25, "pay_min": 9000,  "pay_max": 20000, "cooldown": 20, "xp": 70, "fatigue": 8},
}

BUSINESSES = {
    "kiosk":       {"name": "Киоск",               "price": 5_000,       "income": 110,    "available_in": ["vologda", "kazan", "ekb", "ufa"]},
    "shop":        {"name": "Магазин",             "price": 28_000,      "income": 420,    "available_in": ["vologda", "kazan", "ekb", "ufa", "spb"]},
    "cafe":        {"name": "Кафе",                "price": 95_000,      "income": 1_550,  "available_in": ["vologda", "kazan", "ekb", "spb", "moscow"]},
    "auto_service":{"name": "Автосервис",          "price": 190_000,     "income": 3_100,  "available_in": ["vologda", "ekb", "kazan", "spb"]},
    "restaurant":  {"name": "Ресторан",            "price": 300_000,     "income": 5_000,  "available_in": ["kazan", "ekb", "spb", "moscow", "istanbul"]},
    "car_wash":    {"name": "Автомойка",           "price": 480_000,     "income": 7_800,  "available_in": ["ekb", "spb", "moscow", "istanbul", "berlin"]},
    "hotel":       {"name": "Гостиница",           "price": 1_300_000,   "income": 19_500, "available_in": ["spb", "moscow", "istanbul", "dubai", "berlin"]},
    "factory":     {"name": "Завод",               "price": 3_800_000,   "income": 48_000, "available_in": ["ekb", "moscow", "berlin", "london"]},
    "it_company":  {"name": "IT-компания",         "price": 8_500_000,   "income": 105_000,"available_in": ["moscow", "berlin", "london", "newyork"]},
    "bank":        {"name": "Банк",                "price": 27_000_000,  "income": 300_000,"available_in": ["moscow", "london", "newyork", "monaco"]},
    "holding":     {"name": "Холдинг",             "price": 85_000_000,  "income": 900_000,"available_in": ["london", "newyork", "monaco", "dubai"]},
    "oil_company": {"name": "Нефтяная компания",   "price": 320_000_000, "income": 3_000_000,"available_in": ["moscow", "dubai", "london"]},
    "tech_park":   {"name": "Технопарк",           "price": 48_000_000,  "income": 550_000,"available_in": ["moscow", "berlin", "newyork"]},
    "casino":      {"name": "Казино",              "price": 130_000_000, "income": 1_500_000,"available_in": ["monaco", "dubai", "macau"]},
    "space_port":  {"name": "Космодром",           "price": 950_000_000, "income": 10_000_000,"available_in": ["dubai", "newyork", "monaco"]},
}

CARS = {
    "oka":          {"name": "Ока",                    "price": 120_000,   "fuel_cap": 30,  "consumption": 6.5,  "speed": 1.0, "available_in": ["vologda", "ufa", "kazan", "ekb"]},
    "niva":         {"name": "Лада Нива",               "price": 950_000,   "fuel_cap": 42,  "consumption": 10.5, "speed": 1.1, "available_in": ["vologda", "ufa", "kazan", "ekb", "spb"]},
    "granta":       {"name": "Лада Гранта",             "price": 850_000,   "fuel_cap": 50,  "consumption": 7.2,  "speed": 1.15,"available_in": ["vologda", "ufa", "kazan", "ekb", "spb", "moscow"]},
    "vesta":        {"name": "Лада Веста",              "price": 1_450_000, "fuel_cap": 55,  "consumption": 7.5,  "speed": 1.25,"available_in": ["kazan", "ekb", "spb", "moscow"]},
    "largus":       {"name": "Лада Ларгус",             "price": 1_600_000, "fuel_cap": 50,  "consumption": 8.5,  "speed": 1.1, "available_in": ["vologda", "ekb", "kazan", "spb"]},
    "uaz_patriot":  {"name": "УАЗ Патриот",             "price": 1_800_000, "fuel_cap": 68,  "consumption": 13.5, "speed": 1.05,"available_in": ["vologda", "ufa", "ekb", "kazan"]},
    "uaz_buhanka":  {"name": "УАЗ Буханка",             "price": 1_100_000, "fuel_cap": 56,  "consumption": 14.0, "speed": 0.9, "available_in": ["vologda", "ufa", "ekb"]},
    "gazelle":      {"name": "ГАЗель Next",             "price": 2_400_000, "fuel_cap": 70,  "consumption": 12.0, "speed": 1.0, "available_in": ["ekb", "kazan", "spb", "moscow"]},
    "sobol":        {"name": "ГАЗ Соболь",              "price": 2_100_000, "fuel_cap": 65,  "consumption": 11.5, "speed": 1.0, "available_in": ["ekb", "spb", "moscow"]},
    "volga":        {"name": "Волга (ГАЗ-31105)",       "price": 450_000,   "fuel_cap": 55,  "consumption": 11.0, "speed": 1.05,"available_in": ["vologda", "ufa", "kazan", "ekb"]},
    "moskvich":     {"name": "Москвич 3",               "price": 1_700_000, "fuel_cap": 50,  "consumption": 8.0,  "speed": 1.2, "available_in": ["moscow", "spb", "ekb"]},
    "aurus":        {"name": "Aurus Senat",             "price": 45_000_000,"fuel_cap": 80,  "consumption": 14.0, "speed": 1.6, "available_in": ["moscow", "spb"]},
    "solaris":      {"name": "Hyundai Solaris",         "price": 1_650_000, "fuel_cap": 50,  "consumption": 6.8,  "speed": 1.3, "available_in": ["vologda", "kazan", "ekb", "spb", "moscow"]},
    "rio":          {"name": "Kia Rio",                 "price": 1_700_000, "fuel_cap": 45,  "consumption": 6.5,  "speed": 1.3, "available_in": ["kazan", "ekb", "spb", "moscow"]},
    "camry":        {"name": "Toyota Camry",            "price": 3_900_000, "fuel_cap": 60,  "consumption": 8.5,  "speed": 1.45,"available_in": ["kazan", "ekb", "spb", "moscow", "istanbul"]},
    "rav4":         {"name": "Toyota RAV4",             "price": 4_200_000, "fuel_cap": 55,  "consumption": 8.0,  "speed": 1.4, "available_in": ["spb", "moscow", "berlin"]},
    "bmw3":         {"name": "BMW 3 Series",            "price": 5_500_000, "fuel_cap": 59,  "consumption": 7.5,  "speed": 1.7, "available_in": ["spb", "moscow", "berlin", "istanbul"]},
    "bmw5":         {"name": "BMW 5 Series",            "price": 7_800_000, "fuel_cap": 68,  "consumption": 8.5,  "speed": 1.8, "available_in": ["moscow", "berlin", "london", "dubai"]},
    "mercedes_e":   {"name": "Mercedes E-Class",        "price": 9_900_000, "fuel_cap": 66,  "consumption": 8.0,  "speed": 1.75,"available_in": ["moscow", "berlin", "london", "dubai"]},
    "mercedes_s":   {"name": "Mercedes S-Class",        "price": 16_000_000,"fuel_cap": 76,  "consumption": 10.0, "speed": 1.9, "available_in": ["moscow", "london", "dubai", "newyork", "monaco"]},
    "porsche":      {"name": "Porsche 911",             "price": 23_000_000,"fuel_cap": 64,  "consumption": 11.0, "speed": 2.2, "available_in": ["dubai", "london", "newyork", "monaco"]},
    "lambo":        {"name": "Lamborghini Huracan",     "price": 36_000_000,"fuel_cap": 80,  "consumption": 14.0, "speed": 2.5, "available_in": ["dubai", "monaco", "newyork"]},
    "ferrari":      {"name": "Ferrari 488",             "price": 44_000_000,"fuel_cap": 78,  "consumption": 15.0, "speed": 2.6, "available_in": ["monaco", "dubai", "newyork"]},
    "bugatti":      {"name": "Bugatti Chiron",          "price": 185_000_000,"fuel_cap": 100,"consumption": 25.0, "speed": 3.0, "available_in": ["monaco", "dubai"]},
    "rolls":        {"name": "Rolls-Royce Phantom",     "price": 58_000_000,"fuel_cap": 90,  "consumption": 16.0, "speed": 1.8, "available_in": ["london", "monaco", "dubai"]},
}

HOUSES = {
    "apartment": {"name": "Квартира-студия",         "price": 3_500_000,   "available_in": ["vologda", "ufa", "kazan", "ekb"]},
    "flat":      {"name": "Трёхкомнатная квартира",  "price": 9_500_000,   "available_in": ["vologda", "kazan", "ekb", "spb"]},
    "townhouse": {"name": "Таунхаус",                "price": 19_000_000,  "available_in": ["ekb", "spb", "moscow", "istanbul"]},
    "cottage":   {"name": "Коттедж",                 "price": 38_000_000,  "available_in": ["spb", "moscow", "berlin", "istanbul"]},
    "mansion":   {"name": "Особняк",                 "price": 95_000_000,  "available_in": ["moscow", "berlin", "london", "dubai"]},
    "villa":     {"name": "Вилла на море",           "price": 260_000_000, "available_in": ["dubai", "istanbul", "monaco"]},
    "penthouse": {"name": "Пентхаус",                "price": 190_000_000, "available_in": ["moscow", "london", "newyork", "dubai"]},
    "castle":    {"name": "Замок",                   "price": 850_000_000, "available_in": ["london", "monaco", "berlin"]},
    "island":    {"name": "Частный остров",          "price": 2_600_000_000,"available_in": ["monaco", "dubai"]},
}

YACHTS = {
    "small_yacht":   {"name": "Небольшая яхта",      "price": 48_000_000,  "available_in": ["spb", "istanbul", "dubai"]},
    "motor_yacht":   {"name": "Моторная яхта",       "price": 125_000_000, "available_in": ["istanbul", "dubai", "monaco"]},
    "luxury_yacht":  {"name": "Люксовая яхта",       "price": 360_000_000, "available_in": ["dubai", "monaco", "newyork"]},
    "mega_yacht":    {"name": "Мега-яхта",           "price": 950_000_000, "available_in": ["monaco", "dubai"]},
    "superyacht":    {"name": "Суперъяхта",          "price": 2_600_000_000,"available_in": ["monaco"]},
}

PLANES = {
    "cessna":        {"name": "Cessna",              "price": 85_000_000,  "available_in": ["moscow", "berlin", "dubai"]},
    "business_jet":  {"name": "Бизнес-джет",         "price": 290_000_000, "available_in": ["moscow", "london", "dubai", "newyork"]},
    "gulfstream":    {"name": "Gulfstream G650",     "price": 680_000_000, "available_in": ["london", "dubai", "newyork", "monaco"]},
    "private_boeing":{"name": "Частный Boeing",      "price": 1_900_000_000,"available_in": ["dubai", "newyork", "monaco"]},
    "airbus_acj":    {"name": "Airbus ACJ",          "price": 4_600_000_000,"available_in": ["monaco", "dubai"]},
    "helicopter":    {"name": "Вертолёт",            "price": 48_000_000,  "available_in": ["moscow", "spb", "dubai", "monaco"]},
}

LOCATIONS = {
    "vologda":  {"name": "Вологда",          "country": "Россия",         "price": 0,           "multiplier": 1.0,  "distance": 0},
    "ufa":      {"name": "Уфа",              "country": "Россия",         "price": 80_000,      "multiplier": 1.05, "distance": 1200},
    "kazan":    {"name": "Казань",           "country": "Россия",         "price": 150_000,     "multiplier": 1.1,  "distance": 900},
    "ekb":      {"name": "Екатеринбург",     "country": "Россия",         "price": 300_000,     "multiplier": 1.15, "distance": 1500},
    "spb":      {"name": "Санкт-Петербург",  "country": "Россия",         "price": 800_000,     "multiplier": 1.25, "distance": 700},
    "moscow":   {"name": "Москва",           "country": "Россия",         "price": 2_500_000,   "multiplier": 1.4,  "distance": 500},
    "istanbul": {"name": "Стамбул",          "country": "Турция",         "price": 4_000_000,   "multiplier": 1.35, "distance": 2200},
    "berlin":   {"name": "Берлин",           "country": "Германия",       "price": 12_000_000,  "multiplier": 1.6,  "distance": 1800},
    "dubai":    {"name": "Дубай",            "country": "ОАЭ",            "price": 8_000_000,   "multiplier": 1.7,  "distance": 4000},
    "london":   {"name": "Лондон",           "country": "Великобритания", "price": 25_000_000,  "multiplier": 1.85, "distance": 2500},
    "newyork":  {"name": "Нью-Йорк",         "country": "США",            "price": 40_000_000,  "multiplier": 2.1,  "distance": 7500},
    "monaco":   {"name": "Монако",           "country": "Монако",         "price": 120_000_000, "multiplier": 2.5,  "distance": 2800},
    "macau":    {"name": "Макао",            "country": "Китай",          "price": 55_000_000,  "multiplier": 2.0,  "distance": 7000},
}

STATUSES = [
    {"name": "Нищий",            "min_money": 0},
    {"name": "Бедный",           "min_money": 20_000},
    {"name": "Средний класс",    "min_money": 200_000},
    {"name": "Обеспеченный",     "min_money": 1_000_000},
    {"name": "Богатый",          "min_money": 6_000_000},
    {"name": "Очень богатый",    "min_money": 30_000_000},
    {"name": "Миллионер",        "min_money": 120_000_000},
    {"name": "Мультимиллионер",  "min_money": 600_000_000},
    {"name": "Миллиардер",       "min_money": 2_500_000_000},
    {"name": "Олигарх",          "min_money": 12_000_000_000},
]

PLATE_RARITIES = {
    "common":    {"name": "Обычный",     "chance": 55, "buy_min": 5_000,   "buy_max": 15_000,  "sell_mult": 0.4},
    "nice":      {"name": "Красивый",    "chance": 25, "buy_min": 25_000,  "buy_max": 80_000,  "sell_mult": 0.55},
    "rare":      {"name": "Редкий",      "chance": 12, "buy_min": 150_000, "buy_max": 400_000, "sell_mult": 0.65},
    "epic":      {"name": "Эпический",   "chance": 6,  "buy_min": 800_000, "buy_max": 2_000_000,"sell_mult": 0.7},
    "legendary": {"name": "Легендарный", "chance": 2,  "buy_min": 5_000_000,"buy_max": 15_000_000,"sell_mult": 0.75},
}

ITEMS = {
    "bread":      {"name": "Хлеб",           "price": 80,     "hunger": 15,  "health": 0,  "fatigue": 0,  "type": "food"},
    "shawarma":   {"name": "Шаурма",         "price": 350,    "hunger": 40,  "health": 0,  "fatigue": 5,  "type": "food"},
    "pizza":      {"name": "Пицца",          "price": 600,    "hunger": 55,  "health": 0,  "fatigue": 0,  "type": "food"},
    "energy":     {"name": "Энергетик",      "price": 180,    "hunger": 5,   "health": 0,  "fatigue": -25, "type": "drink"},
    "coffee":     {"name": "Кофе",           "price": 150,    "hunger": 0,   "health": 0,  "fatigue": -15, "type": "drink"},
    "medkit":     {"name": "Аптечка",        "price": 1_200,  "hunger": 0,   "health": 40, "fatigue": 0,  "type": "med"},
    "bandage":    {"name": "Бинт",           "price": 200,    "hunger": 0,   "health": 15, "fatigue": 0,  "type": "med"},
    "pills":      {"name": "Витамины",       "price": 800,    "hunger": 0,   "health": 25, "fatigue": -5, "type": "med"},
    "sim":        {"name": "SIM-карта",      "price": 750,    "hunger": 0,   "health": 0,  "fatigue": 0,  "type": "sim"},
    "fuel_can":   {"name": "Канистра 20л",   "price": 1_800,  "hunger": 0,   "health": 0,  "fatigue": 0,  "type": "fuel"},
    "water":      {"name": "Вода",           "price": 60,     "hunger": 8,   "health": 2,  "fatigue": 0,  "type": "food"},
}

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

MINER_FRAMES = {
    "frame_6":   {"name": "Рама на 6 карт",   "slots": 6,  "price_dns": 12_000,  "avito_min": 6_000,  "avito_max": 11_000},
    "frame_8":   {"name": "Рама на 8 карт",   "slots": 8,  "price_dns": 18_000,  "avito_min": 10_000, "avito_max": 16_000},
    "frame_12":  {"name": "Рама на 12 карт",  "slots": 12, "price_dns": 28_000,  "avito_min": 15_000, "avito_max": 25_000},
    "frame_24":  {"name": "Рама на 24 карты", "slots": 24, "price_dns": 55_000,  "avito_min": 30_000, "avito_max": 48_000},
}

BASEMENT_PRICE = 350_000
CRYPTO_RATE = 18
CRYPTO_PER_HASH_HOUR = 0.45
FUEL_PRICE = 65
HUNGER_PER_HOUR = 4.5
XP_FOR_LEVEL = lambda lvl: 80 + lvl * 45

def main_keyboard():
    keyboard = [
        [KeyboardButton("💼 Работать"), KeyboardButton("📊 Профиль")],
        [KeyboardButton("🏪 Бизнесы"), KeyboardButton("🚗 Транспорт")],
        [KeyboardButton("🏠 Дома"), KeyboardButton("🎒 Инвентарь")],
        [KeyboardButton("🌍 Город"), KeyboardButton("⛽ Поехать")],
        [KeyboardButton("💰 Доход"), KeyboardButton("🎁 Бонус")],
        [KeyboardButton("₿ Крипта"), KeyboardButton("🏛 ГИБДД")],
        [KeyboardButton("🛒 24/7"), KeyboardButton("🏥 Поликлиника")],
        [KeyboardButton("📦 Авито"), KeyboardButton("🏆 Топ")],
        [KeyboardButton("📜 Статусы")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

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
        users[user_id] = _new_user(username, full_name, user_id)
        save_users()
    else:
        _migrate(users[user_id])
    return users[user_id]

def _new_user(username, full_name, user_id):
    return {
        "registered": False, "username": username, "full_name": full_name or "Игрок",
        "money": 0, "level": 1, "xp": 0, "location": "vologda",
        "businesses": {k: 0 for k in BUSINESSES},
        "cars": {k: 0 for k in CARS},
        "houses": {k: 0 for k in HOUSES},
        "yachts": {k: 0 for k in YACHTS},
        "planes": {k: 0 for k in PLANES},
        "last_work": 0, "last_daily": 0, "daily_streak": 0,
        "is_admin": user_id == ADMIN_ID, "pending_job": None,
        "health": 100, "hunger": 100, "fatigue": 0, "last_needs": time.time(), "dead": False,
        "inventory": {}, "current_car": None, "car_fuel": {}, "plates": [], "sims": [],
        "crypto": 0.0, "basement": False, "gpus": [], "frames": [], "active_frame": None, "last_crypto": time.time(),
    }

def _migrate(u):
    for k in BUSINESSES: u["businesses"].setdefault(k, 0)
    for k in CARS: u["cars"].setdefault(k, 0)
    for k in HOUSES: u["houses"].setdefault(k, 0)
    for k in YACHTS: u.setdefault("yachts", {})[k] = u.get("yachts", {}).get(k, 0)
    for k in PLANES: u.setdefault("planes", {})[k] = u.get("planes", {}).get(k, 0)
    defaults = {
        "location": "vologda", "last_work": 0, "last_daily": 0, "daily_streak": 0, "pending_job": None,
        "xp": 0, "health": 100, "hunger": 100, "fatigue": 0, "last_needs": time.time(), "dead": False,
        "inventory": {}, "current_car": None, "car_fuel": {}, "plates": [], "sims": [],
        "crypto": 0.0, "basement": False, "gpus": [], "frames": [], "active_frame": None, "last_crypto": time.time(),
    }
    for k, v in defaults.items():
        u.setdefault(k, v)

def is_admin(uid): return uid == ADMIN_ID

def get_status(user):
    if user.get("is_admin"): return "👑 Создатель"
    money = user["money"]
    current = STATUSES[0]["name"]
    for s in STATUSES:
        if money >= s["min_money"]: current = s["name"]
        else: break
    return current

def calculate_passive_income(user):
    base = sum(BUSINESSES[k]["income"] * v for k, v in user["businesses"].items())
    mult = LOCATIONS.get(user.get("location", "vologda"), LOCATIONS["vologda"])["multiplier"]
    return int(base * mult)

def item_available(item, location):
    available = item.get("available_in")
    return True if not available else location in available

def has_any_house(user):
    return any(v > 0 for v in user["houses"].values())

def get_total_hashrate(user):
    if user.get("active_frame") is None: return 0
    frames = user.get("frames", [])
    if user["active_frame"] >= len(frames): return 0
    frame = frames[user["active_frame"]]
    total = 0
    for gpu_idx in frame.get("installed", []):
        if 0 <= gpu_idx < len(user.get("gpus", [])):
            gpu = user["gpus"][gpu_idx]
            if gpu["quality"] != "dead": total += gpu["hashrate"]
    return total

def calculate_crypto_income(user):
    hashrate = get_total_hashrate(user)
    if hashrate <= 0: return 0.0
    now = time.time()
    hours = min(max((now - user.get("last_crypto", now)) / 3600, 0), 24)
    return round(hashrate * hours * CRYPTO_PER_HASH_HOUR, 2)

def update_needs(user):
    now = time.time()
    last = user.get("last_needs", now)
    hours = (now - last) / 3600
    if hours < 0.05: return
    user["hunger"] = max(0, user.get("hunger", 100) - hours * HUNGER_PER_HOUR)
    if user["hunger"] <= 0:
        user["health"] = max(0, user.get("health", 100) - hours * 8)
    user["fatigue"] = max(0, user.get("fatigue", 0) - hours * 3)
    user["last_needs"] = now
    if user["health"] <= 0:
        user["dead"] = True
        user["health"] = 0
    save_users()

def add_xp(user, amount):
    user["xp"] = user.get("xp", 0) + amount
    leveled = False
    while user["xp"] >= XP_FOR_LEVEL(user["level"]) and user["level"] < 100:
        user["xp"] -= XP_FOR_LEVEL(user["level"])
        user["level"] += 1
        leveled = True
    return leveled

def inv_add(user, item_id, qty=1):
    inv = user.setdefault("inventory", {})
    inv[item_id] = inv.get(item_id, 0) + qty

def inv_remove(user, item_id, qty=1):
    inv = user.setdefault("inventory", {})
    if inv.get(item_id, 0) < qty: return False
    inv[item_id] -= qty
    if inv[item_id] <= 0: del inv[item_id]
    return True

def generate_plate():
    r = random.randint(1, 100)
    acc = 0
    rarity = "common"
    for rid, data in PLATE_RARITIES.items():
        acc += data["chance"]
        if r <= acc:
            rarity = rid
            break
    letters = "АВЕКМНОРСТУХ"
    num = f"{random.choice(letters)}{random.randint(0,999):03d}{random.choice(letters)}{random.choice(letters)}"
    region = random.choice([35, 77, 78, 99, 197, 777, 199, 97, 177, 50, 150])
    return {"plate": f"{num} {region}", "rarity": rarity}


def generate_sim():
    """Генерирует номер SIM от 4 до 7 знаков. Красивые номера реже."""
    length = random.choices([4, 5, 6, 7], weights=[35, 30, 20, 15])[0]
    # шанс красивого
    if random.random() < 0.18:
        # красивые: все одинаковые, 1234, 7777, 0000 и т.п.
        style = random.choice(["same", "seq", "mirror", "lucky"])
        if style == "same":
            d = str(random.randint(0, 9))
            number = d * length
        elif style == "seq":
            start = random.randint(0, 10 - length)
            number = "".join(str((start + i) % 10) for i in range(length))
        elif style == "mirror":
            half = "".join(str(random.randint(0, 9)) for _ in range((length + 1) // 2))
            number = (half + half[::-1])[:length]
        else:  # lucky
            lucky = ["7", "8", "0"]
            number = "".join(random.choice(lucky) for _ in range(length))
        beautiful = True
    else:
        # обычный, но не начинающийся с 0 если 4+ 
        first = str(random.randint(1, 9))
        rest = "".join(str(random.randint(0, 9)) for _ in range(length - 1))
        number = first + rest
        beautiful = False
    return {"number": number, "beautiful": beautiful, "length": length}

def generate_minigame():
    a = random.randint(2, 12)
    b = random.randint(2, 12)
    op = random.choice(["+", "-", "*"])
    if op == "+":
        correct = a + b
        question = f"{a} + {b} = ?"
    elif op == "-":
        if a < b: a, b = b, a
        correct = a - b
        question = f"{a} − {b} = ?"
    else:
        correct = a * b
        question = f"{a} × {b} = ?"
    wrongs = set()
    while len(wrongs) < 3:
        w = correct + random.choice([-1, 1]) * random.randint(1, 8)
        if w != correct and w > 0: wrongs.add(w)
    options = list(wrongs) + [correct]
    random.shuffle(options)
    return question, correct, options

# ====================== КОМАНДЫ ======================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id, update.effective_user.username, update.effective_user.full_name)
    update_needs(user)
    if not user["registered"]:
        user["registered"] = True
        save_users()
        text = (
            f"Добро пожаловать, *{user['full_name']}*!\n"
            f"Ты в *Вологде*. Следи за здоровьем, голодом и усталостью.\n"
            f"Работай, покупай транспорт, езди сам, майни крипту, собирай номера.\nУдачи!"
        )
        if is_admin(update.effective_user.id): text += "\n\n👑 Ты Создатель."
    else:
        loc = LOCATIONS[user["location"]]
        text = (
            f"С возвращением!\nСтатус: *{get_status(user)}* | Ур. *{user['level']}*\n"
            f"Город: *{loc['name']}*\n💰 {user['money']:,} ₽ | ₿ {user.get('crypto', 0):.1f}\n"
            f"❤️ {user.get('health', 100):.0f} | 🍗 {user.get('hunger', 100):.0f} | 😴 {user.get('fatigue', 0):.0f}"
        )
        if user.get("dead"): text += "\n\n💀 Ты в больнице. Иди в Поликлинику."
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=main_keyboard())

async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    if not user["registered"]: return await update.message.reply_text("Нажми /start")
    update_needs(user)
    loc = LOCATIONS[user["location"]]
    passive = calculate_passive_income(user)
    hashrate = get_total_hashrate(user)
    pending_crypto = calculate_crypto_income(user)
    xp_need = XP_FOR_LEVEL(user["level"])
    car_name = CARS[user["current_car"]]["name"] if user.get("current_car") and user["current_car"] in CARS else "нет"

    def fmt(items, data):
        lines = [f"• {data[k]['name']}: {v}" for k, v in items.items() if v > 0]
        return "\n".join(lines) if lines else "нет"

    text = (
        f"*Профиль*\n\nИмя: {user['full_name']}\n"
        f"Статус: *{get_status(user)}*" + (" 👑" if user.get("is_admin") else "") + "\n"
        f"Уровень: *{user['level']}* (XP {user.get('xp', 0)}/{xp_need})\n"
        f"Город: *{loc['name']}* ({loc['country']}) ×{loc['multiplier']}\n"
        f"Деньги: *{user['money']:,} ₽*\nКрипта: *{user.get('crypto', 0):.2f} ₿* (+{pending_crypto:.2f})\n"
        f"Хешрейт: *{hashrate}* H/ч\nТекущее авто: *{car_name}*\nНомеров: {len(user.get('plates', []))}\n\n"
        f"*Состояние*\n❤️ Здоровье: *{user.get('health', 100):.0f}/100*\n"
        f"🍗 Голод: *{user.get('hunger', 100):.0f}/100*\n😴 Усталость: *{user.get('fatigue', 0):.0f}/100*\n"
        f"{'💀 ТЫ МЁРТВ — иди в поликлинику' if user.get('dead') else ''}\n\n"
        f"Пассив: *{passive:,} ₽/час*\nСерия бонусов: *{user.get('daily_streak', 0)}*\n\n"
        f"*Бизнесы:*\n{fmt(user['businesses'], BUSINESSES)}\n\n*Машины:*\n{fmt(user['cars'], CARS)}\n\n*Дома:*\n{fmt(user['houses'], HOUSES)}"
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
    if not user["registered"]: return await update.message.reply_text("Сначала /start")
    update_needs(user)
    if user.get("dead"): return await update.message.reply_text("💀 Ты мёртв. Сначала поликлиника.")
    if user.get("fatigue", 0) >= 85: return await update.message.reply_text("😴 Слишком устал. Выпей энергетик или отдохни.")
    if user.get("hunger", 100) < 15: return await update.message.reply_text("🍗 Слишком голоден. Купи еду в 24/7.")
    keyboard = []
    for jid, job in JOBS.items():
        avail = user["level"] >= job["min_level"]
        mark = "✅" if avail else f"🔒{job['min_level']}ур"
        keyboard.append([InlineKeyboardButton(f"{job['name']} ({job['pay_min']}-{job['pay_max']}₽) {mark}", callback_data=f"job_{jid}")])
    await update.message.reply_text("Выбери работу (мини-игра + усталость + XP):", reply_markup=InlineKeyboardMarkup(keyboard))

async def collect(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    if not user["registered"]: return await update.message.reply_text("Сначала /start")
    update_needs(user)
    income = calculate_passive_income(user)
    if income == 0: return await update.message.reply_text("Нет бизнесов.")
    user["money"] += income
    save_users()
    await update.message.reply_text(f"Получено: *{income:,} ₽*\nБаланс: *{user['money']:,} ₽*", parse_mode="Markdown")

async def daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    if not user["registered"]: return await update.message.reply_text("Сначала /start")
    update_needs(user)
    now = time.time()
    last = user.get("last_daily", 0)
    if now - last < 20 * 3600:
        left = int((20 * 3600 - (now - last)) / 3600)
        return await update.message.reply_text(f"Бонус недоступен. ~{left} ч.")
    if now - last < 48 * 3600: user["daily_streak"] = user.get("daily_streak", 0) + 1
    else: user["daily_streak"] = 1
    streak = user["daily_streak"]
    base = 3500 + user["level"] * 450
    bonus = int(base * (1 + streak * 0.12))
    user["money"] += bonus
    user["last_daily"] = now
    add_xp(user, 15 + streak * 2)
    user["health"] = min(100, user.get("health", 100) + 10)
    user["fatigue"] = max(0, user.get("fatigue", 0) - 20)
    save_users()
    await update.message.reply_text(f"🎁 Бонус!\nСерия: *{streak}*\n+*{bonus:,} ₽*\n+XP\nЗдоровье↑ Усталость↓\nБаланс: *{user['money']:,} ₽*", parse_mode="Markdown")

async def top_players(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not users: return await update.message.reply_text("Пока никто не играет.")
    sorted_users = sorted(users.values(), key=lambda x: x["money"], reverse=True)[:10]
    text = "*🏆 Топ-10:*\n\n"
    for i, u in enumerate(sorted_users, 1):
        medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, f"{i}.")
        text += f"{medal} {u.get('full_name', 'Игрок')} — *{u['money']:,} ₽* (ур.{u.get('level',1)})\n"
    await update.message.reply_text(text, parse_mode="Markdown")

async def shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    loc = user["location"]
    available = [(k, v) for k, v in BUSINESSES.items() if item_available(v, loc)]
    if not available: return await update.message.reply_text("В этом городе нет бизнесов.")
    keyboard = [[InlineKeyboardButton(f"{v['name']} — {v['price']:,} ₽ (×{user['businesses'][k]})", callback_data=f"buybiz_{k}")] for k, v in available]
    await update.message.reply_text(f"Бизнесы в *{LOCATIONS[loc]['name']}*:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def cars_shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    loc = user["location"]
    available = [(k, v) for k, v in CARS.items() if item_available(v, loc)]
    if not available: return await update.message.reply_text("В этом городе нет машин.")
    keyboard = [[InlineKeyboardButton(f"{v['name']} — {v['price']:,} ₽ (×{user['cars'].get(k,0)})", callback_data=f"buycar_{k}")] for k, v in available]
    keyboard.append([InlineKeyboardButton("🔑 Выбрать текущее авто", callback_data="select_car")])
    keyboard.append([InlineKeyboardButton("⛽ Заправить текущее", callback_data="refuel")])
    await update.message.reply_text(f"Транспорт в *{LOCATIONS[loc]['name']}*:\n(можно ездить самому)", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def houses_shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    loc = user["location"]
    available = [(k, v) for k, v in HOUSES.items() if item_available(v, loc)]
    if not available: return await update.message.reply_text("В этом городе нет домов.")
    keyboard = [[InlineKeyboardButton(f"{v['name']} — {v['price']:,} ₽ (×{user['houses'][k]})", callback_data=f"buyhouse_{k}")] for k, v in available]
    if has_any_house(user) and not user.get("basement"):
        keyboard.append([InlineKeyboardButton(f"🔧 Подвал — {BASEMENT_PRICE:,} ₽", callback_data="buy_basement")])
    await update.message.reply_text(f"Дома в *{LOCATIONS[loc]['name']}*:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def city_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    current = user["location"]
    keyboard = [[InlineKeyboardButton(f"{loc['name']} — {loc['price']:,} ₽ (такси){' ✅' if lid == current else ''}", callback_data=f"moveto_{lid}")] for lid, loc in LOCATIONS.items()]
    await update.message.reply_text(f"Сейчас: *{LOCATIONS[current]['name']}*\nТакси — быстро, но дорого.\nИли «⛽ Поехать» своим ходом.", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def inventory_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    update_needs(user)
    inv = user.get("inventory", {})
    sims = user.get("sims", [])
    text = "*🎒 Инвентарь*\n\n"
    keyboard = []
    if inv:
        for iid, qty in inv.items():
            item = ITEMS.get(iid, {"name": iid})
            text += f"• {item['name']}: {qty}\n"
            keyboard.append([InlineKeyboardButton(f"Использовать {item['name']}", callback_data=f"use_{iid}")])
    else:
        text += "Предметов нет.\n"
    text += f"\n*📱 SIM-карты ({len(sims)}):*\n"
    if sims:
        for i, s in enumerate(sims[:12]):
            beaut = " ✨" if s.get("beautiful") else ""
            text += f"{i+1}. `{s['number']}` ({s.get('length', len(s['number']))}з){beaut}\n"
        if len(sims) > 12:
            text += f"... и ещё {len(sims)-12}\n"
        keyboard.append([InlineKeyboardButton("💰 Продать SIM", callback_data="sell_sim_menu")])
    else:
        text += "нет (покупай в 24/7)\n"
    if not inv and not sims:
        text = "Инвентарь пуст.\nКупи еду и SIM в 🛒 24/7."
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None, parse_mode="Markdown")

async def shop_247(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    update_needs(user)
    keyboard = [[InlineKeyboardButton(f"{v['name']} — {v['price']:,} ₽", callback_data=f"buyitem_{k}")] for k, v in ITEMS.items()]
    await update.message.reply_text("*🛒 Магазин 24/7*\nЕда, аптечки, энергетики, канистры, SIM.", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def clinic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    update_needs(user)
    text = f"*🏥 Поликлиника*\n\n❤️ Здоровье: {user.get('health', 100):.0f}/100\n{'💀 Ты мёртв — нужна реанимация' if user.get('dead') else 'Ты в порядке'}"
    keyboard = [
        [InlineKeyboardButton("💊 Витамины (800₽)", callback_data="buyitem_pills")],
        [InlineKeyboardButton("🩹 Аптечка (1200₽)", callback_data="buyitem_medkit")],
        [InlineKeyboardButton("💉 Реанимация (15 000₽)", callback_data="revive")],
        [InlineKeyboardButton("🛏 Отдохнуть (−30 уст., 2000₽)", callback_data="rest")],
    ]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def gibdd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    plates = user.get("plates", [])
    text = f"*🏛 ГИБДД*\n\nТвои номера ({len(plates)}):\n"
    if plates:
        for i, p in enumerate(plates[:15]):
            rname = PLATE_RARITIES.get(p["rarity"], {}).get("name", p["rarity"])
            text += f"{i+1}. `{p['plate']}` — {rname}\n"
        if len(plates) > 15: text += f"... и ещё {len(plates)-15}\n"
    else: text += "пока нет\n"
    text += "\nКупи случайный номер (цена от редкости)."
    keyboard = [
        [InlineKeyboardButton("🎲 Купить случайный Н/З", callback_data="buy_plate")],
        [InlineKeyboardButton("💰 Продать номер", callback_data="sell_plate_menu")],
    ]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def drive_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    update_needs(user)
    if user.get("dead"): return await update.message.reply_text("💀 Мёртвые не ездят.")
    if not user.get("current_car") or user["cars"].get(user["current_car"], 0) < 1:
        return await update.message.reply_text("Сначала купи и выбери машину в «🚗 Транспорт».")
    car = CARS[user["current_car"]]
    fuel = user.get("car_fuel", {}).get(user["current_car"], 0)
    text = f"*⛽ Поехать сам*\n\nАвто: *{car['name']}*\nБензин: *{fuel:.1f}/{car['fuel_cap']} л*\nРасход: {car['consumption']} л/100км\n\nВыбери город:"
    keyboard = []
    cur = user["location"]
    for lid, loc in LOCATIONS.items():
        if lid == cur: continue
        dist = abs(loc.get("distance", 0) - LOCATIONS[cur].get("distance", 0))
        need_fuel = dist / 100 * car["consumption"]
        keyboard.append([InlineKeyboardButton(f"{loc['name']} (~{dist} км, {need_fuel:.1f} л)", callback_data=f"drive_{lid}")])
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def avito_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🖥 Видеокарты и рамы", callback_data="crypto_avito")],
        [InlineKeyboardButton("🚗 Машины с рук", callback_data="avito_cars")],
        [InlineKeyboardButton("🏠 Квартиры/дома", callback_data="avito_houses")],
        [InlineKeyboardButton("📦 Случайное объявление", callback_data="avito_random")],
    ]
    await update.message.reply_text("*📦 Авито*\nБ/у рынок. Цены ниже, но бывают сюрпризы.", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def crypto_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    if not user["registered"]: return await update.message.reply_text("Сначала /start")
    update_needs(user)
    hashrate = get_total_hashrate(user)
    pending = calculate_crypto_income(user)
    basement = "✅" if user.get("basement") else "❌"
    text = f"*₿ Крипта*\n\nБаланс: *{user.get('crypto', 0):.2f} ₿*\nК сбору: *{pending:.2f} ₿*\nХешрейт: *{hashrate}* H/ч\nПодвал: {basement}\nКарт: {len(user.get('gpus', []))} | Рам: {len(user.get('frames', []))}"
    keyboard = [
        [InlineKeyboardButton("⛏ Собрать", callback_data="crypto_collect")],
        [InlineKeyboardButton("🛒 DNS", callback_data="crypto_dns"), InlineKeyboardButton("📦 Авито", callback_data="crypto_avito")],
        [InlineKeyboardButton("🖥 Мои карты", callback_data="crypto_my_gpus")],
        [InlineKeyboardButton("🔧 Рамы", callback_data="crypto_frames")],
        [InlineKeyboardButton("💸 Продать крипту", callback_data="crypto_sell")],
        [InlineKeyboardButton("🏠 Подвал", callback_data="buy_basement")],
    ]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = get_user(query.from_user.id)
    data = query.data
    update_needs(user)

    if data.startswith("job_"):
        if user.get("dead"): return await query.edit_message_text("💀 Сначала поликлиника.")
        if user.get("fatigue", 0) >= 85: return await query.edit_message_text("😴 Слишком устал.")
        job_id = data[4:]
        job = JOBS.get(job_id)
        if not job: return
        if user["level"] < job["min_level"]: return await query.answer(f"Нужен {job['min_level']} ур.", show_alert=True)
        now = time.time()
        if now - user["last_work"] < job["cooldown"]:
            return await query.answer(f"Подожди {int(job['cooldown'] - (now - user['last_work']))} сек.", show_alert=True)
        question, correct, options = generate_minigame()
        user["pending_job"] = {"job_id": job_id, "correct": correct, "started": now}
        save_users()
        keyboard = [[InlineKeyboardButton(str(o), callback_data=f"mg_{o}")] for o in options]
        await query.edit_message_text(f"Работа: *{job['name']}*\n\n🧠 Реши пример:\n*{question}*", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        return

    if data.startswith("mg_"):
        pending = user.get("pending_job")
        if not pending: return await query.edit_message_text("Сессия устарела.")
        try: answer = int(data[3:])
        except: return
        job = JOBS.get(pending["job_id"])
        if not job:
            user["pending_job"] = None
            save_users()
            return
        now = time.time()
        if now - pending.get("started", 0) > 120:
            user["pending_job"] = None
            save_users()
            return await query.edit_message_text("Время вышло.")
        loc_mult = LOCATIONS[user["location"]]["multiplier"]
        pay = int(random.randint(job["pay_min"], job["pay_max"]) * loc_mult)
        user["last_work"] = now
        user["pending_job"] = None
        user["fatigue"] = min(100, user.get("fatigue", 0) + job.get("fatigue", 10))
        success = answer == pending["correct"]
        if success:
            user["money"] += pay
            leveled = add_xp(user, job.get("xp", 10))
            level_up = f"\n\n🎉 Уровень → *{user['level']}*!" if leveled else ""
            save_users()
            await query.edit_message_text(f"✅ Верно!\n*{job['name']}* → *{pay:,} ₽*\n+{job.get('xp',10)} XP\nУсталость +{job.get('fatigue',10)}\nБаланс: *{user['money']:,} ₽*{level_up}", parse_mode="Markdown")
        else:
            reduced = int(pay * random.uniform(0.2, 0.35))
            user["money"] += reduced
            add_xp(user, max(1, job.get("xp", 10) // 3))
            save_users()
            await query.edit_message_text(f"❌ Неверно (ответ {pending['correct']})\nПолучено *{reduced:,} ₽*\nУсталость растёт.\nБаланс: *{user['money']:,} ₽*", parse_mode="Markdown")
        return

    mapping = {"buybiz_": ("businesses", BUSINESSES), "buycar_": ("cars", CARS), "buyhouse_": ("houses", HOUSES), "buyyacht_": ("yachts", YACHTS), "buyplane_": ("planes", PLANES)}
    for prefix, (field, catalog) in mapping.items():
        if data.startswith(prefix):
            item_id = data[len(prefix):]
            if item_id not in catalog: return
            item = catalog[item_id]
            if not item_available(item, user["location"]): return await query.edit_message_text("Недоступно в этом городе.")
            price = item["price"]
            if user["money"] < price: return await query.edit_message_text(f"Не хватает ({price:,} ₽)")
            user["money"] -= price
            user[field][item_id] = user[field].get(item_id, 0) + 1
            if field == "cars":
                user.setdefault("car_fuel", {})[item_id] = item.get("fuel_cap", 50) * 0.3
                if not user.get("current_car"): user["current_car"] = item_id
            save_users()
            await query.edit_message_text(f"Куплено: *{item['name']}*\nОстаток: *{user['money']:,} ₽*", parse_mode="Markdown")
            return

    if data == "buy_basement":
        if user.get("basement"): return await query.edit_message_text("Подвал уже есть.")
        if not has_any_house(user): return await query.edit_message_text("Сначала купи дом.")
        if user["money"] < BASEMENT_PRICE: return await query.edit_message_text(f"Нужно {BASEMENT_PRICE:,} ₽")
        user["money"] -= BASEMENT_PRICE
        user["basement"] = True
        save_users()
        await query.edit_message_text(f"✅ Подвал готов.\nОстаток: *{user['money']:,} ₽*", parse_mode="Markdown")
        return

    if data.startswith("moveto_"):
        loc_id = data[7:]
        if loc_id not in LOCATIONS or loc_id == user["location"]: return await query.edit_message_text("Уже здесь.")
        price = LOCATIONS[loc_id]["price"]
        if user["money"] < price: return await query.edit_message_text(f"Не хватает ({price:,} ₽)")
        user["money"] -= price
        user["location"] = loc_id
        user["fatigue"] = min(100, user.get("fatigue", 0) + 5)
        save_users()
        loc = LOCATIONS[loc_id]
        await query.edit_message_text(f"Приехал в *{loc['name']}* на такси.\n×{loc['multiplier']}\nОстаток: *{user['money']:,} ₽*", parse_mode="Markdown")
        return

    if data == "select_car":
        owned = [k for k, v in user["cars"].items() if v > 0]
        if not owned: return await query.edit_message_text("Нет машин.")
        keyboard = [[InlineKeyboardButton(CARS[k]["name"], callback_data=f"setcar_{k}")] for k in owned]
        await query.edit_message_text("Выбери текущее авто:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if data.startswith("setcar_"):
        cid = data[7:]
        if user["cars"].get(cid, 0) < 1: return
        user["current_car"] = cid
        save_users()
        await query.edit_message_text(f"Теперь ездишь на *{CARS[cid]['name']}*", parse_mode="Markdown")
        return

    if data == "refuel":
        cid = user.get("current_car")
        if not cid or user["cars"].get(cid, 0) < 1: return await query.edit_message_text("Нет выбранного авто.")
        car = CARS[cid]
        fuel = user.setdefault("car_fuel", {}).get(cid, 0)
        need = car["fuel_cap"] - fuel
        if need < 1: return await query.edit_message_text("Бак полный.")
        cost = int(need * FUEL_PRICE)
        if user["money"] < cost: return await query.edit_message_text(f"Нужно ~{cost:,} ₽")
        user["money"] -= cost
        user["car_fuel"][cid] = car["fuel_cap"]
        save_users()
        await query.edit_message_text(f"Заправлено на {need:.1f} л за *{cost:,} ₽*", parse_mode="Markdown")
        return

    if data.startswith("drive_"):
        loc_id = data[6:]
        if loc_id not in LOCATIONS or loc_id == user["location"]: return await query.edit_message_text("Уже здесь.")
        cid = user.get("current_car")
        if not cid or user["cars"].get(cid, 0) < 1: return await query.edit_message_text("Нет авто.")
        car = CARS[cid]
        fuel = user.setdefault("car_fuel", {}).get(cid, 0)
        dist = abs(LOCATIONS[loc_id].get("distance", 0) - LOCATIONS[user["location"]].get("distance", 0))
        need = dist / 100 * car["consumption"]
        if fuel < need: return await query.edit_message_text(f"Не хватает бензина ({fuel:.1f}/{need:.1f} л).")
        user["car_fuel"][cid] = fuel - need
        user["location"] = loc_id
        user["fatigue"] = min(100, user.get("fatigue", 0) + 8 + dist / 500)
        user["hunger"] = max(0, user.get("hunger", 100) - 5)
        save_users()
        loc = LOCATIONS[loc_id]
        await query.edit_message_text(f"🚗 Доехал до *{loc['name']}* на {car['name']}.\nПотрачено {need:.1f} л. Осталось {user['car_fuel'][cid]:.1f} л.", parse_mode="Markdown")
        return

    if data.startswith("buyitem_"):
        iid = data[8:]
        if iid not in ITEMS: return
        item = ITEMS[iid]
        if user["money"] < item["price"]: return await query.edit_message_text(f"Не хватает ({item['price']:,} ₽)")
        user["money"] -= item["price"]
        if iid == "sim":
            sim = generate_sim()
            user.setdefault("sims", []).append(sim)
            save_users()
            beaut = "✨ Красивый!" if sim["beautiful"] else ""
            await query.edit_message_text(
                f"📱 Куплена SIM-карта\n"
                f"Номер: `{sim['number']}` ({sim['length']} знаков) {beaut}\n"
                f"Остаток: *{user['money']:,} ₽*\n"
                f"Симки хранятся отдельно (смотри в Инвентаре).",
                parse_mode="Markdown"
            )
        else:
            inv_add(user, iid)
            save_users()
            await query.edit_message_text(f"Куплено: *{item['name']}*\nВ инвентаре. Остаток: *{user['money']:,} ₽*", parse_mode="Markdown")
        return

    if data.startswith("use_"):
        iid = data[4:]
        if not inv_remove(user, iid): return await query.edit_message_text("Нет такого предмета.")
        item = ITEMS.get(iid, {})
        if iid == "fuel_can":
            cid = user.get("current_car")
            if not cid:
                inv_add(user, iid)
                return await query.edit_message_text("Нет выбранного авто.")
            car = CARS[cid]
            add = min(20, car["fuel_cap"] - user.setdefault("car_fuel", {}).get(cid, 0))
            user["car_fuel"][cid] = user["car_fuel"].get(cid, 0) + add
            save_users()
            await query.edit_message_text(f"Залил {add:.0f} л из канистры.")
            return
        user["hunger"] = min(100, user.get("hunger", 100) + item.get("hunger", 0))
        user["health"] = min(100, user.get("health", 100) + item.get("health", 0))
        user["fatigue"] = max(0, user.get("fatigue", 0) + item.get("fatigue", 0))
        if user["health"] > 0: user["dead"] = False
        save_users()
        await query.edit_message_text(f"Использовано: *{item.get('name', iid)}*\n❤️ {user['health']:.0f} | 🍗 {user['hunger']:.0f} | 😴 {user['fatigue']:.0f}", parse_mode="Markdown")
        return

    if data == "revive":
        if not user.get("dead") and user.get("health", 100) > 20: return await query.edit_message_text("Ты и так жив.")
        if user["money"] < 15000: return await query.edit_message_text("Нужно 15 000 ₽")
        user["money"] -= 15000
        user["health"] = 60
        user["dead"] = False
        user["fatigue"] = max(0, user.get("fatigue", 0) - 30)
        save_users()
        await query.edit_message_text("💉 Реанимация успешна. Здоровье 60.")
        return

    if data == "rest":
        if user["money"] < 2000: return await query.edit_message_text("Нужно 2000 ₽")
        user["money"] -= 2000
        user["fatigue"] = max(0, user.get("fatigue", 0) - 30)
        user["health"] = min(100, user.get("health", 100) + 5)
        save_users()
        await query.edit_message_text(f"Отдохнул. Усталость: {user['fatigue']:.0f}")
        return

    if data == "buy_plate":
        p = generate_plate()
        rdata = PLATE_RARITIES[p["rarity"]]
        price = random.randint(rdata["buy_min"], rdata["buy_max"])
        if user["money"] < price: return await query.edit_message_text(f"Этот номер стоит {price:,} ₽ — не хватает.")
        user["money"] -= price
        user.setdefault("plates", []).append(p)
        save_users()
        await query.edit_message_text(f"Номер выдан:\n`{p['plate']}`\nРедкость: *{rdata['name']}*\nЦена: {price:,} ₽\nОстаток: *{user['money']:,} ₽*", parse_mode="Markdown")
        return

    if data == "sell_plate_menu":
        plates = user.get("plates", [])
        if not plates: return await query.edit_message_text("Нет номеров.")
        keyboard = []
        for i, p in enumerate(plates[:20]):
            rdata = PLATE_RARITIES[p["rarity"]]
            sell = int(random.randint(rdata["buy_min"], rdata["buy_max"]) * rdata["sell_mult"])
            keyboard.append([InlineKeyboardButton(f"{p['plate']} → ~{sell:,} ₽", callback_data=f"sellplate_{i}")])
        await query.edit_message_text("Выбери номер для продажи:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if data.startswith("sellplate_"):
        try: idx = int(data[10:])
        except: return
        plates = user.get("plates", [])
        if not (0 <= idx < len(plates)): return await query.edit_message_text("Номер не найден.")
        p = plates.pop(idx)
        rdata = PLATE_RARITIES[p["rarity"]]
        sell = int(random.randint(rdata["buy_min"], rdata["buy_max"]) * rdata["sell_mult"])
        user["money"] += sell
        save_users()
        await query.edit_message_text(f"Продан `{p['plate']}` за *{sell:,} ₽*", parse_mode="Markdown")
        return

    if data == "sell_sim_menu":
        sims = user.get("sims", [])
        if not sims:
            return await query.edit_message_text("Нет SIM-карт.")
        keyboard = []
        for i, s in enumerate(sims[:15]):
            base = 200 + s.get("length", 4) * 80
            if s.get("beautiful"):
                base = int(base * 3.5)
            keyboard.append([InlineKeyboardButton(f"{s['number']} → ~{base:,} ₽", callback_data=f"sellsim_{i}")])
        await query.edit_message_text("Выбери SIM для продажи:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if data.startswith("sellsim_"):
        try: idx = int(data[8:])
        except: return
        sims = user.get("sims", [])
        if not (0 <= idx < len(sims)):
            return await query.edit_message_text("SIM не найдена.")
        s = sims.pop(idx)
        base = 200 + s.get("length", 4) * 80
        if s.get("beautiful"):
            base = int(base * 3.5)
        price = random.randint(int(base * 0.85), int(base * 1.15))
        user["money"] += price
        save_users()
        beaut = " (красивый)" if s.get("beautiful") else ""
        await query.edit_message_text(f"Продана SIM `{s['number']}`{beaut} за *{price:,} ₽*", parse_mode="Markdown")
        return

    if data == "avito_cars":
        pool = list(CARS.keys())
        random.shuffle(pool)
        keyboard = []
        for cid in pool[:6]:
            c = CARS[cid]
            price = int(c["price"] * random.uniform(0.55, 0.85))
            keyboard.append([InlineKeyboardButton(f"{c['name']} — {price:,} ₽", callback_data=f"avito_buycar_{cid}_{price}")])
        await query.edit_message_text("*🚗 Авито — машины с рук*\nРиск кидалова/битых.", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        return

    if data.startswith("avito_buycar_"):
        parts = data.split("_")
        cid, price = parts[2], int(parts[3])
        if cid not in CARS: return
        if user["money"] < price: return await query.edit_message_text("Не хватает денег.")
        user["money"] -= price
        roll = random.random()
        if roll < 0.12:
            refund = int(price * 0.15)
            user["money"] += refund
            save_users()
            await query.edit_message_text(f"💀 Кинули. Вернули только {refund:,} ₽.")
            return
        user["cars"][cid] = user["cars"].get(cid, 0) + 1
        user.setdefault("car_fuel", {})[cid] = CARS[cid]["fuel_cap"] * (0.2 if roll < 0.30 else 0.5)
        if not user.get("current_car"): user["current_car"] = cid
        save_users()
        msg = "с повышенным расходом и почти пустым баком" if roll < 0.30 else "в нормальном состоянии"
        await query.edit_message_text(f"✅ Купил *{CARS[cid]['name']}* за {price:,} ₽ ({msg}).", parse_mode="Markdown")
        return

    if data == "avito_houses":
        pool = list(HOUSES.keys())
        random.shuffle(pool)
        keyboard = [[InlineKeyboardButton(f"{HOUSES[hid]['name']} — {int(HOUSES[hid]['price'] * random.uniform(0.6, 0.88)):,} ₽", callback_data=f"avito_buyhouse_{hid}_{int(HOUSES[hid]['price'] * random.uniform(0.6, 0.88))}")] for hid in pool[:5]]
        await query.edit_message_text("*🏠 Авито — жильё*", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        return

    if data.startswith("avito_buyhouse_"):
        parts = data.split("_")
        hid, price = parts[2], int(parts[3])
        if hid not in HOUSES: return
        if user["money"] < price: return await query.edit_message_text("Не хватает.")
        user["money"] -= price
        if random.random() < 0.15:
            refund = int(price * 0.2)
            user["money"] += refund
            save_users()
            await query.edit_message_text(f"Обман. Вернули {refund:,} ₽.")
            return
        user["houses"][hid] = user["houses"].get(hid, 0) + 1
        save_users()
        await query.edit_message_text(f"✅ Куплено: *{HOUSES[hid]['name']}*", parse_mode="Markdown")
        return

    if data == "avito_random":
        choice = random.choice(["car", "house", "nothing"])
        if choice == "car":
            cid = random.choice(list(CARS.keys()))
            price = int(CARS[cid]["price"] * random.uniform(0.5, 0.8))
            await query.edit_message_text(f"Случайное: {CARS[cid]['name']} за {price:,} ₽", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Купить", callback_data=f"avito_buycar_{cid}_{price}")]]))
        elif choice == "house":
            hid = random.choice(list(HOUSES.keys()))
            price = int(HOUSES[hid]["price"] * random.uniform(0.55, 0.85))
            await query.edit_message_text(f"Случайное: {HOUSES[hid]['name']} за {price:,} ₽", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Купить", callback_data=f"avito_buyhouse_{hid}_{price}")]]))
        else:
            await query.edit_message_text("Сегодня ничего интересного.")
        return

    # Крипта
    if data == "crypto_collect":
        pending = calculate_crypto_income(user)
        if pending <= 0: return await query.edit_message_text("Нечего собирать.")
        user["crypto"] = round(user.get("crypto", 0) + pending, 2)
        user["last_crypto"] = time.time()
        save_users()
        await query.edit_message_text(f"⛏ +*{pending:.2f} ₿*\nВсего: *{user['crypto']:.2f} ₿*", parse_mode="Markdown")
        return

    if data == "crypto_sell":
        amount = user.get("crypto", 0)
        if amount < 1: return await query.edit_message_text("Мало крипты.")
        money = int(amount * CRYPTO_RATE)
        user["money"] += money
        user["crypto"] = 0.0
        save_users()
        await query.edit_message_text(f"Продано за *{money:,} ₽*", parse_mode="Markdown")
        return

    if data == "crypto_dns":
        keyboard = [[InlineKeyboardButton(f"{g['name']} — {g['price_dns']:,} ₽", callback_data=f"buygpu_dns_{gid}")] for gid, g in GPUS.items()]
        keyboard += [[InlineKeyboardButton(f"{f['name']} — {f['price_dns']:,} ₽", callback_data=f"buyframe_dns_{fid}")] for fid, f in MINER_FRAMES.items()]
        keyboard.append([InlineKeyboardButton("« Назад", callback_data="crypto_back")])
        await query.edit_message_text("*DNS* — всё новое.", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        return

    if data == "crypto_avito":
        keyboard = [[InlineKeyboardButton(f"{g['name']} — {g['avito_min']:,}–{g['avito_max']:,}", callback_data=f"buygpu_avito_{gid}")] for gid, g in GPUS.items()]
        keyboard += [[InlineKeyboardButton(f"{f['name']} б/у", callback_data=f"buyframe_avito_{fid}")] for fid, f in MINER_FRAMES.items()]
        keyboard.append([InlineKeyboardButton("« Назад", callback_data="crypto_back")])
        await query.edit_message_text("*Авито* — дешевле, риск (10% мёртвая, 25% плохая).", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        return

    if data == "crypto_back":
        await crypto_menu(update, context)
        return

    if data.startswith("buygpu_dns_"):
        gid = data[11:]
        if gid not in GPUS: return
        g = GPUS[gid]
        if user["money"] < g["price_dns"]: return await query.edit_message_text("Не хватает.")
        user["money"] -= g["price_dns"]
        user.setdefault("gpus", []).append({"gpu_id": gid, "quality": "good", "hashrate": g["hashrate"], "source": "dns"})
        save_users()
        await query.edit_message_text(f"✅ {g['name']} куплена.")
        return

    if data.startswith("buygpu_avito_"):
        gid = data[13:]
        if gid not in GPUS: return
        g = GPUS[gid]
        price = random.randint(g["avito_min"], g["avito_max"])
        if user["money"] < price: return await query.edit_message_text("Не хватает.")
        user["money"] -= price
        roll = random.random()
        if roll < 0.10: q, hr, t = "dead", 0, "💀 Мёртвая"
        elif roll < 0.35: q, hr, t = "bad", max(1, g["hashrate"] // 2), "⚠️ Плохая"
        else: q, hr, t = "good", g["hashrate"], "✅ Норм"
        user.setdefault("gpus", []).append({"gpu_id": gid, "quality": q, "hashrate": hr, "source": "avito"})
        save_users()
        await query.edit_message_text(f"Куплено: {g['name']}\n{t}\nЦена {price:,} ₽")
        return

    if data.startswith("buyframe_dns_"):
        fid = data[13:]
        if fid not in MINER_FRAMES: return
        f = MINER_FRAMES[fid]
        if not user.get("basement"): return await query.edit_message_text("Нужен подвал.")
        if user["money"] < f["price_dns"]: return await query.edit_message_text("Не хватает.")
        user["money"] -= f["price_dns"]
        user.setdefault("frames", []).append({"frame_id": fid, "quality": "good", "slots": f["slots"], "installed": [], "source": "dns"})
        if user.get("active_frame") is None: user["active_frame"] = len(user["frames"]) - 1
        save_users()
        await query.edit_message_text(f"✅ Рама {f['name']} куплена.")
        return

    if data.startswith("buyframe_avito_"):
        fid = data[15:]
        if fid not in MINER_FRAMES: return
        f = MINER_FRAMES[fid]
        if not user.get("basement"): return await query.edit_message_text("Нужен подвал.")
        price = random.randint(f["avito_min"], f["avito_max"])
        if user["money"] < price: return await query.edit_message_text("Не хватает.")
        user["money"] -= price
        roll = random.random()
        if roll < 0.08: q, slots = "dead", 0
        elif roll < 0.30: q, slots = "bad", max(1, f["slots"] - random.randint(1, 3))
        else: q, slots = "good", f["slots"]
        user.setdefault("frames", []).append({"frame_id": fid, "quality": q, "slots": slots, "installed": [], "source": "avito"})
        if user.get("active_frame") is None and q != "dead": user["active_frame"] = len(user["frames"]) - 1
        save_users()
        await query.edit_message_text(f"Рама куплена ({q}, слотов {slots}).")
        return

    if data == "crypto_my_gpus":
        gpus = user.get("gpus", [])
        if not gpus: return await query.edit_message_text("Нет видеокарт.")
        text = "*Видеокарты:*\n"
        keyboard = []
        for i, gpu in enumerate(gpus):
            name = GPUS.get(gpu["gpu_id"], {}).get("name", gpu["gpu_id"])
            q = {"good": "✅", "bad": "⚠️", "dead": "💀"}.get(gpu["quality"], "?")
            text += f"{i+1}. {q} {name} — {gpu['hashrate']}H\n"
            sell = 500 if gpu["quality"] == "dead" else int(GPUS.get(gpu["gpu_id"], {}).get("price_dns", 10000) * (0.35 if gpu["quality"]=="good" else 0.18))
            keyboard.append([InlineKeyboardButton(f"Продать #{i+1} (~{sell})", callback_data=f"sellgpu_{i}")])
        keyboard.append([InlineKeyboardButton("« Назад", callback_data="crypto_back")])
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        return

    if data.startswith("sellgpu_"):
        try: idx = int(data[8:])
        except: return
        gpus = user.get("gpus", [])
        if not (0 <= idx < len(gpus)): return
        gpu = gpus[idx]
        base = GPUS.get(gpu["gpu_id"], {}).get("price_dns", 10000)
        price = 500 if gpu["quality"] == "dead" else int(base * (0.35 if gpu["quality"] == "good" else 0.18))
        for fr in user.get("frames", []):
            fr["installed"] = [x - 1 if x > idx else x for x in fr.get("installed", []) if x != idx]
        user["gpus"].pop(idx)
        user["money"] += price
        save_users()
        await query.edit_message_text(f"Продано за {price:,} ₽")
        return

    if data == "crypto_frames":
        frames = user.get("frames", [])
        if not frames: return await query.edit_message_text("Нет рам.")
        text = "*Рамы:*\n"
        keyboard = []
        for i, fr in enumerate(frames):
            name = MINER_FRAMES.get(fr["frame_id"], {}).get("name", "?")
            act = " ⭐" if user.get("active_frame") == i else ""
            text += f"{i+1}. {name}{act} — {len(fr.get('installed',[]))}/{fr['slots']}\n"
            keyboard.append([InlineKeyboardButton(f"Установить в #{i+1}", callback_data=f"install_{i}"), InlineKeyboardButton(f"Активная #{i+1}", callback_data=f"setactive_{i}")])
        keyboard.append([InlineKeyboardButton("« Назад", callback_data="crypto_back")])
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        return

    if data.startswith("setactive_"):
        try: idx = int(data[10:])
        except: return
        if 0 <= idx < len(user.get("frames", [])):
            user["active_frame"] = idx
            save_users()
            await query.edit_message_text(f"Рама #{idx+1} активна.")
        return

    if data.startswith("install_"):
        try: fidx = int(data[8:])
        except: return
        frames = user.get("frames", [])
        if not (0 <= fidx < len(frames)): return
        frame = frames[fidx]
        if frame["slots"] <= 0: return await query.edit_message_text("Рама нерабочая.")
        used = set()
        for fr in frames: used.update(fr.get("installed", []))
        free = [i for i in range(len(user.get("gpus", []))) if i not in used and user["gpus"][i]["quality"] != "dead"]
        free_slots = frame["slots"] - len(frame.get("installed", []))
        if not free or free_slots <= 0: return await query.edit_message_text("Нет свободных карт или слотов.")
        to_inst = free[:free_slots]
        frame.setdefault("installed", []).extend(to_inst)
        save_users()
        await query.edit_message_text(f"Установлено {len(to_inst)} карт. Хешрейт: {get_total_hashrate(user)}")
        return

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    mapping = {
        "💼 Работать": work_menu, "📊 Профиль": status_cmd, "🏪 Бизнесы": shop, "🚗 Транспорт": cars_shop,
        "🏠 Дома": houses_shop, "🌍 Город": city_menu, "💰 Доход": collect, "🎁 Бонус": daily,
        "🏆 Топ": top_players, "📜 Статусы": statuses_list, "₿ Крипта": crypto_menu,
        "🎒 Инвентарь": inventory_cmd, "🛒 24/7": shop_247, "🏥 Поликлиника": clinic,
        "🏛 ГИБДД": gibdd, "⛽ Поехать": drive_menu, "📦 Авито": avito_menu,
    }
    handler = mapping.get(text)
    if handler: await handler(update, context)

async def admin_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return await update.message.reply_text("Нет доступа.")
    await update.message.reply_text("*Админ:* /setmoney /addmoney /setlevel /give /setcrypto /resetme /users", parse_mode="Markdown")

async def set_money(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    if not context.args: return await update.message.reply_text("/setmoney 1000000")
    try:
        user = get_user(update.effective_user.id)
        user["money"] = int(context.args[0])
        save_users()
        await update.message.reply_text(f"Баланс: {user['money']:,} ₽")
    except: await update.message.reply_text("Ошибка")

async def add_money(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    if not context.args: return
    try:
        user = get_user(update.effective_user.id)
        user["money"] += int(context.args[0])
        save_users()
        await update.message.reply_text(f"Теперь: {user['money']:,} ₽")
    except: pass

async def set_level(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    if not context.args: return
    try:
        user = get_user(update.effective_user.id)
        user["level"] = max(1, int(context.args[0]))
        save_users()
        await update.message.reply_text(f"Уровень: {user['level']}")
    except: pass

async def give_money(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    if len(context.args) < 2: return
    try:
        target, amount = int(context.args[0]), int(context.args[1])
        if target not in users: return await update.message.reply_text("Не найден")
        users[target]["money"] += amount
        save_users()
        await update.message.reply_text(f"Выдано {amount:,}")
    except: pass

async def set_crypto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    if not context.args: return
    try:
        user = get_user(update.effective_user.id)
        user["crypto"] = float(context.args[0])
        save_users()
        await update.message.reply_text(f"Крипта: {user['crypto']:.2f}")
    except: pass

async def reset_me(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    uid = update.effective_user.id
    users[uid] = _new_user(update.effective_user.username, update.effective_user.full_name, uid)
    users[uid]["registered"] = True
    save_users()
    await update.message.reply_text("Сброшено. Снова в Вологде.")

async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    text = "*Игроки:*\n"
    for uid, u in list(users.items())[:40]:
        text += f"`{uid}` {u.get('full_name')} — {u['money']:,} ₽ | {u.get('crypto',0):.1f}₿\n"
    await update.message.reply_text(text or "Пусто", parse_mode="Markdown")

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
    app.add_handler(CommandHandler("city", city_menu))
    app.add_handler(CommandHandler("crypto", crypto_menu))
    app.add_handler(CommandHandler("inventory", inventory_cmd))
    app.add_handler(CommandHandler("admin", admin_help))
    app.add_handler(CommandHandler("setmoney", set_money))
    app.add_handler(CommandHandler("addmoney", add_money))
    app.add_handler(CommandHandler("setlevel", set_level))
    app.add_handler(CommandHandler("give", give_money))
    app.add_handler(CommandHandler("setcrypto", set_crypto))
    app.add_handler(CommandHandler("resetme", reset_me))
    app.add_handler(CommandHandler("users", list_users))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, button_handler))
    print("Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()
