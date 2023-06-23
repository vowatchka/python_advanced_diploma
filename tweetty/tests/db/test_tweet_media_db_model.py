from datetime import datetime

import pytest
from sqlalchemy import select

from ...db import models

pytestmark = [pytest.mark.anyio, pytest.mark.db_models, pytest.mark.tweet_media_db_model]


async def test_add_tweet_media(db_session):
    """Проверка добавления нового медиа."""
    user = models.User(nickname="test1", api_key="a" * 30)
    db_session.add(user)
    await db_session.commit()

    new_tweet = models.Tweet(content="test", user_id=user.id)
    db_session.add(new_tweet)
    await db_session.commit()

    new_tweet_media = models.TweetMedia(rel_uri="/test", uploaded_at=datetime.now(), tweet_id=new_tweet.id)
    db_session.add(new_tweet_media)
    await db_session.commit()

    queryset = await db_session.execute(
        select(models.TweetMedia).where(models.TweetMedia.id == new_tweet_media.id)
    )
    added_tweet_media: models.TweetMedia = queryset.scalars().one()
    assert added_tweet_media.id is not None
    assert added_tweet_media.rel_uri == new_tweet_media.rel_uri
    assert added_tweet_media.uploaded_at == new_tweet_media.uploaded_at
    assert added_tweet_media.tweet_id == new_tweet_media.tweet_id


async def test_cascade_delete_tweet_medias(db_session):
    """Проверка наличия каскадного удаления медиа."""
    user = models.User(nickname="test1", api_key="a" * 30)
    db_session.add(user)
    await db_session.commit()

    tweet = models.Tweet(content="test", user_id=user.id)
    db_session.add(tweet)
    await db_session.commit()

    async with db_session.begin():
        new_tweet_medias = [
            models.TweetMedia(rel_uri="/test1", tweet_id=tweet.id),
            models.TweetMedia(rel_uri="/test2", tweet_id=tweet.id),
            models.TweetMedia(rel_uri="/test3", tweet_id=tweet.id),
        ]
        db_session.add_all(new_tweet_medias)

        tweet_medias_qs = await db_session.execute(
            select(models.TweetMedia).where(models.TweetMedia.tweet_id == tweet.id)
        )
        assert len(tweet_medias_qs.scalars().all()) == len(new_tweet_medias)

        tweet_qs = await db_session.execute(
            select(models.Tweet).where(models.Tweet.id == tweet.id)
        )
        await db_session.delete(tweet_qs.scalars().one())

        tweet_medias_qs = await db_session.execute(
            select(models.TweetMedia).where(models.TweetMedia.tweet_id == tweet.id)
        )
        assert len(tweet_medias_qs.scalars().all()) == 0
