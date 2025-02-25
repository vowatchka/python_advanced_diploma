import pytest
import sqlalchemy_utils as sautils
from httpx import AsyncClient
from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from ..api import create_api
from ..api.routers import medias as media_routers
from ..db import models, pg
from ..settings import POSTGRES_URL
from .api import api_client  # noqa: F401
from .api.test_follows import followed_user  # noqa: F401
from .api.test_medias import generate_mediafile_name, test_file, test_file_uploaded_path  # noqa: F401
from .api.test_tweets import test_tweet  # noqa: F401

TestSession = sessionmaker(expire_on_commit=False, class_=AsyncSession)


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session")
def database_for_tests():
    test_pg_uri = pg.change_database_name(POSTGRES_URL, "test")

    # создаем тестовую БД
    if not sautils.database_exists(test_pg_uri):
        sautils.create_database(test_pg_uri)

    yield test_pg_uri

    # удаляем тестовую БД
    if sautils.database_exists(test_pg_uri):
        sautils.drop_database(test_pg_uri)


@pytest.fixture(scope="session")
async def engine(anyio_backend, database_for_tests: str):
    test_db = pg.change_database_name(POSTGRES_URL, "test")
    async_test_pg_uri = pg.make_async_postgres_url(test_db)

    test_engine = create_async_engine(
        async_test_pg_uri,
        # https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html#using-multiple-asyncio-event-loops
        poolclass=NullPool,
    )

    # создаем таблицы
    async with test_engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)

    yield test_engine

    # удаляем таблицы
    async with test_engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.drop_all)

    await test_engine.dispose()


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


@pytest.fixture
def api(db_session):
    _api = create_api()

    _api.dependency_overrides[models.db_session] = lambda: db_session
    _api.dependency_overrides[media_routers.generate_mediafile_name] = generate_mediafile_name

    yield _api


@pytest.fixture
async def client(api):
    # Использование fastapi.TestClient приводило к исключению:
    # RuntimeError: Task <Task pending name='anyio.from_thread.BlockingPortal._call_func'
    #   coro=<BlockingPortal._call_func()
    #   running at /usr/local/lib/python3.9/site-packages/anyio/from_thread.py:219>
    #   cb=[TaskGroup._spawn.<locals>.task_done()
    #   at /usr/local/lib/python3.9/site-packages/anyio/_backends/_asyncio.py:726]>
    #   got Future <Future pending cb=[Protocol._on_waiter_completed()]> attached to a different loop
    #
    # Из возможных решений были:
    #   1. В фикстуре, создающей сессию БД (db_session), делать bind не на подключение (conn),
    #      а на движок (engine), но в этом случае не работает rollback после каждого теста,
    #      потому что нет открытой транзакции (см. поведение в sqlalchemy.orm.session.Session::rollback).
    #   2. Понизить версию fastapi до 0.68.2
    #      (см. https://github.com/encode/starlette/issues/1315#issuecomment-965098142).
    #      Это действительно устраняло проблему, но рано или поздно версию придется повысить
    #      и опять столкнуться с проблемой.
    #   3. Использовать httpx.AsyncClient (см. https://fastapi.tiangolo.com/advanced/async-tests/#httpx)
    async with AsyncClient(app=api, base_url="http://testserver") as test_client:
        yield test_client


@pytest.fixture
async def test_user(db_session: AsyncSession):
    """Тестовый пользователь."""
    user = models.User(nickname="test1", api_key="a" * 30)
    db_session.add(user)
    await db_session.commit()

    yield user
