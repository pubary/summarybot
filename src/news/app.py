import asyncio
import datetime
import logging

import pytz
from time import sleep

import requests

from bs4 import BeautifulSoup

from config import NEWS_AGE, HEADERS
from src.database import Session
from src.services import NewsService


logger = logging.getLogger(__name__)


def connect_day_to_url(last_urls: set, url_and_date: list) -> set:
    """Attaching a date to those URLs that were selected because they were not in the database.
    This action is performed for those URLs for which the correct date is recorded in the XML-file."""
    res = set()
    for last_url in last_urls:
        for u_d in url_and_date:
            if u_d[0] == last_url:
                res.add(u_d)
    return res


def get_data(session: Session, urls_data: set, recording: str = 'not-recording') -> (list, list):
    """Receiving and Splitting data depending on the date of news from the URL
    and recording the news HTML into the database if this is enabled.
    If the input data does not contain a date, then it is extracted from the content."""
    new_url_data = list()
    old_url_data = list()
    for data in urls_data:
        if isinstance(data, tuple):
            url = data[0]
            day = data[1]
        else:
            url = data
            day = None
        try:
            response = session.get(url, timeout=(10, 5))
        except Exception:
            logger.exception(f'on get response from <{url}> in <def get_data()>:')
            continue
        else:
            if response.status_code == 200:
                try:
                    text = response.text
                    if not day:
                        day = parse_date(text)
                    else:
                        try:
                            day = datetime.datetime.strptime(day, '%Y-%m-%dT%H:%M:%S%z')
                        except:
                            day = None
                    if recording == 'not-record':
                        text = ''
                    if day and 24*60*60*NEWS_AGE >= (datetime.datetime.now(pytz.UTC) - day).total_seconds():
                        new_url_data.append({'url': url, 'day': day, 'content': text})
                    else:
                        old_url_data.append({'url': url, 'day': day, 'content': ''})
                except Exception:
                    logger.exception(f'on <def parse_date()> for <{url}> in <def get_data()>:')
                    continue
    new_url_data.sort(key=lambda x: x.get('day') if x.get('day') else datetime.datetime.strptime('1970', '%Y'))
    return new_url_data, old_url_data


def get_requests_session() -> requests.sessions:
    """Receiving and updating a session for requests"""
    session = requests.Session()
    session.headers.update(HEADERS)
    return session


def parser(xml_url: str, language: str, session: requests.sessions) -> (list, str):
    """Finding news link and news date from network XML-file. Forming a list from this data. If applications are blocked
    from accessing network XML-file, then news data is retrieved from a local file with the same name."""
    try:
        response = session.get(xml_url, timeout=(10, 1))
        if response.status_code == 200:
            data_list = list()
            soup = BeautifulSoup(response.text, features='xml')
            if 'robots' in str(soup.find('meta')):
                logger.warning(f'File {xml_url} is not available for URL robot extraction.')
                from_file = soup_from_file(xml_url)
                if from_file:
                    soup = from_file
            for link in soup.find_all('url'):
                url = link.find('loc')
                if url:
                    date = link.find('lastmod')
                    if not date:
                        date = link.find('news:publication_date')
                    if date:
                        date = date.text
                    else:
                        date = '1970-01-01T00:00:00+00:00'
                    data_list.append((url.text.lower(), date))
            return data_list, language
    except requests.exceptions.ConnectionError as e:
        logger.exception(f'in <def parser({xml_url}, {language})>:')
        raise e


def parse_date(text: str) -> datetime:
    """Finding the publication news date in news text."""
    soup = BeautifulSoup(text, 'lxml')
    date = soup.find_all('span', class_='page__meta-item-text')
    if not date:
        return False
    date_time = datetime.datetime.strptime(f'{date[0].text} +0300', '%d.%m.%Y %z')
    return date_time


def pull_url(site_info: tuple, session: requests.sessions, check_date: bool) -> bool:
    """Retrieving news links from one XML-file and writing them to the database.
    Links that are not in the database are selected.
    The date of the news is compared with the configured age and,
    depending on the result, the news data is written to the data database in different ways.
    If the link is received from XML-file labeled "check", then for comparison with age, the date is taken,
    which is extracted from the text of the news.
    Comparison of news date with age is not performed when the application is launched for the first time."""
    if not session:
        session = get_requests_session()
    xml_url = site_info[0].lower()
    lang_code = site_info[1].upper()
    url_and_date, language = parser(xml_url, lang_code, session)
    urls = set(map(lambda x: x[0], url_and_date))
    all_url = set(NewsService().get_all_url())
    last_urls = urls.difference(all_url)
    logger.info(f'Detected {len(last_urls)} new in {len(urls)} url from {xml_url}.')
    if not any(last_urls):
        return False
    if site_info[2] == 'check' and check_date:
        new_data, old_data = get_data(session, last_urls, site_info[3])
        logger.info(f'Check date successful for {len(new_data)} new in {len(last_urls)} url from {xml_url}.')
    elif site_info[2] != 'check' and check_date:
        new_data, old_data = get_data(session, connect_day_to_url(last_urls, url_and_date), site_info[3])
        session.close()
        logger.info(f'Check date successful for {len(new_data)} new in {len(last_urls)} url from {xml_url}.')
    else:
        new_data, old_data = list(), list(map(lambda x: {'url': x}, last_urls))
    try:
        if any(new_data):
            NewsService().create_many(new_data, lang_code, has_summary=False, has_summaries=False)
        if any(old_data):
            NewsService().create_many(old_data, lang_code, has_summary=True, has_summaries=True)
    except Exception as e:
        raise e
    else:
        logger.info(f'News url from {xml_url} added to database')
        return True


def pull_urls(sites_info: list, check_date: bool = True) -> None:
    """Sequentially obtaining links to news from list of XML-file and writing them to the database.
    For XML files marked CHECK, the session is used several times to receive links."""
    session = get_requests_session()
    for site_info in sites_info:
        logger.debug(f'Pull URLs from {site_info[0]} has started')
        sleep(1)
        if site_info[2] == 'check':
            sess = session
        else:
            sess = False
        try:
            pull_url(site_info, sess, check_date)
        except Exception:
            logger.exception(f'in <def pull_url()>. News url from {site_info[0]} not added to database:')
            continue
    session.close()


def soup_from_file(url: str) -> BeautifulSoup or bool:
    """Getting BS-instance from a local XML-file to extract news data."""
    from pathlib import Path
    from config import BASE_DIR
    file_name = url.split('/')[-1]
    try:
        with open(Path(BASE_DIR, 'xml', file_name), encoding='utf-8', mode='r') as p:
            response_text = p.read()
        return BeautifulSoup(response_text, features='xml')
    except Exception:
        return False


async def main(sites_list, wait_pull_url) -> None:
    """Main loop for getting data from files.
    At the selected time, there is the lowest probability of blocking access of applications to a network XML-file."""
    while True:
        await asyncio.sleep(11*60)
        if datetime.datetime.now().minute < 45:
            continue
        while True:
            await asyncio.sleep(111)
            if datetime.datetime.now().minute < 57:
                continue
            if (datetime.datetime.now().hour % wait_pull_url) != 0:
                break
            pull_urls(sites_list)
            break


if __name__ == '__main__':
    from config import NEWS_SITES_LIST
    pull_urls(NEWS_SITES_LIST, check_date=True)
