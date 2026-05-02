from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from services import fetch_rates, get_exchange_rate
from keyboards import (crypto_select_keyboard, fiat_select_keyboard,
                        to_crypto_keyboard, confirm_exchange_keyboard, main_menu_keyboard)
from database import get_user, create_transaction
from config import EXCHANGE_FEE_PERCENT, MIN_EXCHANGE_USD, MAX_EXCHANGE_USD, ADMIN_IDS

router = Router()


class ExchangeStates(StatesGroup):
    choosing_from = State()
    choosing_to = State()
    entering_amount = State()
    entering_wallet = State()
    confirming = State()


@router.message(F.text == "💱 Обменять")
async def start_exchange(message: Message, state: FSMContext):
    await state.set_state(ExchangeStates.choosing_from)
    await message.answer(
        "💱 <b>Обмен криптовалюты</b>\n\n"
        "Выберите <b>отдаваемую</b> валюту:",
        parse_mode="HTML",
        reply_markup=crypto_select_keyboard("from_crypto")
    )


@router.callback_query(F.data.startswith("from_crypto:"))
async def choose_from_crypto(callback: CallbackQuery, state: FSMContext):
    from_currency = callback.data.split(":")[1]
    await state.update_data(from_currency=from_currency)
    await state.set_state(ExchangeStates.choosing_to)

    await callback.message.edit_text(
        f"✅ Отдаёте: <b>{from_currency}</b>\n\n"
        f"Выберите <b>получаемую</b> валюту:",
        parse_mode="HTML",
        reply_markup=fiat_select_keyboard(from_currency)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("fiat_to:"))
async def choose_fiat_to(callback: CallbackQuery, state: FSMContext):
    _, from_currency, to_currency = callback.data.split(":")
    await state.update_data(to_currency=to_currency)
    await state.set_state(ExchangeStates.entering_amount)

    try:
        rate = await get_exchange_rate(from_currency, to_currency)
        await callback.message.edit_text(
            f"💱 <b>{from_currency} → {to_currency}</b>\n"
            f"📈 Курс: 1 {from_currency} ≈ {rate:,.4f} {to_currency}\n"
            f"💸 Комиссия: {EXCHANGE_FEE_PERCENT}%\n\n"
            f"Введите сумму в <b>{from_currency}</b>:\n"
            f"<i>Минимум: ${MIN_EXCHANGE_USD} | Максимум: ${MAX_EXCHANGE_USD:,.0f}</i>",
            parse_mode="HTML"
        )
    except Exception:
        await callback.message.edit_text(
            f"💱 <b>{from_currency} → {to_currency}</b>\n\n"
            f"Введите сумму в <b>{from_currency}</b>:",
            parse_mode="HTML"
        )
    await callback.answer()


@router.callback_query(F.data.startswith("crypto_to:"))
async def choose_crypto_to(callback: CallbackQuery, state: FSMContext):
    from_currency = callback.data.split(":")[1]
    await callback.message.edit_text(
        f"✅ Отдаёте: <b>{from_currency}</b>\n\n"
        f"Выберите <b>получаемую</b> криптовалюту:",
        parse_mode="HTML",
        reply_markup=to_crypto_keyboard(from_currency)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("exchange_pair:"))
async def choose_crypto_pair(callback: CallbackQuery, state: FSMContext):
    _, from_currency, to_currency = callback.data.split(":")
    await state.update_data(from_currency=from_currency, to_currency=to_currency)
    await state.set_state(ExchangeStates.entering_amount)

    try:
        rate = await get_exchange_rate(from_currency, to_currency)
        await callback.message.edit_text(
            f"💱 <b>{from_currency} → {to_currency}</b>\n"
            f"📈 Курс: 1 {from_currency} ≈ {rate:.6f} {to_currency}\n"
            f"💸 Комиссия: {EXCHANGE_FEE_PERCENT}%\n\n"
            f"Введите сумму в <b>{from_currency}</b>:",
            parse_mode="HTML"
        )
    except Exception:
        await callback.message.edit_text(
            f"💱 <b>{from_currency} → {to_currency}</b>\n\nВведите сумму в <b>{from_currency}</b>:",
            parse_mode="HTML"
        )
    await callback.answer()


