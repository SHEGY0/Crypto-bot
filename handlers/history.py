from aiogram import Router, F
from aiogram.types import Message

from database import get_user_transactions

router = Router()

STATUS_EMOJI = {
    "pending": "⏳",
    "processing": "🔄",
    "completed": "✅",
    "cancelled": "❌",
    "failed": "💔",
}


@router.message(F.text == "📋 История")
async def show_history(message: Message):
    transactions = await get_user_transactions(message.from_user.id, limit=10)

    if not transactions:
        await message.answer(
            "📋 <b>История транзакций</b>\n\n"
            "У вас пока нет транзакций.\n"
            "Нажмите «💱 Обменять», чтобы создать первую заявку!",
            parse_mode="HTML"
        )
        return

    text = "📋 <b>История транзакций</b> (последние 10)\n\n"

    for tx in transactions:
        emoji = STATUS_EMOJI.get(tx["status"], "❓")
        date = tx["created_at"][:16].replace("T", " ")
        text += (
            f"{emoji} <b>#{tx['id']}</b> | {date}\n"
            f"  {tx['from_amount']} {tx['from_currency']} → "
            f"{tx['to_amount']:.6f} {tx['to_currency']}\n"
            f"  Комиссия: ${tx['fee_usd']:.2f} | Статус: {tx['status']}\n\n"
        )

    await message.answer(text, parse_mode="HTML")
