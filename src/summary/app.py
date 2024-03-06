import asyncio
import logging
import os

import requests
from dotenv import load_dotenv

from config import KAGI, MY_DEBUG
from src.deepl import deepl
from src.services import NewsService, SummaryService


load_dotenv()
logger = logging.getLogger(__name__)


class Summary:
    def __init__(self):
        self.auth_key = os.getenv('KAGI_TOKEN')
        self.url = KAGI['url']

    async def get_summary(self, link: str, language: str, wait_summary: int) -> str:
        """Creating summary text using KAGI API."""
        await asyncio.sleep(wait_summary)
        url = self.url + KAGI['summary_endpoint']
        params = {'url': link,
                  'summary_type': KAGI['summary_type'],
                  'engine': KAGI['engine'],
                  'target_language': language}
        headers = {'Authorization': f'Bot {self.auth_key}'}
        try:
            response = requests.get(url, headers=headers, params=params)
        except Exception as e:
            logger.exception(f'Error in <def get_summary({link})>:')
            raise e
        else:
            length = response.headers.get('Content-Length', 'not_exist')
            if response.status_code == 200\
                    and response.headers['Content-Type'] == 'application/json'\
                    and length != '0':
                res = response.json()
                meta = res.get('meta')
                api_balance = meta.get('api_balance')
                data = res.get('data')
                content = data.get('output')
                if api_balance < 1:
                    logger.warning(f'Attention: the need to top up your API credits is approaching!'
                                   f' Currently on account {api_balance} credits.')
                return content


async def main(age: float, wait_searching: int, wait_create: int, wait_translate: int) -> None:
    """The main loop of searching news without summaries in the database and creating summaries for them."""
    while True:
        await asyncio.sleep(wait_searching)
        logger.debug('Trying to create a first summary for newses...')
        try:
            newses = await NewsService().get_many_news_data(age=age, has_summary=False, has_summaries=False)
        except Exception:
            logger.exception('Unable to retrieve data for objects <News> from db.')
            continue
        if not any(newses):
            continue
        for news in newses:
            logger.debug(f'Detected new object <News> id {news.pk} without first summary.')
            try:
                if MY_DEBUG:
                    content = f'Dummy {news.lang_code} summary from {news.url}.'
                else:
                    content = await Summary().get_summary(news.url, news.lang_code, wait_create)
                if not content:
                    logger.warning(f'Summary for <News> id {news.pk} was not getting.'
                                   f' There may not be enough credits in your KAGI account.')
                    continue
                summary_pk = await SummaryService().create(news.pk, news.lang_pk, content)
                await NewsService().update_news(news.pk, content=None, has_summary=True, has_summaries=False)
            except Exception:
                logger.exception(f'No summary was get or create for <News> id {news.pk}')
                continue
            else:
                logger.info(f'The first summary for <News> id {news.pk} on {news.lang_code} has been created.')
                data = {'news_pk': news.pk, 'summary_pk': summary_pk, 'summary_lang': news.lang_pk, 'content': content}
                asyncio.create_task(deepl(wait_translate, data))


if __name__ == '__main__':
    # asyncio.run(main(age=10, wait_searching=5, wait_create=1, wait_translate=1))
    li = 'https://bits.media/birzha-coinbase-i-coinbase-asset-management-zapustili-platformu-dolgovykh-instrumentov/'
    print(asyncio.run(Summary().get_summary(li, 'RU', 1)))
