import os

# =============================
# 🔧 НАСТРОЙКИ БОТА
# =============================

# Telegram Bot Token (получить у @BotFather)
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

# ID администраторов (через запятую)
ADMIN_IDS = [6477447974]  # Замените на свои Telegram ID

# Комиссия обменника (в процентах)
EXCHANGE_FEE_PERCENT = 1.5

# Минимальная сумма обмена в USD
MIN_EXCHANGE_USD = 10.0

# Максимальная сумма обмена в USD
MAX_EXCHANGE_USD = 50000.0

# Реферальный бонус (в процентах от комиссии)
REFERRAL_BONUS_PERCENT = 20.0

# Поддерживаемые валюты
SUPPORTED_CRYPTO = ["BTC", "ETH", "USDT", "BNB", "SOL", "TON", "LTC", "XRP"]
SUPPORTED_FIAT = ["RUB", "USD", "EUR", "UAH", "KZT"]

# CoinGecko API (бесплатный, без ключа)
COINGECKO_API = "https://api.coingecko.com/api/v3"

# Маппинг символов к CoinGecko ID
COIN_IDS = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "USDT": "tether",
    "BNB": "binancecoin",
    "SOL": "solana",
    "TON": "the-open-network",
    "LTC": "litecoin",
    "XRP": "ripple",
}

# Telegram ID группы поддержки (опционально)
SUPPORT_CHAT_ID = None  # Например: -1001234567890

# База данных
DATABASE_PATH = "crypto_exchange.db"
