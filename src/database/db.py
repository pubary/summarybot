import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import DB_URL


logger = logging.getLogger(__name__)

engine = create_engine(
    DB_URL,
    connect_args={'check_same_thread': False},
    max_overflow=10,
    pool_size=20,
    pool_recycle=3600,
    pool_timeout=5,
    echo=False
)

Session = sessionmaker(engine, autocommit=False, autoflush=False)


def create_db() -> None:
    """Database creation."""
    from src.database.tables import Base
    Base.metadata.create_all(engine)
    logger.info('Database created!')


def get_session() -> Session:
    """Obtaining a session to work with the database."""
    session = Session()
    try:
        yield session
    finally:
        session.close()


if __name__ == '__main__':
    create_db()
