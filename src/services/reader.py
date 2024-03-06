import logging
from typing import Any

from sqlalchemy import select, insert, update
from sqlalchemy.exc import SQLAlchemyError

from src.database import get_session, Reader, Session, Language  # , Language, ReaderSummary
from src.services import LanguageService


logger = logging.getLogger(__name__)


class ReaderService:
    def __init__(self, session: Session = get_session().__next__()):
        self.session = session
        self.language_service = LanguageService(self.session)

    async def is_exists(self, tg_user_id: int) -> tuple:
        """The values of the 'pk', 'lang_pk', 'is_active' fields are returned for an 'Reader' instance
        by the 'tg_user_id' field"""
        stmt = select(Reader).where(Reader.tg_id == tg_user_id)
        with self.session as s:
            try:
                data = s.scalars(stmt).one_or_none()
            except Exception as e:
                logger.exception(f'in <is_exists({tg_user_id})> for object <Reader>:')
                raise e
            else:
                if data:
                    lang_pk = s.scalar(select(Language.code).where(Language.pk == data.lang_pk))
                    return data.pk, lang_pk, data.is_active
                else:
                    return None, None, None

    async def create(self, tg_user_id: int, lang_code: str = None) -> (Any, str):
        """Writing 'Reader' instances to the database."""
        if lang_code:
            select_stmt = select(Language.pk).where(Language.code == lang_code.upper())
        else:
            select_stmt = None
        insert_stmt = insert(Reader).values(tg_id=tg_user_id)
        with self.session as s:
            try:
                inst = s.execute(insert_stmt)
                inst_pk = inst.inserted_primary_key[0]
                if lang_code:
                    inst = s.get(Reader, inst_pk)
                    inst.lang_pk = s.execute(select_stmt).scalar_one_or_none()
                s.commit()
            except SQLAlchemyError as e:
                s.rollback()
                logger.exception(f'in <create({tg_user_id}) for object <Reader>:')
                raise e
            else:
                logger.debug(f'Object <Reader> id {inst_pk} created successfully.')
                return inst_pk, lang_code

    async def update(self, tg_user_id: int, is_active: bool) -> bool:
        """Updating 'Reader' instances in the database."""
        upd_stmt = update(Reader).where(Reader.tg_id == tg_user_id).values(is_active=is_active)
        with self.session as s:
            try:
                s.execute(upd_stmt)
                s.commit()
            except SQLAlchemyError as e:
                s.rollback()
                logger.exception(f'in <update({tg_user_id})> for object <Reader>:')
                raise e
            else:
                logger.debug(f'Object <Reader> tg_id {tg_user_id} updated successfully.')
                return True

    async def set_language(self, tg_user_id: int, lang_code: str) -> bool:
        """Assigning a language to an instance 'Reader'."""
        inst_stmt = select(Reader).where(Reader.tg_id == tg_user_id)
        select_stmt = select(Language.pk).where(Language.code == lang_code.upper())
        with self.session as s:
            try:
                inst = s.execute(inst_stmt).scalar_one_or_none()
                inst_pk = inst.pk
                inst.lang_pk = s.execute(select_stmt).scalar_one_or_none()
                s.commit()
            except SQLAlchemyError as e:
                s.rollback()
                logger.exception(f'in <set_language({tg_user_id}, {lang_code})> for object <Reader>.')
                raise e
            else:
                logger.debug(f'Object <Reader> id {inst_pk} is assigned language {lang_code.upper()}.')
                return True


if __name__ == '__main__':
    import asyncio
    from dotenv import load_dotenv
    import os
    rs = ReaderService()
    load_dotenv()
    BOT_ADMIN_ID = int(os.getenv('BOT_ADMIN_ID'))
    # res = asyncio.run(rs.create(12345, 'rU'))
    # asyncio.run(rs.update(12345, is_active=False))
    # asyncio.run(rs.set_language(12345, 'es'))
    pk, code = asyncio.run(rs.is_exists(BOT_ADMIN_ID))
    print(pk, code)
