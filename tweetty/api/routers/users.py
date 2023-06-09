from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Path, Response
from sqlalchemy import and_
from sqlalchemy.ext.asyncio import AsyncSession

from ...db import models
from ...shortcuts import get_object_or_none
from ..auth import get_authorized_user
from ..exceptions import (HTTP_406_NOT_ACCEPTABLE_DESC, HTTP_500_INTERNAL_SERVER_ERROR_DESC, NotAcceptableError,
                          NotFoundError, http_exception,)
from ..models import HTTPErrorModel, ResultModel

users_router = APIRouter(
    prefix="/users",
    responses={
        500: {"model": HTTPErrorModel, "description": HTTP_500_INTERNAL_SERVER_ERROR_DESC},
    },
)

users_tags = ["users"]
follows_tags = users_tags + ["follows"]

UserId = Annotated[int, Path(description="Id пользователя")]


async def get_user_or_none(db_session: Annotated[AsyncSession, Depends(models.db_session)],
                           user_id: UserId) -> Optional[models.User]:
    """Возвращает пользователя или `None`."""
    return await get_object_or_none(
        db_session,
        models.User,
        models.User.id == user_id
    )


async def get_user_or_404(user: Annotated[Optional[models.User], Depends(get_user_or_none)],
                          user_id: UserId) -> models.User:
    """Возвращает пользователя или возбуждает `404 Not Found`, если пользователя нет."""
    if user is None:
        raise http_exception(NotFoundError(f"user {user_id} doesn't exist"), status_code=404)
    return user


async def get_following_or_none(
    db_session: Annotated[AsyncSession, Depends(models.db_session)],
    user: Annotated[models.User, Depends(get_user_or_404)],
    auth_user: Annotated[models.User, Depends(get_authorized_user)]
) -> Optional[models.Follower]:
    """Возвращает подписку одного пользователя на другого или `None`."""
    return await get_object_or_none(
        db_session,
        models.Follower,
        and_(
            models.Follower.user_id == user.id,
            models.Follower.follower_id == auth_user.id
        )
    )


@users_router.post(
    "/{user_id}/follow",
    summary="Подписаться на пользователя",
    status_code=201,
    response_model=ResultModel,
    response_description="User Followed",
    responses={
        200: {"model": ResultModel, "description": "Already Followed"},
        404: {"model": HTTPErrorModel, "description": "User Not Found"},
        406: {"model": HTTPErrorModel, "description": HTTP_406_NOT_ACCEPTABLE_DESC},
    },
    tags=follows_tags,
)
async def follow_user(
    db_session: Annotated[AsyncSession, Depends(models.db_session)],
    auth_user: Annotated[models.User, Depends(get_authorized_user)],
    user_id: UserId,
    following: Annotated[Optional[models.Follower], Depends(get_following_or_none)],
    response: Response,
) -> ResultModel:
    """Подписаться на пользователя."""
    if user_id == auth_user.id:
        # подписаться на себя же нельзя
        raise http_exception(
            NotAcceptableError("following to himself is not acceptable"),
            status_code=406
        )
    elif following is not None:
        # пользователь уже подписан на запрошенного пользователя
        response.status_code = 200
    else:
        # подписываем одного пользователя на другого
        following = models.Follower(
            user_id=user_id,
            follower_id=auth_user.id
        )
        db_session.add(following)
        await db_session.commit()

    return ResultModel(result=True)
