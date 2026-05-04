from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from database import get_or_create_user, get_user
from keyboards import main_menu_keyboard

router = Router()


def welcome_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💱 Начать обмен", callback_data="go_exchange")],
        [InlineKeyboardButton(text="⭐️ Отзывы клиентов", callback_data="go_reviews")],
    ])


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()

    args = message.text.split()
    ref_code = args[1] if len(args) > 1 else None

    user = await get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username or "",
        full_name=message.from_user.full_name,
        referred_by_code=ref_code
    )

    agent_number = user.get("agent_number", "0000")
    agent_tag = f"🥷 Агент #{agent_number}"
    is_new = user.get("total_exchanged_usd", 0) == 0

    if is_new:
        welcome_text = (
            f"👋 Добро пожаловать, <b>{agent_tag}</b>!\n\n"
            f"💎 <b>TetherSell</b> — быстрый и надёжный крипто обменник\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"⚡️ <b>Почему выбирают нас:</b>\n\n"
            f"🔒 Полная анонимность — никаких KYC\n"
            f"💸 Комиссия всего <b>1.5%</b> — одна из лучших на рынке\n"
            f"⏱ Выплата за <b>5-30 минут</b> после подтверждения\n"
            f"🌍 Работаем <b>24/7</b> без выходных\n"
            f"🛡 Более <b>500+ успешных обменов</b>\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"💱 <b>Что мы обмениваем:</b>\n"
            f"USDT · BTC · ETH · BNB · SOL · TON\n"
            f"→ Рубли (СБП), USD, EUR и другие\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"👇 Выберите действие:"
        )
        await message.answer(welcome_text, parse_mode="HTML", reply_markup=main_menu_keyboard())
        await message.answer("🚀 Готовы начать? Нажмите кнопку:", reply_markup=welcome_keyboard())
    else:
        await message.answer(
            f"👋 С возвращением, <b>{agent_tag}</b>!\n\n"
            f"Выберите действие в меню 👇",
            parse_mode="HTML",
            reply_markup=main_menu_keyboard()
        )


@router.callback_query(F.data == "go_exchange")
async def go_exchange(callback: CallbackQuery):
    await callback.message.answer(
        "💱 Нажмите кнопку <b>«💱 Обменять»</b> в меню ниже 👇",
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "go_reviews")
async def go_reviews(callback: CallbackQuery):
    await callback.message.answer(
        "⭐️ Нажмите кнопку <b>«⭐️ Отзывы»</b> в меню ниже 👇",
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(F.text == "👤 Профиль")
async def show_profile(message: Message):
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("Пользователь не найден. Напишите /start")
        return

    agent_number = user.get("agent_number", "0000")

    text = (
        f"🥷 <b>Агент #{agent_number}</b>\n\n"
        f"🆔 ID: <code>{message.from_user.id}</code>\n"
        f"💰 Всего обменяно: <b>${user['total_exchanged_usd']:.2f}</b>\n"
        f"🎁 Реферальный бонус: <b>${user['bonus_balance']:.2f}</b>\n"
        f"🔗 Реф. код: <code>{user['referral_code']}</code>\n"
        f"📅 Регистрация: {user['created_at'][:10]}"
    )
    await message.answer(text, parse_mode="HTML")


@router.callback_query(F.data == "main_menu")
async def back_to_main(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer("🏠 Главное меню", reply_markup=main_menu_keyboard())
    await callback.answer()


@router.callback_query(F.data == "cancel")
async def cancel_action(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Действие отменено")
    await callback.message.answer("🏠 Главное меню", reply_markup=main_menu_keyboard())
    await callback.answer()
