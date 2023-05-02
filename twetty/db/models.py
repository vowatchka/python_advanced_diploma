from sqlalchemy import Column, Integer, String, CheckConstraint
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

from .pg import POSTGRES_URL, make_async_postgres_url

engine = create_async_engine(make_async_postgres_url(POSTGRES_URL))
Session = sessionmaker(expire_on_commit=False, class_=AsyncSession)

Base: type = declarative_base()


class User(Base):
    """Таблица пользователей."""

    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    nickname = Column(
        String,
        unique=True,
        nullable=False,
        doc="Никнейм",
        comment="Никнейм",
    )
    first_name = Column(
        String,
        nullable=True,
        default=None,
        doc="Имя",
        comment="Имя",
    )
    last_name = Column(
        String,
        nullable=True,
        default=None,
        doc="Фамилия",
        comment="Фамилия",
    )
    api_key = Column(
        String,
        unique=True,
        nullable=False,
        doc="Ключ API, выданный пользователю",
        comment="Ключ API, выданный пользователю",
    )

    __table_args__ = (
        CheckConstraint(
            "length(nickname) >= 5 and length(nickname) <= 20",
            name="nickname_length"
        ),
        CheckConstraint(
            "length(first_name) >= 1 and length(first_name) <= 100",
            name="first_name_length"
        ),
        CheckConstraint(
            "length(last_name) >= 1 and length(last_name) <= 100",
            name="last_name_length"
        ),
        CheckConstraint(
            "length(api_key) >= 30 and length(api_key) <= 256",
            name="api_key_length"
        ),
    )
