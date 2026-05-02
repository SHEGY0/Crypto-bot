# 🤖 CryptoSwap — Telegram Bot для крипто обменника

## 📋 Функции

- 💱 **Обмен криптовалют** — BTC, ETH, USDT, BNB, SOL, TON, LTC, XRP + фиат (RUB, USD, EUR)
- 📊 **Курсы в реальном времени** — через CoinGecko API (бесплатно, без ключа)
- 📋 **История транзакций** — последние 10 операций
- 👥 **Реферальная система** — 20% от комиссии за каждого реферала
- 💬 **Поддержка** — тикеты, пересылаемые администратору
- 👤 **Профиль пользователя** — статистика и реф. код

---

## 🚀 Установка и запуск

### 1. Клонировать / распаковать проект

```bash
cd crypto_bot
```

### 2. Установить зависимости

```bash
pip install -r requirements.txt
```

### 3. Настроить конфигурацию

Откройте `config.py` и заполните:

```python
BOT_TOKEN = "ВАШ_ТОКЕН"        # Получить у @BotFather
ADMIN_IDS = [123456789]        # Ваш Telegram ID (узнать у @userinfobot)
```

Также настройте:
- `EXCHANGE_FEE_PERCENT` — комиссия обменника (по умолчанию 1.5%)
- `MIN_EXCHANGE_USD` / `MAX_EXCHANGE_USD` — лимиты обмена
- `REFERRAL_BONUS_PERCENT` — реферальный бонус (по умолчанию 20%)

### 4. Запустить бота

```bash
python bot.py
```

---

## 📁 Структура проекта

```
crypto_bot/
├── bot.py              # Точка входа
├── config.py           # Настройки
├── database.py         # SQLite база данных
├── services.py         # Получение курсов (CoinGecko)
├── keyboards.py        # Клавиатуры Telegram
├── requirements.txt    # Зависимости
└── handlers/
    ├── start.py        # /start, профиль
    ├── rates.py        # Курсы валют
    ├── exchange.py     # Процесс обмена (FSM)
    ├── history.py      # История транзакций
    ├── referral.py     # Реферальная система
    └── support.py      # Поддержка пользователей
```

---

## ⚙️ Архитектура

- **aiogram 3.x** — асинхронный фреймворк для Telegram ботов
- **aiosqlite** — асинхронная SQLite база данных
- **aiohttp** — HTTP клиент для запросов к CoinGecko
- **FSM (Finite State Machine)** — управление диалогами обмена и поддержки

---

## 🔒 Важно для продакшена

1. **Кошелёк** — в `handlers/exchange.py` замените адрес на свой реальный кошелёк
2. **Проверка платежей** — интегрируйте реальный API blockchain (Blockchair, BlockCypher)
3. **База данных** — для нагрузки замените SQLite на PostgreSQL
4. **Переменные окружения** — используйте `.env` файл вместо хардкода токена
5. **Вебхук** — для продакшена используйте webhook вместо polling

---

## 🌐 Поддерживаемые валюты

**Крипто:** BTC, ETH, USDT, BNB, SOL, TON, LTC, XRP  
**Фиат:** RUB, USD, EUR, UAH, KZT

Добавить новую валюту: `config.py` → `SUPPORTED_CRYPTO` / `COIN_IDS`
