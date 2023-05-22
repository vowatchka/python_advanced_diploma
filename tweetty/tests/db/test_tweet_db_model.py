from datetime import datetime

import pytest
from sqlalchemy import select

from ...db import models


@pytest.mark.anyio
async def test_add_tweet(db_session):
    user = models.User(nickname="test1", api_key="a" * 30)
    db_session.add(user)
    await db_session.commit()

    new_tweet = models.Tweet(content="test", posted_at=datetime.now(), user_id=user.id)
    db_session.add(new_tweet)
    await db_session.commit()

    queryset = await db_session.execute(
        select(models.Tweet).where(models.Tweet.id == new_tweet.id)
    )
    added_tweet: models.Tweet = queryset.scalars().one()
    assert added_tweet.id is not None
    assert added_tweet.content == new_tweet.content
    assert added_tweet.posted_at == new_tweet.posted_at
    assert added_tweet.user_id == new_tweet.user_id


@pytest.mark.anyio
async def test_cascade_delete_tweets(db_session):
    """Проверка наличия каскадного удаления твитов."""
    user = models.User(nickname="test1", api_key="a" * 30)
    db_session.add(user)
    await db_session.commit()

    async with db_session.begin():
        tweets = [
            models.Tweet(content="tweet1", user_id=user.id),
            models.Tweet(content="tweet2", user_id=user.id),
            models.Tweet(content="tweet3", user_id=user.id),
        ]
        db_session.add_all(tweets)

        tweet_qs = await db_session.execute(
            select(models.Tweet).where(models.Tweet.user_id == user.id)
        )
        assert len(tweet_qs.scalars().all()) == len(tweets)

        user_qs = await db_session.execute(
            select(models.User).where(models.User.id == user.id)
        )
        await db_session.delete(user_qs.scalars().one())

        tweet_qs = await db_session.execute(
            select(models.Tweet).where(models.Tweet.user_id == user.id)
        )
        assert len(tweet_qs.scalars().all()) == 0
