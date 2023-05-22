from urllib.parse import urlparse

from environs import Env

env = Env()
POSTGRES_URL = env("POSTGRES_URL")


def make_async_postgres_url(pg_uri: str) -> str:
    """
    Создает из переданного URI асинхронный URI
    для подключения к PostgreSQL.

    :param pg_url: URI для подключения к PostgreSQL.
    """
    parsed_uri = urlparse(pg_uri)
    async_uri = parsed_uri._replace(scheme="postgresql+asyncpg")
    return async_uri.geturl()


def change_database_name(pg_uri: str, db_name: str) -> str:
    """
    Изменяет в переданном URI имя БД на указанное.

    :param pg_uri: URI для подключения к PostgreSQL.
    :param db_name: имя БД.
    """
    parsed_uri = urlparse(pg_uri)
    new_uri = parsed_uri._replace(path=f"/{db_name}")
    return new_uri.geturl()
