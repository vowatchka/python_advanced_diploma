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
        session.add_all(
            [
                models.User(
                    nickname="predefined_test_user",
                    api_key="test" * 20,
                ),
                models.User(
                    nickname="tweeter_user",
                    api_key="tweeter_user" * 20,
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
        await test_session.close()


@pytest.fixture
async def rollbacked_db_session(db_session):
    yield db_session
    await db_session.rollback()


@pytest.fixture
async def not_rollbacked_db_session(db_session):
    yield db_session
