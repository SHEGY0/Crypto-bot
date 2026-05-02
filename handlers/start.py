from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from database import get_or_create_user, get_user
from keyboards import main_menu_keyboard

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()

    # Check for referral code
    args = message.text.split()
    ref_code = args[1] if len(args) > 1 else None

    user = await get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username or "",
        full_name=message.from_user.full_name,
        referred_by_code=ref_code
    )

    welcome_text = (
        f"👋 Добро пожаловать в <b>CryptoSwap</b>, {message.from_user.first_name}!\n\n"
        f"🔐 Быстрый и безопасный обмен криптовалют\n"
        f"💸 Комиссия всего <b>1.5%</b>\n"
        f"⚡️ Обработка заявок за 5-30 минут\n\n"
        f"Выберите действие в меню ниже 👇"
    )

    await message.answer(welcome_text, parse_mode="HTML", reply_markup=main_menu_keyboard())


@router.message(F.text == "👤 Профиль")
async def show_profile(message: Message):
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("Пользователь не найден. Напишите /start")
        return

    text = (
        f"👤 <b>Ваш профиль</b>\n\n"
        f"🆔 ID: <code>{message.from_user.id}</code>\n"
        f"👤 Имя: {user['full_name']}\n"
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
