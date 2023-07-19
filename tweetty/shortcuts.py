from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .api.exceptions import NotFoundError, http_exception
from .typing import SAModelObject


async def get_object_or_none(db_session: AsyncSession, model: type[SAModelObject], *whereclause: Any) -> SAModelObject:
    """Возвращает объект записи в БД или `None."""
    stmt = select(model)
    if whereclause:
        stmt = stmt.where(*whereclause)

    object_qs = await db_session.execute(stmt)
    return object_qs.scalar_one_or_none()


async def get_object_or_404(
    db_session: AsyncSession, model: type[SAModelObject], *whereclause: Any, message_404: Optional[str] = None
) -> SAModelObject:
    """Возвращает объект записи в БД или возбуждает исключение `404 Not Found`."""
    obj = await get_object_or_none(db_session, model, *whereclause)
    if obj is None:
        if message_404 is None:
            message_404 = "not found"
        raise http_exception(NotFoundError(message_404), status_code=404)

    return obj
