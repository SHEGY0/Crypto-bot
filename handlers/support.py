from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import save_support_ticket
from keyboards import main_menu_keyboard
from config import ADMIN_IDS

router = Router()


class SupportStates(StatesGroup):
    waiting_for_message = State()


@router.message(F.text == "💬 Поддержка")
async def start_support(message: Message, state: FSMContext):
    await state.set_state(SupportStates.waiting_for_message)
    await message.answer(
        "💬 <b>Служба поддержки</b>\n\n"
        "Опишите вашу проблему или вопрос.\n"
        "Мы ответим в течение 15-60 минут.\n\n"
        "✍️ Напишите ваше сообщение:",
        parse_mode="HTML"
    )


@router.message(SupportStates.waiting_for_message)
async def process_support_message(message: Message, state: FSMContext):
    user_message = message.text

    await save_support_ticket(message.from_user.id, user_message)

    # Forward to admins
    try:
        for admin_id in ADMIN_IDS:
            await message.bot.send_message(
                admin_id,
                f"📩 <b>Новый тикет поддержки</b>\n\n"
                f"👤 От: @{message.from_user.username} (ID: <code>{message.from_user.id}</code>)\n"
                f"📝 Сообщение:\n{user_message}",
                parse_mode="HTML"
            )
    except Exception:
        pass

    await state.clear()
    await message.answer(
        "✅ <b>Сообщение отправлено!</b>\n\n"
        "Наш менеджер ответит вам в ближайшее время.\n"
        "Обычно это занимает 15-60 минут.",
        parse_mode="HTML",
        reply_markup=main_menu_keyboard()
    )
