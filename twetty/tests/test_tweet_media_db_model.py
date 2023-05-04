from datetime import datetime

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from .utils import table_exists, generate_test_models
from ..db import models


@pytest.mark.anyio
async def test_table_tweet_media_exist(engine):
    """Проверка существования таблицы tweet_media."""
    is_exists = await table_exists(engine, "tweet_media")
    assert is_exists


@pytest.mark.anyio
async def test_rel_uri_not_null(db_session):
    """Проверка наличия ограничения NOT NULL поля rel_uri."""
    with pytest.raises(IntegrityError, match=r".*NotNullViolationError.*"):
        db_session.add(
            models.TweetMedia(
                rel_uri=None,
            )
        )
        await db_session.commit()


@pytest.mark.anyio
@pytest.mark.parametrize(
    "new_tweet_media",
    [
        # короткий путь
        models.TweetMedia(rel_uri=""),
    ]
)
async def test_rel_uri_length(db_session, new_tweet_media):
    with pytest.raises(IntegrityError, match=r".*CheckViolationError.*"):
        db_session.add(new_tweet_media)
        await db_session.commit()


@pytest.mark.anyio
async def test_uploaded_at_default(db_session):
    """Проверка наличия дефолтного значения поля uploaded_at."""
    new_tweet_media = models.TweetMedia(rel_uri="/test")
    db_session.add(new_tweet_media)
    await db_session.commit()
    await db_session.refresh(new_tweet_media)

    assert new_tweet_media.uploaded_at is not None
    assert isinstance(new_tweet_media.uploaded_at, datetime)


@pytest.mark.anyio
@pytest.mark.parametrize(
    "new_tweet_media",
    [
        *generate_test_models(models.TweetMedia, range(100, 106), rel_uri="/test", tweet_id=lambda x: x)
    ]
)
async def test_tweet_id_foreign_key(db_session, new_tweet_media):
    """Поверка наличия ограничения FOREIGN KEY поля tweet_id."""
    with pytest.raises(IntegrityError, match=r".*ForeignKeyViolationError.*"):
        db_session.add(new_tweet_media)
        await db_session.commit()


@pytest.mark.anyio
async def test_cascade_delete_tweet_medias(db_session):
    """Проверка наличия каскадного удаления медиа."""
    tweet_id = 1
    new_tweet_medias = [
        models.TweetMedia(rel_uri="/test1", tweet_id=tweet_id),
        models.TweetMedia(rel_uri="/test2", tweet_id=tweet_id),
        models.TweetMedia(rel_uri="/test3", tweet_id=tweet_id),
    ]

    async with db_session.begin():
        db_session.add_all(new_tweet_medias)

        tweet_medias_qs = await db_session.execute(
            select(models.TweetMedia).where(models.TweetMedia.tweet_id == tweet_id)
        )
        assert len(tweet_medias_qs.scalars().all()) == len(new_tweet_medias)

        tweet_qs = await db_session.execute(
            select(models.Tweet).where(models.Tweet.id == tweet_id)
        )
        await db_session.delete(tweet_qs.scalars().one())

        tweet_medias_qs = await db_session.execute(
            select(models.TweetMedia).where(models.TweetMedia.tweet_id == tweet_id)
        )
        assert len(tweet_medias_qs.scalars().all()) == 0
