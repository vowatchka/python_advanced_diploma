from datetime import datetime

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from .utils import table_exists, generate_test_models
from ..db import models


@pytest.mark.anyio
async def test_table_tweet_exist(engine):
    """Проверка создания таблицы tweet."""
    assert await table_exists(engine, "tweet")


@pytest.mark.anyio
@pytest.mark.parametrize(
    "new_tweet",
    [
        models.Tweet(content="test tweet", posted_at=datetime.now(), user_id=2)
    ]
)
async def test_add_tweet(db_session, new_tweet):
    db_session.add(new_tweet)
    await db_session.commit()

    queryset = await db_session.execute(
        select(models.Tweet).where(models.Tweet.id == new_tweet.id)
    )
    added_tweet: models.Tweet = queryset.scalars().one()
    assert added_tweet.id is not None
    assert added_tweet.content == new_tweet.content
    assert added_tweet.posted_at == new_tweet.posted_at
    assert added_tweet.user_id == added_tweet.user_id


@pytest.mark.anyio
async def test_content_not_null(db_session):
    """Проверка наличия ограничения NOT NULL поля content."""
    with pytest.raises(IntegrityError, match=r".*NotNullViolationError.*"):
        db_session.add(
            models.Tweet(
                content=None,
                user_id=2,
            )
        )
        await db_session.commit()


@pytest.mark.anyio
@pytest.mark.parametrize(
    "new_tweet",
    [
        # короткий твит
        models.Tweet(content="", user_id=2),
    ]
)
async def test_content_length(db_session, new_tweet):
    """Проверка наличия ограничений по длине поля content"""
    with pytest.raises(IntegrityError, match=r".*CheckViolationError.*"):
        db_session.add(new_tweet)
        await db_session.commit()


@pytest.mark.anyio
@pytest.mark.parametrize(
    "new_tweet",
    [
        # длинный твит
        *generate_test_models(models.Tweet, range(280, 286), content=lambda count: "a" * count, user_id=2),
    ]
)
async def test_content_length_truncate(db_session, new_tweet):
    """Проверка обрезания по длине поля content."""
    db_session.add(new_tweet)
    await db_session.commit()
    await db_session.refresh(new_tweet)

    assert len(new_tweet.content) == 280


@pytest.mark.anyio
async def test_posted_at_default(db_session):
    """Проверка наличия дефолтного значения поля posted_at."""
    new_tweet = models.Tweet(content="tweet", user_id=2)
    db_session.add(new_tweet)
    await db_session.commit()

    assert new_tweet.posted_at is not None
    assert isinstance(new_tweet.posted_at, datetime)


@pytest.mark.anyio
async def test_user_id_not_null(db_session):
    """Проверка наличия ограничения NOT NULL поля user_id."""
    with pytest.raises(IntegrityError, match=r".*NotNullViolationError.*"):
        db_session.add(
            models.Tweet(
                content="tweet",
                user_id=None
            )
        )
        await db_session.commit()


@pytest.mark.anyio
@pytest.mark.parametrize(
    "new_tweet",
    [
        *generate_test_models(models.Tweet, range(100, 106), content="tweet", user_id=lambda x: x),
    ]
)
async def test_user_id_foreign_key(db_session, new_tweet):
    """Проверка наличия ограничения FOREIGN KEY поля user_id."""
    with pytest.raises(IntegrityError, match=r".*ForeignKeyViolationError.*"):
        db_session.add(new_tweet)
        await db_session.commit()


@pytest.mark.anyio
async def test_cascade_delete_tweets(db_session):
    """Проверка наличия каскадного удаления твитов."""
    user_id = 2
    tweets = [
        models.Tweet(content="tweet1", user_id=user_id),
        models.Tweet(content="tweet2", user_id=user_id),
        models.Tweet(content="tweet3", user_id=user_id),
    ]

    async with db_session.begin():
        db_session.add_all(tweets)

        tweet_qs = await db_session.execute(
            select(models.Tweet).where(models.Tweet.user_id == user_id)
        )
        assert len(tweet_qs.scalars().all()) == len(tweets)

        user_qs = await db_session.execute(
            select(models.User).where(models.User.id == user_id)
        )
        await db_session.delete(user_qs.scalars().one())

        tweet_qs = await db_session.execute(
            select(models.Tweet).where(models.Tweet.user_id == user_id)
        )
        assert len(tweet_qs.scalars().all()) == 0
