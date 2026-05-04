"""
Запусти этот скрипт один раз чтобы добавить начальные отзывы:
python3 seed_reviews.py
"""
import asyncio
import aiosqlite
import random

DATABASE_PATH = "crypto_exchange.db"

FAKE_REVIEWS = [
    (4, "Все норм прошло, бот удобный, разобрался быстро."),
    (5, "Менял первый раз, переживал немного, но все ок."),
    (5, "Быстро ответили и помогли оформить заявку."),
    (4, "Удобно что все через тг, без лишней мороки."),
    (5, "Обмен сделали как обещали, вопросов нет."),
    (4, "Норм сервис, можно пользоваться."),
    (5, "Деньги получил, все четко."),
    (4, "Простой бот, ничего лишнего, удобно."),
    (5, "Уже не первый раз меняю тут, пока все устраивает."),
    (5, "Все прошло спокойно, без задержек."),
    (4, "Курс нормальный был, обмен занял не очень долго."),
    (4, "Обычный рабочий обменник, свою задачу делает."),
]

# Уникальные ID и номера агентов которые не попадутся реальным пользователям
FAKE_USERS = [
    (100000001, "3847"),
    (100000002, "5621"),
    (100000003, "2193"),
    (100000004, "7834"),
    (100000005, "4512"),
    (100000006, "9271"),
    (100000007, "6483"),
    (100000008, "1759"),
    (100000009, "8326"),
    (100000010, "4097"),
    (100000011, "7614"),
    (100000012, "2938"),
]

# Даты за последние 2 месяца
DATES = [
    "2026-03-05 14:22:00",
    "2026-03-11 09:45:00",
    "2026-03-18 16:30:00",
    "2026-03-24 11:15:00",
    "2026-03-29 18:44:00",
    "2026-04-03 10:20:00",
    "2026-04-08 13:55:00",
    "2026-04-14 08:30:00",
    "2026-04-19 15:10:00",
    "2026-04-25 17:40:00",
    "2026-04-30 12:05:00",
    "2026-05-03 20:15:00",
]


async def seed():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Создаём таблицу если нет
        await db.execute("""
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                agent_number TEXT DEFAULT '0000',
                rating INTEGER NOT NULL,
                text TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        try:
            await db.execute("ALTER TABLE reviews ADD COLUMN agent_number TEXT DEFAULT '0000'")
        except Exception:
            pass

        for i, (rating, text) in enumerate(FAKE_REVIEWS):
            user_id, agent_number = FAKE_USERS[i]
            date = DATES[i]
            await db.execute(
                "INSERT INTO reviews (user_id, agent_number, rating, text, status, created_at) VALUES (?, ?, ?, ?, 'approved', ?)",
                (user_id, agent_number, rating, text, date)
            )
            print(f"✅ Добавлен отзыв от 🥷 Агент #{agent_number}: {text[:40]}...")

        await db.commit()
        print("\n🎉 Все 12 отзывов добавлены!")


asyncio.run(seed())
