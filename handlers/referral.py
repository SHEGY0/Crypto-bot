from aiogram import Router, F
from aiogram.types import Message
from aiogram.utils.deep_linking import create_start_link

from database import get_referral_stats
from config import REFERRAL_BONUS_PERCENT

router = Router()


@router.message(F.text == "👥 Рефералы")
async def show_referrals(message: Message):
    stats = await get_referral_stats(message.from_user.id)

    if not stats:
        await message.answer("Ошибка загрузки. Напишите /start")
        return

    bot = message.bot
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={stats['referral_code']}"

    text = (
        f"👥 <b>Реферальная программа</b>\n\n"
        f"🎁 Вы получаете <b>{REFERRAL_BONUS_PERCENT}%</b> от нашей комиссии\n"
        f"за каждый обмен ваших рефералов!\n\n"
        f"📊 <b>Ваша статистика:</b>\n"
        f"👤 Приглашено: <b>{stats['referral_count']}</b> чел.\n"
        f"💰 Заработано: <b>${stats['bonus_balance']:.2f}</b>\n\n"
        f"🔗 <b>Ваша реферальная ссылка:</b>\n"
        f"<code>{ref_link}</code>\n\n"
        f"📤 Поделитесь ссылкой с друзьями — и начните зарабатывать!"
    )

    await message.answer(text, parse_mode="HTML")
