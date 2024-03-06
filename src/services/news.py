import datetime
import logging
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError

from src.database import Session, get_session, News, Language
from src.services import LanguageService


logger = logging.getLogger(__name__)


class NewsService:
    def __init__(self, session: Session = get_session().__next__()):
        self.session = session
        self.language_service = LanguageService(self.session)

    def get_all_url(self) -> list:
        """Getting field 'url' from the database for all instance 'News'."""
        stmt = select(News.url)
        with self.session as s:
            data = s.scalars(stmt).all()
        if data:
            return data
        else:
            return list()

    def create_many(self, data_list: list, lang_code: str, has_summary: bool, has_summaries: bool) -> None:
        """Writing multiple 'News' instances to the database."""
        select_stmt = select(Language.pk).where(Language.code == lang_code.upper())
        with self.session as s:
            lang_pk = s.execute(select_stmt).scalar_one_or_none()
            for count in range(len(data_list)):
                url = data_list[count].get('url')
                day = data_list[count].get('day', None)
                content = data_list[count].get('content', '')
                news = News(url=url.lower(),
                            content=content,
                            lang_pk=lang_pk,
                            has_summary=has_summary,
                            has_summaries=has_summaries)
                try:
                    s.add(news)
                    if isinstance(day, datetime.datetime):
                        news.day = day
                    s.flush()
                except SQLAlchemyError as e:
                    s.rollback()
                    data_list.pop(count)
                    logger.debug(f'News url {url} not added to database. Error:\n{e.args[0]}')
                    self.create_many(data_list, lang_code, has_summary, has_summaries)
                    break
                except Exception as e:
                    s.rollback()
                    raise e
            s.commit()

    async def update_news(self, news_pk: int, content: str or None, has_summary: bool, has_summaries: bool):
        """Updating 'News' instances in the database."""
        upd_stmt = update(News).where(News.pk == news_pk).values(content=content,
                                                                 has_summary=has_summary,
                                                                 has_summaries=has_summaries)
        with self.session as s:
            try:
                s.execute(upd_stmt)
                s.commit()
            except SQLAlchemyError as e:
                s.rollback()
                logger.exception(f'in <update_news(news id {news_pk})>:')
                raise e
            else:
                logger.debug(f'Object <News> id {news_pk} updated successfully.')
                return True

    async def get_news_data(self, pk: int) -> Any:
        """Getting 'News' instance from the database by its 'pk' field."""
        stmt = select(News).where(News.pk == pk)
        with self.session as s:
            data = s.execute(stmt).scalar_one_or_none()
            if data:
                return data

    async def get_many_news_data(self, age: float = 1, has_summary: bool =False, has_summaries: bool = False) -> Any:
        """Getting from the database fields 'pk', 'url', 'lang_pk', 'lang_pk.lang_code' as 'lang_pk', 'day'
        for an 'News' instance by its age, fields 'has_summary' and 'has_summaries'."""
        target_date = datetime.datetime.now() - datetime.timedelta(days=age)
        stmt = select(News.pk.label('pk'),
                      News.url.label('url'),
                      News.lang_pk.label('lang_pk'),
                      Language.code.label('lang_code'),
                      News.day.label('day')).\
            join(Language). \
            where(News.date >= target_date). \
            where(News.has_summary == has_summary,
                  News.has_summaries == has_summaries). \
            order_by(News.pk)
        with self.session as s:
            data = s.execute(stmt)
            if data:
                return data


if __name__ == '__main__':
    import asyncio
    ns = NewsService()
    # all_urls = asyncio.run(ns.get_all_url())
    # print(len(all_urls))
    # asyncio.run(ns.update_news(35633, None, True, True))
    # res = asyncio.run(ns.get_news_data('27563'))
    # if res.day:
    #     news_day = res.day.strftime('%H:%M %Y-%m-%d')
    #     print(res.pk, res.day, news_day)
    # datas = [{'url': 'test1', 'day': datetime.datetime.strptime('12:45:56+00:00', '%H:%M:%S%z'), 'content': '11'},
    #          {'url': 'test1', 'day': '', 'content': '22'},]
    # ns.create_many(datas, 'ru', has_summary=True, has_summaries=True)
    res = asyncio.run(ns.get_many_news_data(age=10, has_summary=False, has_summaries=False))
    if any(res):
        for r in res:
            print(r.pk, r.lang_code, r.lang_pk, '\n', r.url)
            break
