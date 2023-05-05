import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from .utils import table_exists, generate_test_models
from ..db import models


@pytest.mark.anyio
async def test_table_follower_exists(engine):
    """Проверка существования таблицы follower."""
    is_exists = await table_exists(engine, "follower")
    assert is_exists


@pytest.mark.anyio
async def test_user_id_not_null(db_session):
    """Проверка наличия ограничения NOT NULL поля user_id."""
    with pytest.raises(IntegrityError, match=r".*NotNullViolationError.*"):
        db_session.add(
            models.Follower(
                user_id=None,
                follower_id=1,
            )
        )
        await db_session.commit()


@pytest.mark.anyio
@pytest.mark.parametrize(
    "new_follower",
    [
        *generate_test_models(models.Follower, range(100, 106), user_id=lambda x: x, follower_id=1),
    ]
)
async def test_user_id_foreign_key(db_session, new_follower):
    """Проверка наличия ограничения FOREIGN KEY поля user_id."""
    with pytest.raises(IntegrityError, match=r".*ForeignKeyViolationError.*"):
        db_session.add(new_follower)
        await db_session.commit()


@pytest.mark.anyio
async def test_follower_id_not_null(db_session):
    """Проверка наличия ограничения NOT NULL поля follower_id."""
    with pytest.raises(IntegrityError, match=r".*NotNullViolationError.*"):
        db_session.add(
            models.Follower(
                user_id=1,
                follower_id=None,
            )
        )
        await db_session.commit()


@pytest.mark.anyio
@pytest.mark.parametrize(
    "new_follower",
    [
        *generate_test_models(models.Follower, range(100, 106), user_id=1, follower_id=lambda x: x),
    ]
)
async def test_follower_id_foreign_key(db_session, new_follower):
    """Проверка наличия ограничения FOREIGN KEY поля follower_id."""
    with pytest.raises(IntegrityError, match=r".*ForeignKeyViolationError.*"):
        db_session.add(new_follower)
        await db_session.commit()


@pytest.mark.anyio
async def test_cascade_delete_followers(db_session):
    """Проверка наличия каскадного удаления фолловеров."""
    users = [
        models.User(nickname="test1", api_key="a" * 30),
        models.User(nickname="test2", api_key="b" * 30),
        models.User(nickname="test3", api_key="c" * 30),
    ]
    db_session.add_all(users)
    await db_session.commit()

    async with db_session.begin():
        followers = [
            models.Follower(user_id=users[0].id, follower_id=users[1].id),
            models.Follower(user_id=users[0].id, follower_id=users[2].id),
        ]
        db_session.add_all(followers)

        followers_qs = await db_session.execute(
            select(models.Follower).where(models.Follower.user_id == users[0].id)
        )
        assert len(followers_qs.scalars().all()) == len(followers)

        # удаляем одного подписчика
        follower_qs = await db_session.execute(
            select(models.Follower).where(models.Follower.follower_id == users[2].id)
        )
        await db_session.delete(follower_qs.scalars().one())

        followers = [follower for follower in followers if follower.follower_id != users[2].id]

        follower_qs = await db_session.execute(
            select(models.Follower).where(models.Follower.user_id == users[0].id)
        )
        assert len(follower_qs.scalars().all()) == len(followers)

        # удаляем пользователя, на которого подписаны
        following_qs = await db_session.execute(
            select(models.Follower).where(models.Follower.user_id == users[0].id)
        )
        await db_session.delete(following_qs.scalars().one())

        follower_qs = await db_session.execute(
            select(models.Follower).where(models.Follower.user_id == users[0].id)
        )
        assert len(follower_qs.scalars().all()) == 0


@pytest.mark.anyio
async def test_cannot_follow_for_self(db_session):
    """Проверка, что нельзя подписываться на себя же."""
    user = models.User(
        nickname="testtest",
        api_key="a" * 30,
    )
    db_session.add(user)
    await db_session.commit()

    with pytest.raises(IntegrityError, match=r".*CheckViolationError.*"):
        new_follower = models.Follower(
            user_id=user.id,
            follower_id=user.id
        )
        db_session.add(new_follower)
        await db_session.commit()


@pytest.mark.anyio
async def test_cannot_follow_twice(db_session):
    """Проверка, что один пользователь не может подписываться еще раз
    на пользователя, на которого он уже подписан."""
    users = [
        models.User(nickname="test1", api_key="a" * 30),
        models.User(nickname="test2", api_key="b" * 30),
    ]
    db_session.add_all(users)
    await db_session.commit()

    follow_once = models.Follower(
        user_id=users[0].id,
        follower_id=users[1].id,
    )
    db_session.add(follow_once)
    await db_session.commit()

    follow_twice = models.Follower(
        user_id=users[0].id,
        follower_id=users[1].id,
    )
    with pytest.raises(IntegrityError, match=r".*UniqueViolationError.*"):
        db_session.add(follow_twice)
        await db_session.commit()
