from datetime import datetime
from typing import List

from sqlalchemy import ForeignKey, BigInteger, String, Text, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Mapped, mapped_column


Base = declarative_base()


class Language(Base):
    __tablename__ = 'languages'
    pk: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(8), unique=True)
    name: Mapped[str] = mapped_column(String(32), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    readers: Mapped[List['Reader']] = relationship(back_populates='language')
    summaries: Mapped[List['Summary']] = relationship(back_populates='language')
    newses: Mapped[List['News']] = relationship(back_populates='language')


class Reader(Base):
    __tablename__ = 'readers'
    pk: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[datetime] = mapped_column(default=datetime.now)
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    lang_pk: Mapped[int] = mapped_column(ForeignKey('languages.pk'), nullable=True)
    language: Mapped['Language'] = relationship(back_populates='readers')
    summaries: Mapped[List['Summary']] = relationship(secondary='reader_summary',
                                                      back_populates='readers',
                                                      viewonly=True, )


class News(Base):
    __tablename__ = 'newses'
    pk: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[datetime] = mapped_column(default=datetime.now)
    url: Mapped[str] = mapped_column(unique=True)
    day: Mapped[datetime] = mapped_column(nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=True)
    has_summary: Mapped[bool] = mapped_column(default=False)
    has_summaries: Mapped[bool] = mapped_column(default=False)
    lang_pk: Mapped[int] = mapped_column(ForeignKey('languages.pk'))
    language: Mapped['Language'] = relationship(back_populates='newses')
    summaries: Mapped[List['Summary']] = relationship(back_populates='news')


class Summary(Base):
    __tablename__ = 'summaries'
    pk: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[datetime] = mapped_column(default=datetime.now)
    content: Mapped[str] = mapped_column(Text)
    lang_pk: Mapped[int] = mapped_column(ForeignKey('languages.pk'))
    news_pk: Mapped[int] = mapped_column(ForeignKey('newses.pk'))
    is_sent: Mapped[bool] = mapped_column(default=False)
    language: Mapped['Language'] = relationship(back_populates='summaries')
    news: Mapped['News'] = relationship(back_populates='summaries')
    readers: Mapped[List['Reader']] = relationship(secondary='reader_summary', back_populates='summaries')
    __table_args__ = (UniqueConstraint('lang_pk', 'news_pk', name='uc_language_summary'), )


class ReaderSummary(Base):
    __tablename__ = 'reader_summary'
    pk: Mapped[int] = mapped_column(primary_key=True)
    is_sent: Mapped[bool] = mapped_column(default=False)
    summary_pk: Mapped[int] = mapped_column(ForeignKey('summaries.pk'), nullable=False)
    reader_pk: Mapped[int] = mapped_column(ForeignKey('readers.pk'), nullable=False)
    __table_args__ = (UniqueConstraint('summary_pk', 'reader_pk', name='uc_reader_summary'), )

