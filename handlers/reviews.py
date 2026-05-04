from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import aiosqlite
from config import ADMIN_IDS, DATABASE_PATH
from database import get_user

router = Router()


class ReviewStates(StatesGroup):
    waiting_rating = State()
    waiting_text = State()


async def init_reviews_db():
    async with aiosqlite.connect(DATABASE_PATH) as db:
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
        await db.commit()


async def save_review(user_id: int, agent_number: str, rating: int, text: str):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "INSERT INTO reviews (user_id, agent_number, rating, text) VALUES (?, ?, ?, ?)",
            (user_id, agent_number, rating, text)
        )
        await db.commit()
        async with db.execute("SELECT last_insert_rowid()") as cur:
            row = await cur.fetchone()
        return row[0]


async def get_approved_reviews(limit: int = 10):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM reviews WHERE status='approved' ORDER BY created_at DESC LIMIT ?",
            (limit,)
        ) as cur:
            rows = await cur.fetchall()
        return [dict(r) for r in rows]


async def approve_review(review_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("UPDATE reviews SET status='approved' WHERE id=?", (review_id,))
        await db.commit()


async def reject_review(review_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("UPDATE reviews SET status='rejected' WHERE id=?", (review_id,))
        await db.commit()


async def get_review_stats():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(
            "SELECT COUNT(*), AVG(rating) FROM reviews WHERE status='approved'"
        ) as cur:
            row = await cur.fetchone()
        return {"count": row[0] or 0, "avg": row[1] or 0}


def rating_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⭐️ 1", callback_data="rate:1"),
            InlineKeyboardButton(text="⭐️ 2", callback_data="rate:2"),
            InlineKeyboardButton(text="⭐️ 3", callback_data="rate:3"),
            InlineKeyboardButton(text="⭐️ 4", callback_data="rate:4"),
            InlineKeyboardButton(text="⭐️ 5", callback_data="rate:5"),
        ],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_review")]
    ])


def moderation_keyboard(review_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Опубликовать", callback_data=f"approve_review:{review_id}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_review:{review_id}"),
        ]
    ])


@router.message(F.text == "⭐️ Отзывы")
async def show_reviews(message: Message):
    await init_reviews_db()
    reviews = await get_approved_reviews()
    stats = await get_review_stats()

    if not reviews:
        text = (
            "⭐️ <b>Отзывы клиентов</b>\n\n"
            "Пока отзывов нет. Будьте первым!\n\n"
            "Нажмите кнопку ниже чтобы оставить отзыв 👇"
        )
    else:
        stars = "⭐️" * round(stats["avg"])
        text = (
            f"⭐️ <b>Отзывы клиентов</b>\n"
            f"Средняя оценка: {stars} <b>{stats['avg']:.1f}</b> ({stats['count']} отзывов)\n\n"
        )
        for r in reviews:
            stars_str = "⭐️" * r["rating"]
            date = r["created_at"][:10]
            agent = r.get("agent_number", "0000")
            text += f"{stars_str} <b>🥷 Агент #{agent}</b>\n{r['text']}\n<i>{date}</i>\n\n"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✍️ Оставить отзыв", callback_data="write_review")]
    ])
    await message.answer(text, parse_mode="HTML", reply_markup=keyboard)


@router.callback_query(F.data == "write_review")
async def start_review(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ReviewStates.waiting_rating)
    await callback.message.answer(
        "✍️ <b>Оставить отзыв</b>\n\nСначала поставьте оценку нашему сервису:",
        parse_mode="HTML",
        reply_markup=rating_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("rate:"))
async def process_rating(callback: CallbackQuery, state: FSMContext):
    rating = int(callback.data.split(":")[1])
    await state.update_data(rating=rating)
    await state.set_state(ReviewStates.waiting_text)

    stars = "⭐️" * rating
    await callback.message.edit_text(
        f"Ваша оценка: {stars}\n\n"
        f"✍️ Теперь напишите ваш отзыв:\n"
        f"<i>Расскажите о вашем опыте работы с нами</i>",
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "cancel_review")
async def cancel_review(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Отзыв отменён.")
    await callback.answer()


@router.message(ReviewStates.waiting_text)
async def process_review_text(message: Message, state: FSMContext):
    text = message.text.strip()

    if len(text) < 5:
        await message.answer("❌ Отзыв слишком короткий. Напишите подробнее.")
        return
    if len(text) > 500:
        await message.answer("❌ Отзыв слишком длинный. Максимум 500 символов.")
        return

    data = await state.get_data()
    rating = data["rating"]
    await state.clear()

    # Получаем номер агента
    user = await get_user(message.from_user.id)
    agent_number = user.get("agent_number", "0000") if user else "0000"

    review_id = await save_review(message.from_user.id, agent_number, rating, text)
    stars = "⭐️" * rating

    try:
        for admin_id in ADMIN_IDS:
            await message.bot.send_message(
                admin_id,
                f"📝 <b>Новый отзыв на модерацию!</b>\n\n"
                f"🥷 Агент #{agent_number}\n"
                f"Оценка: {stars} ({rating}/5)\n"
                f"Текст: {text}\n\n"
                f"Опубликовать?",
                parse_mode="HTML",
                reply_markup=moderation_keyboard(review_id)
            )
    except Exception:
        pass

    await message.answer(
        f"✅ <b>Спасибо за отзыв, 🥷 Агент #{agent_number}!</b>\n\n"
        f"{stars}\n{text}\n\n"
        f"<i>Отзыв отправлен на модерацию и будет опубликован в ближайшее время.</i>",
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("approve_review:"))
async def approve_review_cb(callback: CallbackQuery):
    review_id = int(callback.data.split(":")[1])
    await approve_review(review_id)
    await callback.message.edit_text(
        callback.message.text + "\n\n✅ <b>Опубликован!</b>",
        parse_mode="HTML"
    )
    await callback.answer("✅ Отзыв опубликован!")


@router.callback_query(F.data.startswith("reject_review:"))
async def reject_review_cb(callback: CallbackQuery):
    review_id = int(callback.data.split(":")[1])
    await reject_review(review_id)
    await callback.message.edit_text(
        callback.message.text + "\n\n❌ <b>Отклонён.</b>",
        parse_mode="HTML"
    )
    await callback.answer("❌ Отзыв отклонён.")
