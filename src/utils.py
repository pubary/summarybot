import logging
from time import sleep

from config import NEWS_SITES_LIST
from src.database import create_db
from src.deepl import Deepl
from src.news import pull_urls
from src.services import LanguageService, NewsService


logger = logging.getLogger(__name__)


def first_launch_prepare() -> None:
    """Creating a database and populating it when you first launch the application."""
    try:
        if not LanguageService().exist_lang('en'):
            create_db()
            sleep(1)
            Deepl().create_languages()
        sleep(1)
        if not any(NewsService().get_all_url()):
            pull_urls(NEWS_SITES_LIST, check_date=False)
    except Exception as e:
        logger.exception('on prepare to launch the application:\n', e)
