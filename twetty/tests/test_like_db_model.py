import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from .utils import table_exists, generate_test_models
from ..db import models


@pytest.mark.anyio
async def test_add_like(db_session):
    """Проверка добавления нового лайка."""
    users = [
        models.User(nickname="test1", api_key="a" * 30),
        models.User(nickname="test2", api_key="b" * 30),
    ]
    db_session.add_all(users)
    await db_session.commit()

    tweet = models.Tweet(content="test", user_id=users[0].id)
    db_session.add(tweet)
    await db_session.commit()

    new_like = models.Like(tweet_id=tweet.id, user_id=users[1].id)
    db_session.add(new_like)
    await db_session.commit()

    queryset = await db_session.execute(
        select(models.Like).where(models.Like.id == new_like.id)
    )
    added_like: models.Like = queryset.scalars().one()
    assert added_like.id is not None
    assert added_like.tweet_id == new_like.tweet_id
    assert added_like.user_id == new_like.user_id


@pytest.mark.anyio
async def test_cascade_delete_likes(db_session):
    """Проверка наличия каскадного удаления лайков."""
    users = [
        models.User(nickname="test1", api_key="a" * 30),
        models.User(nickname="test2", api_key="b" * 30),
        models.User(nickname="test3", api_key="c" * 30),
    ]
    db_session.add_all(users)
    await db_session.commit()

    tweet = models.Tweet(content="test", user_id=users[0].id)
    db_session.add(tweet)
    await db_session.commit()

    async with db_session.begin():
        likes = [
            models.Like(tweet_id=tweet.id, user_id=users[1].id),
            models.Like(tweet_id=tweet.id, user_id=users[2].id),
        ]
        db_session.add_all(likes)

        likes_qs = await db_session.execute(
            select(models.Like).where(models.Like.tweet_id == tweet.id)
        )
        assert len(likes_qs.scalars().all()) == len(likes)

        # удаляем одного пользователя, оставившего лайки
        user_4_qs = await db_session.execute(
            select(models.User).where(models.User.id == users[2].id)
        )
        await db_session.delete(user_4_qs.scalars().one())

        likes = [like for like in likes if like.user_id != users[2].id]

        likes_qs = await db_session.execute(
            select(models.Like).where(models.Like.tweet_id == tweet.id)
        )
        assert len(likes_qs.scalars().all()) == len(likes)

        # удаляем твит с лайками
        tweet_qs = await db_session.execute(
            select(models.Tweet).where(models.Tweet.id == tweet.id)
        )
        await db_session.delete(tweet_qs.scalars().one())

        likes_qs = await db_session.execute(
            select(models.Like).where(models.Like.tweet_id == tweet.id)
        )
        assert len(likes_qs.scalars().all()) == 0


@pytest.mark.anyio
async def test_can_like_own_tweet(db_session):
    """Проверка, что можно лайкать свой твит."""
    user = models.User(
        nickname="testtest",
        api_key="a" * 30,
    )
    db_session.add(user)
    await db_session.commit()

    tweet = models.Tweet(
        content="test",
        user_id=user.id
    )
    db_session.add(tweet)
    await db_session.commit()

    new_like = models.Like(
        tweet_id=tweet.id,
        user_id=user.id,
    )
    db_session.add(new_like)
    await db_session.commit()


@pytest.mark.anyio
async def test_cannot_like_twice(db_session):
    """Проверка, что один пользователь не может добавить еще один лайк
    твиту, который он уже залайкал."""
    user = models.User(
        nickname="testtest",
        api_key="a" * 30,
    )
    db_session.add(user)
    await db_session.commit()

    tweet = models.Tweet(
        content="test",
        user_id=user.id
    )
    db_session.add(tweet)
    await db_session.commit()

    like_once = models.Like(
        tweet_id=tweet.id,
        user_id=user.id
    )
    db_session.add(like_once)
    await db_session.commit()

    like_twice = models.Like(
        tweet_id=tweet.id,
        user_id=user.id
    )
    with pytest.raises(IntegrityError, match=r".*UniqueViolationError.*"):
        db_session.add(like_twice)
        await db_session.commit()
