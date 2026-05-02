import aiosqlite
from config import DATABASE_PATH
from datetime import datetime


async def init_db():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                telegram_id INTEGER UNIQUE NOT NULL,
                username TEXT,
                full_name TEXT,
                referral_code TEXT UNIQUE,
                referred_by INTEGER,
                total_exchanged_usd REAL DEFAULT 0,
                bonus_balance REAL DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                from_currency TEXT NOT NULL,
                to_currency TEXT NOT NULL,
                from_amount REAL NOT NULL,
                to_amount REAL NOT NULL,
                rate REAL NOT NULL,
                fee_usd REAL NOT NULL,
                status TEXT DEFAULT 'pending',
                wallet_address TEXT,
                tx_hash TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS support_tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                message TEXT NOT NULL,
                status TEXT DEFAULT 'open',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()


async def get_or_create_user(telegram_id: int, username: str, full_name: str, referred_by_code: str = None):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)) as cursor:
            user = await cursor.fetchone()

        if user:
            return dict(user)

        # Generate referral code
        import hashlib
        ref_code = hashlib.md5(str(telegram_id).encode()).hexdigest()[:8].upper()

        referred_by_id = None
        if referred_by_code:
            async with db.execute("SELECT id FROM users WHERE referral_code = ?", (referred_by_code,)) as cur:
                referrer = await cur.fetchone()
                if referrer:
                    referred_by_id = referrer["id"]

        await db.execute(
            "INSERT INTO users (telegram_id, username, full_name, referral_code, referred_by) VALUES (?, ?, ?, ?, ?)",
            (telegram_id, username, full_name, ref_code, referred_by_id)
        )
        await db.commit()

        async with db.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)) as cursor:
            user = await cursor.fetchone()
        return dict(user)


async def get_user(telegram_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)) as cursor:
            user = await cursor.fetchone()
        return dict(user) if user else None


async def create_transaction(user_id: int, from_currency: str, to_currency: str,
                              from_amount: float, to_amount: float, rate: float,
                              fee_usd: float, wallet_address: str):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            """INSERT INTO transactions 
               (user_id, from_currency, to_currency, from_amount, to_amount, rate, fee_usd, wallet_address)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (user_id, from_currency, to_currency, from_amount, to_amount, rate, fee_usd, wallet_address)
        )
        await db.execute(
            "UPDATE users SET total_exchanged_usd = total_exchanged_usd + ? WHERE id = ?",
            (from_amount * rate if from_currency != "USDT" else from_amount, user_id)
        )
        await db.commit()


async def get_user_transactions(telegram_id: int, limit: int = 10):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """SELECT t.* FROM transactions t
               JOIN users u ON t.user_id = u.id
               WHERE u.telegram_id = ?
               ORDER BY t.created_at DESC LIMIT ?""",
            (telegram_id, limit)
        ) as cursor:
            rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def get_referral_stats(telegram_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT id, referral_code, bonus_balance FROM users WHERE telegram_id = ?", (telegram_id,)) as cur:
            user = await cur.fetchone()
        if not user:
            return None
        async with db.execute("SELECT COUNT(*) as cnt FROM users WHERE referred_by = ?", (user["id"],)) as cur:
            ref_count = await cur.fetchone()
        return {
            "referral_code": user["referral_code"],
            "bonus_balance": user["bonus_balance"],
            "referral_count": ref_count["cnt"]
        }


async def save_support_ticket(telegram_id: int, message: str):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        user = await get_user(telegram_id)
        if user:
            await db.execute(
                "INSERT INTO support_tickets (user_id, message) VALUES (?, ?)",
                (user["id"], message)
            )
            await db.commit()
