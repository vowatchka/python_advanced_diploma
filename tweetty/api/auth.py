from typing import Annotated

from fastapi import Depends, HTTPException, Security
from fastapi.openapi.models import APIKey
from fastapi.security import APIKeyHeader
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import models

api_key_header = APIKeyHeader(
    name="api-key",
    scheme_name="API-Key",
    description="Ключ авторизации пользователя",
    auto_error=False,
)


async def get_api_key(api_key: Annotated[str, Security(api_key_header)]) -> str:
    """Возвращает ключ авторизации пользователя."""
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="Missed APIKey header"
        )
    return api_key


async def get_authorized_user(
    api_key: Annotated[APIKey, Depends(get_api_key)],
    db_session: Annotated[AsyncSession, Depends(models.db_session)],
) -> models.User:
    """Возвращает пользователя по ключу авторизации."""
    user_qs = await db_session.execute(
        select(models.User).where(models.User.api_key == api_key)
    )
    user: models.User = user_qs.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=401,
            detail="No user with such APIKey"
        )
    return user
