import asyncio
import logging
import os
from typing import Any

import requests
from dotenv import load_dotenv

from config import DEEPL, MY_DEBUG
from src.services import LanguageService, NewsService, SummaryService


load_dotenv()
logger = logging.getLogger(__name__)


class Deepl:
    def __init__(self):
        self.auth_key = os.getenv('DEEPL_TOKEN')
        self.url = DEEPL['url']

    def get_languages(self) -> Any:
        """Receiving from the DEEPL API a list of possible languages for translation."""
        params = {'auth_key': self.auth_key}
        url = self.url + DEEPL['lang_endpoint']
        response = requests.get(url, params=params)
        return response.json()

    def create_languages(self) -> None:
        """Entry into a database of possible languages for translation."""
        try:
            LanguageService().create_many(self.get_languages())
        except Exception as e:
            logger.exception('in getting and recording languages to db:')
            raise e
        else:
            logger.info('Languages were received and recorded in the database!')

    async def translate(self, lang_code: str, text: str) -> str:
        """Translating text using DEEPL API."""
        await asyncio.sleep(5)
        params = {'auth_key': self.auth_key,
                  'target_lang': lang_code,
                  'text': text}
        url = self.url + DEEPL['transl_endpoint']
        response = requests.get(url, params=params)
        return response.json()['translations'][0]['text']


async def main(wait_translate: int, data: dict) -> None:
    """Identifying the languages used by readers and translating summary into these languages."""
    readers_languages = await LanguageService().get_readers_languages()
    if readers_languages:
        logger.debug('Trying to translate a summaries for newses...')
        await asyncio.sleep(wait_translate)
        news_pk = data['news_pk']
        summary_pk = data['summary_pk']
        summary_lang_pk = data['summary_lang']
        text = data['content']
        logger.debug(f'Trying to translate the summary with id {summary_pk}...')
        for language in readers_languages:
            lang_pk = language.pk
            lang_code = language.code
            if lang_pk == summary_lang_pk:
                continue
            try:
                if MY_DEBUG:
                    content = f'This is dummy translate to {lang_code}: {text}...'
                else:
                    content = await Deepl().translate(lang_code, text)
            except Exception:
                logger.exception(f'on translating <Summary> id {summary_pk} to {lang_code}:')
                continue
            else:
                await SummaryService().create(news_pk, lang_pk, content)
        await NewsService().update_news(news_pk, content=None, has_summary=True, has_summaries=True)
        logger.info(f'Translate of summaries completed for <News> id {news_pk}.')


if __name__ == '__main__':
    LANGUAGES = [
        {'language': 'DE', 'name': 'German'}, {'language': 'EN', 'name': 'English'},
        {'language': 'ES', 'name': 'Spanish'}, {'language': 'FR', 'name': 'French'},
        {'language': 'IT', 'name': 'Italian'}, {'language': 'RU', 'name': 'Russian'},
        {'language': 'TR', 'name': 'Turkish'}, {'language': 'UK', 'name': 'Ukrainian'}
    ]
    d = Deepl()
    # res = asyncio.run(d.translate('RU', 'book'))
    # print(res)
    LanguageService().create_many(LANGUAGES)
