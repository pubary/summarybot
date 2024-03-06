import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.exceptions import TelegramBadRequest
from aiogram.methods import DeleteWebhook
from dotenv import load_dotenv

from config import bot_text, MY_DEBUG
from src.bot.handlers import router

from src.services import ReaderSummaryService, NewsService


load_dotenv()
BOT_ADMIN_ID = os.getenv('BOT_ADMIN_ID')
logger = logging.getLogger(__name__)


async def start_bot(bot: Bot) -> None:
    """Information for the administrator about launching the bot"""
    await bot.send_message(BOT_ADMIN_ID, text='Бот запущен!')


async def stop_bot(bot: Bot) -> None:
    """Information for the administrator about stopping the bot"""
    await bot.send_message(BOT_ADMIN_ID, text='Бот остановлен!')


async def sending_msg(bot: Bot, wait_sending: int, amount: int, age: float) -> None:
    """The loop of checking messages prepared for sending and sending them to readers."""
    while True:
        logger.debug('Searching not-sent objects <ReaderSummary>...')
        await asyncio.sleep(wait_sending)
        update_list: list = []
        reader_summaries = await ReaderSummaryService().get_notsent_readersummary(amount=amount, age=age)
        if not any(reader_summaries):
            continue
        logger.info(f'Detected {len(reader_summaries)} not-sent objects <ReaderSummary>.')
        count: int = 0
        previous_news_pk: int = reader_summaries[0][2]
        news = await NewsService().get_news_data(previous_news_pk)
        for reader_summary in reader_summaries:
            if count > 30:
                await asyncio.sleep(1)
                count = 0
            news_pk = reader_summary[2]
            if previous_news_pk != news_pk:
                logger.info(f'Stop sending <ReaderSummary> from <News> id {previous_news_pk}')
                break
            reader_summary_pk = reader_summary[0]
            content = reader_summary[1]
            tg_id = reader_summary[3]
            news_url = news.url
            if news.day:
                news_day = news.day.strftime('%Y-%m-%d %H:%M')
            else:
                news_day = ''
            text = bot_text['sending_summary'].format(content, news_day, news_url)
            try:
                if MY_DEBUG:
                    logger.debug(f'This is dummy send <ReaderSummary> {reader_summary_pk} to <Reader> tg_id {tg_id}.')
                else:
                    await bot.send_message(tg_id, text=text, disable_web_page_preview=True)
            except TelegramBadRequest as e:
                await asyncio.sleep(2)
                logger.warning(f'TelegramBadRequest at sending object <ReaderSummary> id {reader_summary_pk}:\n{e}')
                update_list.append({'pk': reader_summary_pk, 'is_sent': True})
            except Exception:
                logger.exception(f'at sending object <ReaderSummary> id {reader_summary_pk}:')
                continue
            else:
                logger.debug(f'Sending object <ReaderSummary> id {reader_summary_pk} successfully')
                update_list.append({'pk': reader_summary_pk, 'is_sent': True})
            count += 1
            previous_news_pk = news_pk
        try:
            await ReaderSummaryService().update_many(update_list)
        except Exception:
            logger.exception(f'at update objects <ReaderSummary> for <News> id {previous_news_pk}:')
        else:
            logger.info(f'Objects <ReaderSummary> for <News> id {previous_news_pk} were sent and updated successfully.')


async def main(tasks: list, wait_sending: int, amount: int, age: float) -> None:
    """Creating a bot, assigning tasks to it, and starting it."""
    logging.basicConfig(level=os.getenv('LOG_LEVEL'), )
    bot = Bot(token=os.getenv('BOT_TOKEN'), parse_mode='HTML')
    if len(tasks):
        for task in tasks:
            asyncio.create_task(task)
    asyncio.create_task(sending_msg(bot, wait_sending, amount, age))
    loop = asyncio.get_event_loop()
    dp = Dispatcher(loop=loop)
    dp.include_router(router)
    # dp.startup.register(start_bot)
    # dp.shutdown.register(stop_bot)
    await bot(DeleteWebhook(drop_pending_updates=True))
    try:
        logger.info(f'Bot starting with {len(tasks)+1} tasks.')
        await dp.start_polling(bot)
    except Exception:
        logger.exception(f'on <start_polling(bot)>:')
    finally:
        await bot.session.close()


if __name__ == '__main__':
    # from src.summary import summary
    # asyncio.run(
    #     main(
    #         [summary(age=10, wait_searching=10, wait_create=2, wait_translate=1), ],
    #         wait_sending=15, amount=100, age=10),
    #     debug=MY_DEBUG
    # )
    asyncio.run(main([], wait_sending=3, amount=5, age=10), debug=MY_DEBUG)
