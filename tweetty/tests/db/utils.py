from collections.abc import Generator, Iterable

from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import AsyncEngine


async def table_exists(engine: AsyncEngine, table_name: str) -> bool:
    """
    Проверяет наличие таблицы с именем `table_name`.

    :param engine: асинхронный движок SQLAlchemy.
    :param table_name: имя таблицы.
    """
    async with engine.begin() as conn:
        is_exists = await conn.run_sync(lambda sync_engine: inspect(sync_engine).has_table(table_name))
        return is_exists


def generate_test_models(sa_model: type, iterable: Iterable, **kwargs) -> Generator[type, None, None]:
    """
    Генерирует модели SQLAlchemy.

    :param sa_model: класс модели SQLAlchemy.
    :param iterable: итерируемый объект, элементы которого будут
        передаваться в функции, генерирующие данные для полей
        модели `sa_model`.
    :param kwargs: каждый `kwarg` должен быть представлен фиксированным
        значением или функцией, принимающей один аргумент и возвращающей
        некоторые данные. В функцию будут передаваться элементы `iterable`.
    """
    for item in iterable:
        yield sa_model(
            **{
                attr_name: func_or_fixed(item) if callable(func_or_fixed) else func_or_fixed
                for attr_name, func_or_fixed in kwargs.items()
                if hasattr(sa_model, attr_name)
            }
        )
