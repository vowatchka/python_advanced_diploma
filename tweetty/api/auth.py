from typing import Annotated

from fastapi import Depends, Security
from fastapi.openapi.models import APIKey
from fastapi.security import APIKeyHeader
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import models
from .exceptions import UnauthorizedError, http_exception

api_key_header = APIKeyHeader(
    name="api-key",
    scheme_name="API-Key",
    description="Ключ авторизации пользователя",
    auto_error=False,
)


async def get_api_key(api_key: Annotated[str, Security(api_key_header)]) -> str:
    """Возвращает ключ авторизации пользователя."""
    if not api_key:
        raise http_exception(UnauthorizedError("Missed APIKey header"), status_code=401)
    return api_key


async def get_authorized_user(
    api_key: Annotated[APIKey, Depends(get_api_key)],
    db_session: Annotated[AsyncSession, Depends(models.db_session)],
) -> models.User:
    """Возвращает пользователя по ключу авторизации."""
    # фикс для интеграции с фронтом
    # в БД должен быть заранее создан пользователь с указанным api_key
    if api_key == "test":
        api_key = "t" * 30

    user_qs = await db_session.execute(select(models.User).where(models.User.api_key == api_key))
    user: models.User = user_qs.scalar_one_or_none()

    if not user:
        raise http_exception(UnauthorizedError("No user with such APIKey"), status_code=401)
    return user
