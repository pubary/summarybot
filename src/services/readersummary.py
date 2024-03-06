import datetime
from typing import Any

from sqlalchemy import select, update

from src.database import Session, get_session, Summary, Reader, ReaderSummary, News


class ReaderSummaryService:
    def __init__(self, session: Session = get_session().__next__()):
        self.session = session

    async def get_notsent_readersummary(self, amount: int, age: float) -> Any:
        """Returns from database the 'pk' field of the 'ReaderSummary' instance, fields 'content', 'news_pk' of
        the 'Summary' instance, field 'tg_id' of the 'Reader' instance, provided that the 'Summary.date' field
        matches the age, fields 'Reader.is_active', 'News.has_summaries' have the value 'True',
        field 'ReaderSummary.is_sent' have the value 'False'."""
        target_date = datetime.datetime.now() - datetime.timedelta(days=age)
        stmt = \
            select(ReaderSummary.pk,
                   Summary.content,
                   Summary.news_pk,
                   Reader.tg_id).\
            join(Summary).\
            join(Reader).\
            join(News).\
            where(Summary.date >= target_date).\
            where(Reader.is_active == True).\
            where(News.has_summaries == True).\
            where(ReaderSummary.is_sent == False).\
            order_by(Summary.news_pk).\
            limit(amount)
        with self.session as s:
            try:
                data = s.execute(stmt)
            except Exception as e:
                raise e
            else:
                return data.fetchall()

    async def update_many(self, update_list: list) -> bool:
        """Updating multiple 'ReaderSummary' instances in the database."""
        with self.session as s:
            try:
                s.execute(update(ReaderSummary), update_list)
                s.commit()
            except Exception as e:
                s.rollback()
                raise e
            else:
                return True


if __name__ == '__main__':
    import asyncio
    res = asyncio.run(ReaderSummaryService().get_notsent_readersummary(1000, 1))
    print('len(res)=', len(res))
    for r in res:
        print(f'\nnews_pk:', r.news_pk)
        print('ReaderSummary_pk:', r.pk)
        print(f'Summary.content:\n', r.content)
        break
