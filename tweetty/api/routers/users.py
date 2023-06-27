from typing import Annotated, Optional, Union

from fastapi import APIRouter, Depends, Path, Response
from fastapi.responses import RedirectResponse
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...db import models
from ...shortcuts import get_object_or_none
from ..auth import get_authorized_user
from ..exceptions import (HTTP_406_NOT_ACCEPTABLE_DESC, HTTP_500_INTERNAL_SERVER_ERROR_DESC, NotAcceptableError,
                          NotFoundError, http_exception,)
from ..models import HTTPErrorModel, ResultModel, UserResultOut

users_router = APIRouter(
    prefix="/users",
    responses={
        500: {"model": HTTPErrorModel, "description": HTTP_500_INTERNAL_SERVER_ERROR_DESC},
    },
)

users_tags = ["users"]
follows_tags = users_tags + ["follows"]

UserId = Annotated[int, Path(description="Id пользователя")]


class UserGetter:
    def __init__(self, full_user: bool = False, raise_404: bool = False):
        """
        Получатель пользователя.

        :param full_user: получить все данные о пользователе.
        :param raise_404: возбуждать `404 Not Found` или нет.
        """
        self._full_user = full_user
        self._raise_404 = raise_404

    async def __call__(self, db_session: Annotated[AsyncSession, Depends(models.db_session)],
                       user_id: UserId) -> Optional[models.User]:
        if not self._full_user:
            user = await get_object_or_none(db_session, models.User, models.User.id == user_id)
        else:
            user_qs = await db_session.execute(
                select(models.User)
                .where(models.User.id == user_id)
                .options(
                    selectinload(models.User.followers).options(selectinload(models.Follower.follower)),
                    selectinload(models.User.followings).options(selectinload(models.Follower.user)),
                )
            )
            user = user_qs.scalar_one_or_none()

        if self._raise_404 and user is None:
            raise http_exception(NotFoundError(f"user {user_id} doesn't exist"), status_code=404)
        return user


async def get_following_or_none(
    db_session: Annotated[AsyncSession, Depends(models.db_session)],
    auth_user: Annotated[models.User, Depends(get_authorized_user)],
    user: Annotated[models.User, Depends(UserGetter(raise_404=True))],
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


@users_router.get(
    "/me",
    summary="Получить собственный профиль пользователя",
    status_code=200,
    response_model=UserResultOut,
    response_description="Success",
    tags=users_tags
)
async def get_me(
    db_session: Annotated[AsyncSession, Depends(models.db_session)],
    auth_user: Annotated[models.User, Depends(get_authorized_user)],
) -> UserResultOut:
    """Получить собственный профиль пользователя."""
    user_getter = UserGetter(full_user=True, raise_404=True)

    return UserResultOut(
        result=True,
        user=await user_getter(db_session, auth_user.id),
    )


@users_router.get(
    "/{user_id}",
    summary="Получить профиль пользователя",
    status_code=200,
    response_model=UserResultOut,
    response_description="Success",
    responses={
        308: {"description": "Permanent Redirect"},
        404: {"model": HTTPErrorModel, "description": "User Not Found"},
    },
    tags=users_tags,
)
async def get_user(
    auth_user: Annotated[models.User, Depends(get_authorized_user)],  # `auth_user` нужен, чтобы 401 срабатывал раньше
    user: Annotated[models.User, Depends(UserGetter(full_user=True, raise_404=True))],
    user_id: UserId,
) -> Union[RedirectResponse, UserResultOut]:
    """Получить профиль пользователя."""
    if user_id == auth_user.id:
        return RedirectResponse("/api" + users_router.url_path_for(get_me.__name__), status_code=308)

    return UserResultOut(
        result=True,
        user=user,
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


@users_router.delete(
    "/{user_id}/follow",
    summary="Отписаться от пользователя",
    status_code=200,
    response_model=ResultModel,
    response_description="User Unfollowed",
    responses={
        404: {"model": HTTPErrorModel, "description": "User Not Found"},
    },
    tags=follows_tags,
)
async def unfollow_user(
    db_session: Annotated[AsyncSession, Depends(models.db_session)],
    following: Annotated[Optional[models.Follower], Depends(get_following_or_none)],
) -> ResultModel:
    """Отписаться от пользователя."""
    if following is not None:
        await db_session.delete(following)
        await db_session.commit()

    return ResultModel(result=True)
