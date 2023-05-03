import pytest
from sqlalchemy import inspect, select
from sqlalchemy.exc import IntegrityError

from .utils import table_exists, generate_test_models
from ..db import models


@pytest.mark.anyio
async def test_table_user_exist(engine):
    """Проверка создания таблицы user."""
    assert await table_exists(engine, "user")


@pytest.mark.anyio
@pytest.mark.parametrize(
    "new_user",
    [
        models.User(nickname="test_user1", api_key="a" * 30),
        models.User(nickname="test_user2", first_name="First Name", api_key="a" * 30),
        models.User(nickname="test_user3", last_name="Last Name", api_key="a" * 30),
        models.User(nickname="test_user4", first_name="Full Name", last_name="Full Name", api_key="a" * 30),
    ],
)
async def test_add_user(db_session, new_user):
    """Проверка добавления нового пользователя."""
    db_session.add(new_user)
    await db_session.commit()

    queryset = await db_session.execute(
        select(models.User).where(models.User.id == new_user.id)
    )
    added_user: models.User = queryset.scalars().one()
    assert added_user.id is not None
    assert added_user.nickname == new_user.nickname
    assert added_user.first_name == new_user.first_name
    assert added_user.last_name == new_user.last_name
    assert added_user.api_key == new_user.api_key


@pytest.mark.anyio
async def test_nickname_not_null(db_session):
    """Проверка наличия ограничения NOT NULL поля nickname."""
    with pytest.raises(IntegrityError, match=r'.*NotNullViolationError.*'):
        db_session.add(
            models.User(nickname=None, api_key="a" * 30),
        )
        await db_session.commit()


@pytest.mark.anyio
async def test_nickname_unique(db_session):
    """Проверка наличия ограничения UNIQUE поля nickname."""
    with pytest.raises(IntegrityError, match=r'.*UniqueViolationError.*'):
        db_session.add(
            models.User(nickname="predefined_test_user", api_key="a" * 30),
        )
        await db_session.commit()


@pytest.mark.anyio
@pytest.mark.parametrize(
    "new_user",
    [
        # короткий nickname
        *generate_test_models(models.User, range(5), nickname=lambda count: "t" * count, api_key="a" * 30),
        # длинный nickname
        *generate_test_models(models.User, range(21, 27), nickname=lambda count: "t" * count, api_key="a" * 30),
    ],
)
async def test_nickname_length(db_session, new_user):
    """Проверка наличия ограничений по длине поля nickname."""
    with pytest.raises(IntegrityError, match=r'.*CheckViolationError.*'):
        db_session.add(new_user)
        await db_session.commit()


@pytest.mark.anyio
@pytest.mark.parametrize(
    "new_user",
    [
        # короткое имя
        models.User(nickname="test1", first_name="", api_key="a" * 30),
        # длинное имя
        *generate_test_models(
            models.User,
            range(101, 107),
            nickname="test1",
            first_name=lambda count: "a" * count,
            api_key="a" * 30,
        ),
    ],
)
async def test_first_name_length(db_session, new_user):
    """Проверка наличия ограничений по длине поля first_name."""
    with pytest.raises(IntegrityError, match=r'.*CheckViolationError.*'):
        db_session.add(new_user)
        await db_session.commit()


@pytest.mark.anyio
@pytest.mark.parametrize(
    "new_user",
    [
        # короткая фимилия
        models.User(nickname="test1", last_name="", api_key="a" * 30),
        # длинная фамилия
        *generate_test_models(
            models.User,
            range(101, 107),
            nickname="test1",
            last_name=lambda count: "a" * count,
            api_key="a" * 30,
        ),
    ],
)
async def test_last_name_length(db_session, new_user):
    """Проверка наличия ограничений по длине поля last_name."""
    with pytest.raises(IntegrityError, match=r'.*CheckViolationError.*'):
        db_session.add(new_user)
        await db_session.commit()


@pytest.mark.anyio
async def test_api_key_not_null(db_session):
    """Проверка наличия ограничения NOT NULL поля api_key."""
    with pytest.raises(IntegrityError, match=r'.*NotNullViolationError.*'):
        db_session.add(
            models.User(nickname="test1", api_key=None),
        )
        await db_session.commit()


@pytest.mark.anyio
async def test_api_key_unique(db_session):
    """Проверка наличия ограничения UNIQUE поля api_key."""
    with pytest.raises(IntegrityError, match=r'.*UniqueViolationError.*'):
        db_session.add(
            models.User(nickname="test1", api_key="test" * 20),
        )
        await db_session.commit()


@pytest.mark.anyio
@pytest.mark.parametrize(
    "new_user",
    [
        # короткий api_key
        *generate_test_models(models.User, range(6), nickname="test1", api_key=lambda count: "a" * count),
        *generate_test_models(models.User, range(23, 30), nickname="test1", api_key=lambda count: "a" * count),
        # длинный api_key
        *generate_test_models(models.User, range(257, 263), nickname="test1", api_key=lambda count: "a" * count),
    ],
)
async def test_api_key_length(db_session, new_user):
    """Проверка наличия ограничений по длине поля api_key."""
    with pytest.raises(IntegrityError, match=r'.*CheckViolationError.*'):
        db_session.add(new_user)
        await db_session.commit()
