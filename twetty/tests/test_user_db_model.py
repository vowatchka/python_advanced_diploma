import pytest
from sqlalchemy import inspect, select
from sqlalchemy.exc import IntegrityError

from .utils import table_exists, generate_test_models
from ..db import models


@pytest.mark.anyio
async def test_add_user(db_session):
    """Проверка добавления нового пользователя."""
    new_user = models.User(
        nickname="test1",
        first_name="first name",
        last_name="last name",
        api_key="a" * 30,
    )
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
