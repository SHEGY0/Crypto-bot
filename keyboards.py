from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton


def main_menu_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💱 Обменять"), KeyboardButton(text="📊 Курсы валют")],
            [KeyboardButton(text="📋 История"), KeyboardButton(text="👥 Рефералы")],
            [KeyboardButton(text="⭐️ Отзывы"), KeyboardButton(text="💬 Поддержка")],
            [KeyboardButton(text="👤 Профиль")],
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )


def crypto_select_keyboard(action: str):
    from config import SUPPORTED_CRYPTO
    buttons = []
    row = []
    for i, coin in enumerate(SUPPORTED_CRYPTO):
        row.append(InlineKeyboardButton(text=coin, callback_data=f"{action}:{coin}"))
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def fiat_select_keyboard(from_currency: str):
    from config import SUPPORTED_FIAT
    buttons = []
    row = []
    for fiat in SUPPORTED_FIAT:
        row.append(InlineKeyboardButton(text=fiat, callback_data=f"fiat_to:{from_currency}:{fiat}"))
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton(text="🔄 Крипто → Крипто", callback_data=f"crypto_to:{from_currency}")])
    buttons.append([InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def to_crypto_keyboard(from_currency: str):
    from config import SUPPORTED_CRYPTO
    buttons = []
    row = []
    for coin in SUPPORTED_CRYPTO:
        if coin != from_currency:
            row.append(InlineKeyboardButton(text=coin, callback_data=f"exchange_pair:{from_currency}:{coin}"))
            if len(row) == 3:
                buttons.append(row)
                row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data=f"from_crypto:{from_currency}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def confirm_exchange_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_exchange"),
            InlineKeyboardButton(text="❌ Отмена", callback_data="cancel"),
        ]
    ])


def back_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Главное меню", callback_data="main_menu")]
    ])
