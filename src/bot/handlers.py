import asyncio
import logging

from aiogram import Bot, Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, ChatMemberUpdatedFilter, KICKED, MEMBER
from aiogram.types import Message, ChatMemberUpdated, CallbackQuery

from config import bot_text, WAIT_FOR
from . import keyboards as kb
from ..services import ReaderService, LanguageService


router = Router()
rs = ReaderService()
logger = logging.getLogger(__name__)


async def delete_message(message: Message, sleep_time: int = WAIT_FOR['delete_msg']) -> None:
    """Deleting a message after the timeout expires."""
    await asyncio.sleep(sleep_time)
    if message:
        try:
            await message.delete()
        except TelegramBadRequest as e:
            if 'message to delete not found' in str(e):
                logger.debug('The message has already been deleted:', e)


async def error_msg(message: Message) -> None:
    """Sending a message about error."""
    msg = await message.edit_text(bot_text['error'])
    await delete_message(msg)


async def check_exist_and_activate(tg_user_id: int) -> (str, str):
    """Checking for the existence of a reader and creating or activating him. Returns the reader <pk> and <lang_code>"""
    pk, lang_code, is_active = await rs.is_exists(tg_user_id)
    if pk and not is_active:
        await rs.update(tg_user_id, is_active=True)
    elif pk and is_active:
        pass
    else:
        pk, lang_code = await rs.create(tg_user_id)
    return pk, lang_code


@router.message(Command('help'))
async def get_help(message: Message, bot: Bot) -> None:
    """Sending a response message to a reader command <help>."""
    msg = await message.answer(bot_text['help'])
    await delete_message(msg)


@router.callback_query(F.data.startswith('language_'))
async def select_languages(callback: CallbackQuery, bot: Bot) -> None:
    """Changing the reader's language after choosing it."""
    lang_code = callback.data.split('_')[1]
    message = callback.message
    try:
        await check_exist_and_activate(callback.from_user.id)
        await rs.set_language(callback.from_user.id, lang_code)
        language = await LanguageService().get_lang(lang_code)
        lang_name = language.name
    except Exception:
        logger.exception(f'in <select_languages()> for reader {callback.from_user.id}, lang_code {lang_code}:')
        await error_msg(message)
    else:
        msg = await message.edit_text(bot_text['language_selected'].format(lang_name))
        await delete_message(msg)


@router.message(Command('language'))
async def get_languages(message: Message, bot: Bot) -> None:
    """Sending a response message with the keyboard to a reader command <language>."""
    try:
        keyboard = await kb.lang_keyboard()
    except Exception:
        logger.exception(f'on <get_languages()> in <lang_keyboard()>:')
        await error_msg(message)
    else:
        msg = await message.answer(text=bot_text['language_selection'], reply_markup=keyboard)
        asyncio.create_task(delete_message(msg))


@router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=KICKED))
async def reader_blocked_bot(event: ChatMemberUpdated, bot: Bot) -> None:
    """Deactivating the reader after blocking the bot."""
    try:
        await rs.update(event.from_user.id, is_active=False)
    except Exception:
        logger.exception(f'on <reader_blocked_bot()> in <update({event.from_user.id})>:')


@router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=MEMBER))
async def reader_anblocked_bot(event: ChatMemberUpdated, bot: Bot) -> None:
    """Activating the reader after unlocking the bot."""
    try:
        await rs.update(event.from_user.id, is_active=True)
    except Exception:
        logger.exception(f'on <reader_anblocked_bot()> in <update({event.from_user.id})>:')


@router.message(Command('start'))
@router.message()
async def get_start(message: Message, bot: Bot) -> None:
    """Registering the reader and assigning a language to him after sending the command <start> to the bot."""
    reader_tg_id = message.from_user.id
    reader_name = message.from_user.first_name
    msg_lang_code = message.from_user.language_code.upper()
    try:
        pk, lang_code = await check_exist_and_activate(reader_tg_id)
        languages = await rs.language_service.get_all_code()
        if lang_code and (lang_code.upper() in languages):
            msg = await message.answer(bot_text['hello'].format(reader_name, lang_code.upper()))
        elif (not lang_code) and (msg_lang_code in languages):
            await ReaderService().set_language(reader_tg_id, msg_lang_code)
            msg = await message.answer(bot_text['hello'].format(reader_name, msg_lang_code))
        else:
            msg = await message.answer(bot_text['hello_and_select'].format(reader_name))
        asyncio.create_task(delete_message(msg))
    except Exception:
        logger.exception(f'in <get_start({reader_tg_id})>:')
        await error_msg(message)
