import logging

from sqlalchemy import insert, select
from sqlalchemy.exc import SQLAlchemyError

from src.database import Session, get_session, Summary, News, Reader
from src.services import LanguageService
from src.services.news import NewsService


logger = logging.getLogger(__name__)


class SummaryService:
    def __init__(self, session: Session = get_session().__next__()):
        self.session = session
        self.language_service = LanguageService(self.session)
        self.news_service = NewsService(self.session)

    async def create(self, news_pk: int, lang_pk: int, content: str or None) -> int:
        """Writing 'Summary' instances to the database."""
        insert_stmt = insert(Summary).values(news_pk=news_pk, lang_pk=lang_pk, content=content)
        select_stmt = select(Reader).where(Reader.is_active == True, Reader.lang_pk == lang_pk)
        with self.session as s:
            try:
                new_summary = s.execute(insert_stmt)
                summary_pk = new_summary.inserted_primary_key[0]
                new_summary = s.get(Summary, summary_pk)
                new_summary.readers = s.scalars(select_stmt).all()
                s.commit()
            except SQLAlchemyError as e:
                s.rollback()
                logger.exception(f'in <def create({news_pk}, {lang_pk})>:')
                raise e
            else:
                logger.debug(f'Object <Summary> id {summary_pk} created successfully.')
                return summary_pk


if __name__ == '__main__':
    import asyncio
    ss = SummaryService()
    summary = asyncio.run(ss.create(1, 7, None))
    print(summary)
