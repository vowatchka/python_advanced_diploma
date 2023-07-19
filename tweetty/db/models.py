from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.ext.associationproxy import AssociationProxy, association_proxy
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import Mapped, declarative_base, relationship, sessionmaker

from tweetty.settings import POSTGRES_URL

from .pg import make_async_postgres_url

engine = create_async_engine(make_async_postgres_url(POSTGRES_URL))
Session = sessionmaker(expire_on_commit=False, class_=AsyncSession)

Base: Any = declarative_base()


async def db_session():
    session: AsyncSession = Session(bind=engine)
    try:
        yield session
    finally:
        await session.close()


class User(Base):
    """Таблица пользователей."""

    __tablename__ = "user"

    id: Mapped[int] = Column(Integer, primary_key=True)
    nickname: Mapped[str] = Column(
        String,
        unique=True,
        nullable=False,
        doc="Никнейм",
        comment="Никнейм",
    )
    first_name: Mapped[str | None] = Column(
        String,
        nullable=True,
        default=None,
        doc="Имя",
        comment="Имя",
    )
    last_name: Mapped[str | None] = Column(
        String,
        nullable=True,
        default=None,
        doc="Фамилия",
        comment="Фамилия",
    )
    api_key: Mapped[str] = Column(
        String,
        unique=True,
        nullable=False,
        doc="Ключ API, выданный пользователю",
        comment="Ключ API, выданный пользователю",
    )

    __table_args__ = (
        CheckConstraint("length(nickname) >= 5 and length(nickname) <= 20", name="nickname_length"),
        CheckConstraint("length(first_name) >= 1 and length(first_name) <= 100", name="first_name_length"),
        CheckConstraint("length(last_name) >= 1 and length(last_name) <= 100", name="last_name_length"),
        CheckConstraint("length(api_key) >= 30 and length(api_key) <= 256", name="api_key_length"),
    )

    tweets: Mapped[list[Tweet]] = relationship("Tweet", back_populates="user", cascade="all, delete-orphan")
    likes: Mapped[list[Like]] = relationship("Like", back_populates="user", cascade="all, delete-orphan")
    followers: Mapped[list[Follower]] = relationship(
        "Follower", back_populates="user", foreign_keys="Follower.user_id", cascade="all, delete-orphan"
    )
    followings: Mapped[list[Follower]] = relationship(
        "Follower", back_populates="follower", foreign_keys="Follower.follower_id", cascade="all, delete-orphan"
    )

    liked_tweets: AssociationProxy[list[Tweet]] = association_proxy("likes", "tweet")
    followed_users: AssociationProxy[list[User]] = association_proxy("followers", "follower")
    following_users: AssociationProxy[list[User]] = association_proxy("followings", "user")


class Tweet(Base):
    """Таблица твитов."""

    __tablename__ = "tweet"

    id: Mapped[int] = Column(Integer, primary_key=True)
    content: Mapped[str] = Column(
        String(280),
        nullable=False,
        doc="Содержимое твита",
        comment="Содержимое твита",
    )
    posted_at: Mapped[datetime] = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        doc="Дата-время твита",
        comment="Дата-время твита",
    )
    user_id: Mapped[int] = Column(
        Integer,
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        doc="Пользователь, сделавший твит",
        comment="Пользователь, сделавший твит",
    )

    user: Mapped[User] = relationship("User", back_populates="tweets")
    medias: Mapped[list[TweetMedia]] = relationship("TweetMedia", back_populates="tweet", cascade="all, delete-orphan")
    likes: Mapped[list[Like]] = relationship("Like", back_populates="tweet", cascade="all, delete-orphan")

    liked_by_users: AssociationProxy[list[User]] = association_proxy("likes", "user")

    __table_args__ = (CheckConstraint("length(content) >= 1", name="content_length"),)


class TweetMedia(Base):
    """Таблица медиа-файлов, прикрепленных к твитам."""

    __tablename__ = "tweet_media"

    id: Mapped[int] = Column(Integer, primary_key=True)
    rel_uri: Mapped[str] = Column(
        String,
        nullable=False,
        doc="Относительный URI медиа-файла",
        comment="Относительный URI медиа-файла",
    )
    uploaded_at: Mapped[datetime] = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        doc="Дата-время загрузки файла",
        comment="Дата-время загрузки файла",
    )
    tweet_id: Mapped[int | None] = Column(
        Integer,
        ForeignKey("tweet.id", ondelete="CASCADE"),
        nullable=True,
        default=None,
        doc="Твит",
        comment="Твит",
    )

    tweet: Mapped[Tweet] = relationship("Tweet", back_populates="medias")

    __table_args__ = (CheckConstraint("length(rel_uri) >= 1", name="rel_uri_length"),)


class Like(Base):
    """Таблица лайков."""

    __tablename__ = "like"

    id: Mapped[int] = Column(Integer, primary_key=True)
    tweet_id: Mapped[int] = Column(
        Integer,
        ForeignKey("tweet.id", ondelete="CASCADE"),
        nullable=False,
        doc="Твит",
        comment="Твит",
    )
    user_id: Mapped[int] = Column(
        Integer,
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        doc="Пользователь",
        comment="Пользователь",
    )

    tweet: Mapped[Tweet] = relationship("Tweet", back_populates="likes")
    user: Mapped[User] = relationship("User", back_populates="likes")

    __table_args__ = (UniqueConstraint("tweet_id", "user_id", name="unique_like"),)


class Follower(Base):
    """Таблица подписчиков."""

    __tablename__ = "follower"

    id: Mapped[int] = Column(Integer, primary_key=True)
    user_id: Mapped[int] = Column(
        Integer,
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        doc="Пользователь, на которого подписаны",
        comment="Пользователь, на которого подписаны",
    )
    follower_id: Mapped[int] = Column(
        Integer,
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        doc="Подписчик",
        comment="Подписчик",
    )

    user: Mapped[User] = relationship("User", back_populates="followers", foreign_keys=[user_id])
    follower: Mapped[User] = relationship("User", back_populates="followings", foreign_keys=[follower_id])

    __table_args__ = (
        CheckConstraint("user_id <> follower_id", name="user_and_follower_not_equal"),
        UniqueConstraint("user_id", "follower_id", name="unique_following"),
    )