@router.message(ExchangeStates.entering_amount)
async def process_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text.replace(",", "."))
        if amount <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Введите корректное число, например: <code>0.5</code>", parse_mode="HTML")
        return

    data = await state.get_data()
    from_currency = data["from_currency"]
    to_currency = data["to_currency"]

    try:
        rate = await get_exchange_rate(from_currency, to_currency)
        usd_rate = await get_exchange_rate(from_currency, "USD") if from_currency != "USD" else 1.0
        amount_usd = amount * usd_rate

        if amount_usd < MIN_EXCHANGE_USD:
            await message.answer(f"❌ Минимальная сумма: ${MIN_EXCHANGE_USD}")
            return
        if amount_usd > MAX_EXCHANGE_USD:
            await message.answer(f"❌ Максимальная сумма: ${MAX_EXCHANGE_USD:,.0f}")
            return

        fee_percent = EXCHANGE_FEE_PERCENT / 100
        fee_usd = amount_usd * fee_percent
        to_amount = amount * rate * (1 - fee_percent)

        await state.update_data(
            amount=amount,
            to_amount=to_amount,
            rate=rate,
            fee_usd=fee_usd,
            amount_usd=amount_usd
        )
        await state.set_state(ExchangeStates.entering_wallet)

        await message.answer(
            f"📝 <b>Детали обмена:</b>\n\n"
            f"▶️ Отдаёте: <b>{amount} {from_currency}</b>\n"
            f"◀️ Получаете: <b>{to_amount:.6f} {to_currency}</b>\n"
            f"📈 Курс: 1 {from_currency} = {rate:.6f} {to_currency}\n"
            f"💸 Комиссия: ${fee_usd:.2f} ({EXCHANGE_FEE_PERCENT}%)\n\n"
            f"📬 Введите адрес кошелька для получения <b>{to_currency}</b>:",
            parse_mode="HTML"
        )
    except Exception as e:
        await message.answer("❌ Ошибка получения курса. Попробуйте позже.")


@router.message(ExchangeStates.entering_wallet)
async def process_wallet(message: Message, state: FSMContext):
    wallet = message.text.strip()

    if len(wallet) < 10:
        await message.answer("❌ Некорректный адрес кошелька. Попробуйте снова.")
        return

    await state.update_data(wallet=wallet)
    await state.set_state(ExchangeStates.confirming)

    data = await state.get_data()
    from_currency = data["from_currency"]
    to_currency = data["to_currency"]
    amount = data["amount"]
    to_amount = data["to_amount"]
    fee_usd = data["fee_usd"]

    await message.answer(
        f"✅ <b>Подтвердите заявку:</b>\n\n"
        f"▶️ Отдаёте: <b>{amount} {from_currency}</b>\n"
        f"◀️ Получаете: <b>{to_amount:.6f} {to_currency}</b>\n"
        f"💸 Комиссия: ${fee_usd:.2f}\n"
        f"📬 Кошелёк: <code>{wallet}</code>\n\n"
        f"⚠️ После подтверждения, отправьте средства на наш кошелёк.\n"
        f"Менеджер свяжется с вами в течение 5-30 минут.",
        parse_mode="HTML",
        reply_markup=confirm_exchange_keyboard()
    )


@router.callback_query(F.data == "confirm_exchange")
async def confirm_exchange(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user = await get_user(callback.from_user.id)

    if not user:
        await callback.answer("Ошибка: пользователь не найден", show_alert=True)
        return

    from_currency = data["from_currency"]
    to_currency = data["to_currency"]
    amount = data["amount"]
    to_amount = data["to_amount"]
    rate = data["rate"]
    fee_usd = data["fee_usd"]
    wallet = data["wallet"]

    await create_transaction(
        user_id=user["id"],
        from_currency=from_currency,
        to_currency=to_currency,
        from_amount=amount,
        to_amount=to_amount,
        rate=rate,
        fee_usd=fee_usd,
        wallet_address=wallet
    )

    await state.clear()

    # Notify admin
    try:
        from aiogram import Bot
        bot = callback.bot
        for admin_id in ADMIN_IDS:
            await bot.send_message(
                admin_id,
                f"🔔 <b>Новая заявка на обмен!</b>\n\n"
                f"👤 Пользователь: @{callback.from_user.username} (ID: {callback.from_user.id})\n"
                f"▶️ Отдаёт: {amount} {from_currency}\n"
                f"◀️ Получает: {to_amount:.6f} {to_currency}\n"
                f"📬 Кошелёк: <code>{wallet}</code>\n"
                f"💸 Комиссия: ${fee_usd:.2f}",
                parse_mode="HTML"
            )
    except Exception:
        pass

    await callback.message.edit_text(
        f"✅ <b>Заявка создана!</b>\n\n"
        f"📋 Детали:\n"
        f"▶️ {amount} {from_currency} → {to_amount:.6f} {to_currency}\n"
        f"📬 Получатель: <code>{wallet}</code>\n\n"
        f"📌 <b>Следующий шаг:</b>\n"
        f"Отправьте <b>{amount} {from_currency}</b> на наш кошелёк:\n"
        f"<code>bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh</code>\n\n"
        f"⏱ Менеджер обработает заявку в течение 5-30 минут.\n"
        f"По вопросам: нажмите «💬 Поддержка»",
        parse_mode="HTML",
        reply_markup=main_menu_keyboard()
    )
    await callback.answer("✅ Заявка создана!")
