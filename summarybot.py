import asyncio

from config import MY_DEBUG, NEWS_SITES_LIST, WAIT_FOR, LEN_MAILING_LIST, SUMMARY_AGE, NEWS_AGE
from src.bot import bot
from src.news import news
from src.summary import summary
from src.utils import first_launch_prepare


if __name__ == '__main__':
    first_launch_prepare()
    tasks = [summary(age=NEWS_AGE,
                     wait_searching=WAIT_FOR['searching'],
                     wait_create=WAIT_FOR['create'],
                     wait_translate=WAIT_FOR['translate']),
             news(sites_list=NEWS_SITES_LIST,
                  wait_pull_url=WAIT_FOR['pull_url'])]
    asyncio.run(bot(tasks=tasks,
                    wait_sending=WAIT_FOR['sending'],
                    amount=LEN_MAILING_LIST,
                    age=SUMMARY_AGE),
                debug=MY_DEBUG)
