import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from src.database import get_session, Language, Session, Reader


logger = logging.getLogger(__name__)


class LanguageService:
    def __init__(self, session: Session = get_session().__next__()):
        self.session = session

    def create_many(self, languages_list: list) -> None:
        """Writing multiple 'Language' instances to the database."""
        if len(languages_list):
            with self.session as s:
                for count in range(len(languages_list)):
                    lang_code = languages_list[count]['language']
                    lang_name = languages_list[count]['name']
                    language = Language(code=lang_code.upper(), name=lang_name)
                    try:
                        s.add(language)
                        s.flush()
                    except SQLAlchemyError as e:
                        s.rollback()
                        languages_list.pop(count)
                        logger.debug(f'Language {lang_code} not added to database. Error:\n{e.args[0]}')
                        self.create_many(languages_list)
                        break
                    except Exception as e:
                        self.session.rollback()
                        raise e
                s.commit()

    def exist_lang(self, lang_code: str) -> bool:
        """Checking if an 'Language' instance exists in the database."""
        stmt = select(Language).where(Language.code == lang_code.upper())
        with self.session as s:
            data = s.scalar(stmt)
        if data:
            return True
        else:
            return False

    async def get_lang(self, lang_code: str) -> Any:
        """Getting fields 'pk', 'code', 'name' from the database for an 'Language' instance by its 'code' field."""
        stmt = select(Language.pk.label('pk'),
                      Language.code.label('code'),
                      Language.name.label('name'), ).where(Language.code == lang_code.upper())
        with self.session as s:
            data = s.execute(stmt).first()
            if data:
                return data

    async def get_all_code(self) -> list:
        """Getting field 'code' from the database for all 'Language' instance."""
        stmt = select(Language.code).where(Language.is_active == True).order_by(Language.code)
        with self.session as s:
            data = s.scalars(stmt).all()
        if data:
            return data

    async def get_readers_languages(self) -> Any:
        """Getting fields 'language.pk', 'language.code' from the database
        for 'Readers' instance with the status 'active=True'."""
        stmt = select(Language.pk.label('pk'), Language.code.label('code')).\
                join(Reader).where(Reader.is_active == True).\
                order_by(Language.pk).\
                distinct()
        with self.session as s:
            data = s.execute(stmt)
        if data:
            return data


if __name__ == '__main__':
    import asyncio
    ls = LanguageService()
    res = asyncio.run(ls.get_readers_languages())
    print([r.code for r in res])
    res = asyncio.run(ls.get_lang('ru'))
    print(res.code, res.name)
    res = asyncio.run(ls.get_all_code())
    print(res)
