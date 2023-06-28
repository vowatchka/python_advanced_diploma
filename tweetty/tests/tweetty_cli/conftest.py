import pytest
from sqlalchemy import NullPool, create_engine
from sqlalchemy.orm import Session, sessionmaker

from ...db import models

TestSession = sessionmaker()


@pytest.fixture(scope="session")
def engine(database_for_tests: str):
    test_engine = create_engine(
        database_for_tests,
        # https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html#using-multiple-asyncio-event-loops
        poolclass=NullPool,
    )

    # создаем таблицы
    with test_engine.begin() as conn:
        models.Base.metadata.create_all(conn)

    yield test_engine

    # удаляем таблицы
    with test_engine.begin() as conn:
        models.Base.metadata.drop_all(conn)

    test_engine.dispose()


@pytest.fixture
def conn(engine):
    with engine.begin() as conn:
        yield conn
        conn.close()


@pytest.fixture
def db_session(conn):
    with TestSession(bind=conn) as test_session:
        yield test_session
        test_session.rollback()
        test_session.close()


@pytest.fixture
def test_user(db_session: Session):
    """Тестовый пользователь."""
    user = models.User(
        nickname="test1",
        api_key="a" * 30
    )
    db_session.add(user)
    db_session.commit()

    yield user


@pytest.fixture
def followed_user(db_session: Session):
    """Тестовый пользователь, на которого подписываются."""
    user = models.User(
        nickname="Followed User",
        api_key="f" * 30,
    )
    db_session.add(user)
    db_session.commit()

    yield user
