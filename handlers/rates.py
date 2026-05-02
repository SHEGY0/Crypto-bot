from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from services import fetch_rates, format_rate_change

router = Router()


@router.message(F.text == "📊 Курсы валют")
async def show_rates(message: Message):
    await message.answer("⏳ Загружаю актуальные курсы...")
    try:
        rates = await fetch_rates()
        text = "📊 <b>Актуальные курсы криптовалют</b>\n"
        text += f"<i>Обновляется каждую минуту</i>\n\n"

        for symbol, data in rates.items():
            change_str = format_rate_change(data["change_24h"])
            text += (
                f"<b>{symbol}</b>\n"
                f"  💵 ${data['usd']:,.2f}  |  ₽{data['rub']:,.0f}  |  €{data['eur']:,.2f}\n"
                f"  24ч: {change_str}\n\n"
            )

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Обновить", callback_data="refresh_rates")]
        ])
        await message.answer(text, parse_mode="HTML", reply_markup=keyboard)
    except Exception as e:
        await message.answer("❌ Не удалось загрузить курсы. Попробуйте позже.")


@router.callback_query(F.data == "refresh_rates")
async def refresh_rates(callback: CallbackQuery):
    try:
        import time
        import services
        services._cache_ts = 0  # Force refresh

        rates = await fetch_rates()
        text = "📊 <b>Актуальные курсы криптовалют</b>\n"
        text += f"<i>Обновлено только что</i>\n\n"

        for symbol, data in rates.items():
            change_str = format_rate_change(data["change_24h"])
            text += (
                f"<b>{symbol}</b>\n"
                f"  💵 ${data['usd']:,.2f}  |  ₽{data['rub']:,.0f}  |  €{data['eur']:,.2f}\n"
                f"  24ч: {change_str}\n\n"
            )

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Обновить", callback_data="refresh_rates")]
        ])
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
        await callback.answer("✅ Курсы обновлены!")
    except Exception:
        await callback.answer("❌ Ошибка обновления", show_alert=True)
