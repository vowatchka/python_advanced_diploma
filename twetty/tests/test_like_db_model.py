import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from .utils import table_exists, generate_test_models
from ..db import models


@pytest.mark.anyio
async def test_table_like_exists(engine):
    """Проверка существования таблицы like."""
    is_exists = await table_exists(engine, "like")
    assert is_exists


@pytest.mark.anyio
async def test_tweet_id_not_null(db_session):
    """Проверка наличия ограничения NOT NULL поля tweet_id."""
    with pytest.raises(IntegrityError, match=r".*NotNullViolationError.*"):
        db_session.add(
            models.Like(
                tweet_id=None,
                user_id=1,
            )
        )
        await db_session.commit()


@pytest.mark.anyio
@pytest.mark.parametrize(
    "new_like",
    [
        *generate_test_models(models.Like, range(100, 106), tweet_id=lambda x: x, user_id=1),
    ]
)
async def test_tweet_id_foreign_key(db_session, new_like):
    """Проверка наличия ограничения FOREIGN KEY поля tweet_id."""
    with pytest.raises(IntegrityError, match=r".*ForeignKeyViolationError.*"):
        db_session.add(new_like)
        await db_session.commit()


@pytest.mark.anyio
async def test_cascade_delete_likes(db_session):
    """Проверка наличия каскадного удаления лайков."""
    tweet_id = 2
    user_id_1 = 1
    user_id_4 = 4
    likes = [
        models.Like(tweet_id=tweet_id, user_id=user_id_1),
        models.Like(tweet_id=tweet_id, user_id=user_id_1),
        models.Like(tweet_id=tweet_id, user_id=user_id_4),
        models.Like(tweet_id=tweet_id, user_id=user_id_4),
    ]

    async with db_session.begin():
        db_session.add_all(likes)

        likes_qs = await db_session.execute(
            select(models.Like).where(models.Like.tweet_id == tweet_id)
        )
        assert len(likes_qs.scalars().all()) == len(likes)

        # удаляем одного пользователя, оставившего лайки
        user_4_qs = await db_session.execute(
            select(models.User).where(models.User.id == user_id_4)
        )
        await db_session.delete(user_4_qs.scalars().one())

        likes = [like for like in likes if like.user_id != user_id_4]

        likes_qs = await db_session.execute(
            select(models.Like).where(models.Like.tweet_id == tweet_id)
        )
        assert len(likes_qs.scalars().all()) == len(likes)

        # удаляем твит с лайками
        tweet_qs = await db_session.execute(
            select(models.Tweet).where(models.Tweet.id == tweet_id)
        )
        await db_session.delete(tweet_qs.scalars().one())

        likes_qs = await db_session.execute(
            select(models.Like).where(models.Like.tweet_id == tweet_id)
        )
        assert len(likes_qs.scalars().all()) == 0


@pytest.mark.anyio
async def test_user_id_not_null(db_session):
    """Проверка наличия ограничения NOT NULL поля user_id."""
    with pytest.raises(IntegrityError, match=r".*NotNullViolationError.*"):
        db_session.add(
            models.Like(
                tweet_id=1,
                user_id=None,
            )
        )
        await db_session.commit()


@pytest.mark.anyio
@pytest.mark.parametrize(
    "new_like",
    [
        *generate_test_models(models.Like, range(100, 106), tweet_id=1, user_id=lambda x: x),
    ]
)
async def test_user_id_foreign_key(db_session, new_like):
    """Проверка наличия ограничения FOREIGN KEY поля user_id."""
    with pytest.raises(IntegrityError, match=r".*ForeignKeyViolationError.*"):
        db_session.add(new_like)
        await db_session.commit()
