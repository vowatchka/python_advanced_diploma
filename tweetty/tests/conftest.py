import pytest
import sqlalchemy_utils as sautils
from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from ..db import models, pg

TestSession = sessionmaker(expire_on_commit=False, class_=AsyncSession)


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session")
async def engine(anyio_backend):
    test_pg_uri = pg.change_database_name(pg.POSTGRES_URL, "test")
    async_test_pg_uri = pg.make_async_postgres_url(test_pg_uri)

    # создаем тестовую БД
    if not sautils.database_exists(test_pg_uri):
        sautils.create_database(test_pg_uri)

    test_engine = create_async_engine(
        async_test_pg_uri,
        # https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html#using-multiple-asyncio-event-loops
        poolclass=NullPool,
    )

    # создаем таблицы
    async with test_engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)

    # наполняем таблицы начальными данными
    async with TestSession(bind=test_engine) as session:
        # пользователи
        session.add_all(
            [
                models.User(
                    nickname="predefined_test_user",
                    api_key="test1" * 20,
                ),
                models.User(
                    nickname="user_with_tweets",
                    api_key="test2" * 20,
                ),
                models.User(
                    nickname="user_with_medias",
                    api_key="test3" * 20,
                ),
                models.User(
                    nickname="liker",
                    api_key="test4" * 20
                ),
            ]
        )
        await session.commit()

        # твиты
        session.add_all(
            [
                models.Tweet(
                    content="tweet",
                    user_id=3,
                ),
                models.Tweet(
                    content="tweet with likes",
                    user_id=3
                ),
            ]
        )
        await session.commit()

    yield test_engine

    # удаляем таблицы
    async with test_engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.drop_all)

    await test_engine.dispose()
    # удаляем тестовую БД
    if sautils.database_exists(test_pg_uri):
        sautils.drop_database(test_pg_uri)


@pytest.fixture
async def conn(engine):
    async with engine.begin() as conn:
        yield conn
        await conn.close()


@pytest.fixture
async def db_session(conn):
    async with TestSession(bind=conn) as test_session:
        yield test_session
        await test_session.rollback()
        await test_session.close()