import pytest

from ...db.pg import change_database_name, make_async_postgres_url

pytestmark = [pytest.mark.db]


def test_make_async_postgres_url():
    """Проверка функции make_async_postgres_url."""
    sync_schema = "postgresql"
    async_schema = f"{sync_schema}+asyncpg"
    pg_uri = "://test:test@test:5432/test"
    assert make_async_postgres_url(f"{sync_schema}{pg_uri}") == f"{async_schema}{pg_uri}"


def test_change_database_name():
    """Проверка функции change_database_name."""
    pg_uri = "postgresql://test:test@test:5432/"
    db_name = "test"
    new_db_name = "new_test"
    assert change_database_name(f"{pg_uri}{db_name}", new_db_name) == f"{pg_uri}{new_db_name}"
