from typing import Union

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from ..services import LanguageService


async def lang_keyboard() -> Union[InlineKeyboardMarkup, ReplyKeyboardMarkup]:
    """Creating a keyboard for language selection."""
    languages_kb = InlineKeyboardBuilder()
    lang = LanguageService()
    codes = await lang.get_all_code()
    for code in codes:
        languages_kb.add(InlineKeyboardButton(text=code, callback_data=f'language_{code}'))
    return languages_kb.adjust(5).as_markup()
