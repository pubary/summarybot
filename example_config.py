import os
from pathlib import Path
import logging.config


MY_DEBUG: bool = False

WAIT_FOR = {
    'delete_msg': 30,  # SECONDS - timeout before deleting bot answers to reader questions
    'pull_url': 1,  # HOURS - break between searching for new newses URL in the site XML-file <ONLY FROM: 1, 2, 3, 4>
    'searching': 300,  # SECONDS - break between searching for new newses in the database to create a first summary
    'create': 10,  # SECONDS - break between creating the first summaries for new newses from the list
    'translate': 5,  # SECONDS - break between translating summaries for newses from the list
    'sending': 150,  # SECONDS - break between searching for new summaries in the database and sending them
}

LEN_MAILING_LIST: int = 30000  # amount of objects pulled at one time from the database to the list for sending
NEWS_AGE: float = 1.5  # news older than this age in days will not be creating summary
SUMMARY_AGE: float = 1  # summary older than this age in days will not be sent

bot_text: dict = {
    'hello': 'Привет, <b>{}</b>!\nТеперь вы будете получать от бота краткие новости.\n'
             'Установленный язык: {}. Для изменения отправьте: /language',
    'hello_and_select': 'Привет, <b>{}</b>!\nТеперь вы будете получать от бота краткие новости.\n'
                        'Для продолжения выберите язык, отправив: /language',
    'help': 'Этот бот отправляет Вам краткие новости на выбранном вами языке. '
            'Для выбора языка отправьте:  /language',
    'language_selection': 'Выберите вариант ниже:',
    'language_selected': 'Выбран язык: <b>{}</b>',
    'sending_summary': '{}\n\n  <i>{}\n  {}</i>',
    'error': 'Возникла непредвиденная ошибка. Повторите попытку позднее.'
}

NEWS_SITES_LIST = [
    # xml-url, sites language, checking publication date by html body, recording html body into db
    ('https://cryptonews.com/news-sitemap.xml', 'EN', 'uncheck', 'not-record'),
    ('https://bits.media/bitrix-sitemap-iblock-7.xml', 'RU', 'uncheck', 'not-record'),
    ('https://crypto.ru/xml/posts-sitemap-0.xml', 'RU', 'check', 'record'),
]

BASE_DIR = Path(__file__).resolve().parent
DEEPL: dict = {'url': 'https://api-free.deepl.com/v2',
               'transl_endpoint': '/translate',
               'lang_endpoint': '/languages'}
KAGI: dict = {'url': 'https://kagi.com/api/v0',
              'engine': 'cecil',
              'summary_type': 'summary',
              'summary_endpoint': '/summarize'}
LOG_NAME: str = 'summarybot.log'
DB_NAME: str = 'summarybot.sqlite3'

if os.name == 'nt':
    DB_URL: str = f'sqlite+pysqlite:///' + str(Path(BASE_DIR, DB_NAME))
else:
    DB_URL: str = f'sqlite+pysqlite:////' + str(Path(BASE_DIR, DB_NAME))

LOGFILE = Path(BASE_DIR, LOG_NAME)

if MY_DEBUG:
    LOG_LEVEL: str = 'DEBUG'
    LOGGING_CONF = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {'simple': {'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'}},
        'handlers': {'console': {'class': 'logging.StreamHandler', 'formatter': 'simple', 'level': LOG_LEVEL}},
        'root': {'level': LOG_LEVEL, 'handlers': ['console']},
    }
else:
    LOG_LEVEL: str = 'INFO'
    LOGGING_CONF = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {'simple': {'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'}},
        'handlers': {'file_handler': {'class': 'logging.handlers.RotatingFileHandler',
                                      'level': LOG_LEVEL,
                                      'formatter': 'simple',
                                      'filename': LOGFILE,
                                      'encoding': 'utf8',
                                      'maxBytes': 1000000,
                                      'backupCount': 2,
                                      'mode': 'a'}},
        'root': {'level': LOG_LEVEL, 'handlers': ['file_handler']},
    }

logging.config.dictConfig(LOGGING_CONF)

HEADERS = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
    'cache-control': 'max-age=0',
    'if-modified-since': 'Thu, 07 Dec 2023 11:55:38 GMT',
    'if-none-match': 'W/\'6571b2ba-2abed\'',
    'sec-ch-ua': '\'Opera\';v=\'95\', \'Chromium\';v=\'109\', \'Not;A=Brand\';v=\'24\'',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '\'Windows\'',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36 OPR/95.0.0.0'
}
