import os
from pathlib import Path as OsPath
from typing import Annotated

from fastapi import APIRouter, Depends, Path, Response
from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...db import models
from ..auth import get_authorized_user
from ..exceptions import (HTTP_403_FORBIDDEN_DESC, HTTP_500_INTERNAL_SERVER_ERROR_DESC, ForbiddenError, TweetNotFound,
                          http_exception,)
from ..models import HTTPErrorModel, NewTweetIn, NewTweetOut, ResultModel

tweets_router = APIRouter(
    prefix="/tweets",
    responses={
        500: {"model": HTTPErrorModel, "description": HTTP_500_INTERNAL_SERVER_ERROR_DESC},
    },
)
tweets_tags = ["tweets"]
likes_tags = tweets_tags + ["likes"]


@tweets_router.post(
    "",
    summary="Опубликовать новый твит",
    status_code=201,
    response_model=NewTweetOut,
    tags=tweets_tags,
)
async def publish_new_tweet(
    db_session: Annotated[AsyncSession, Depends(models.db_session)],
    auth_user: Annotated[models.User, Depends(get_authorized_user)],
    new_tweet_body: NewTweetIn,
) -> NewTweetOut:
    """Публикация нового твита."""
    async with db_session.begin_nested():
        new_tweet = models.Tweet(
            **new_tweet_body.dict(),
            user_id=auth_user.id,
        )
        db_session.add(new_tweet)
        await db_session.flush([new_tweet])

        # связываем переданные медиа с твитом
        await db_session.execute(
            update(models.TweetMedia)
            .where(models.TweetMedia.id.in_(new_tweet_body.medias))
            .values(tweet_id=new_tweet.id)
        )

    return NewTweetOut(result=True, tweet_id=new_tweet.id)


@tweets_router.delete(
    "/{tweet_id}",
    summary="Удалить твит",
    status_code=200,
    response_model=ResultModel,
    responses={
        403: {"model": HTTPErrorModel, "description": HTTP_403_FORBIDDEN_DESC},
    },
    tags=tweets_tags,
)
async def delete_tweet(
    db_session: Annotated[AsyncSession, Depends(models.db_session)],
    auth_user: Annotated[models.User, Depends(get_authorized_user)],
    tweet_id: Annotated[int, Path(description="Id твита")],
) -> ResultModel:
    """Удаление твита."""
    tweet_qs = await db_session.execute(
        select(models.Tweet)
        .where(models.Tweet.id == tweet_id)
        .options(selectinload(models.Tweet.medias))
    )
    tweet: models.Tweet = tweet_qs.scalar_one_or_none()

    # пытаемся удалить твит, если он существует
    if tweet is not None:
        # запрет на удаление чужого твита
        if tweet.user_id != auth_user.id:
            raise http_exception(
                ForbiddenError(f"user {auth_user.nickname} can't delete someone else tweet"),
                status_code=403,
            )

        # получаем пути до медиа, прикрепленных к удаляемому твиту
        media_file_paths = [OsPath(media.rel_uri).resolve() for media in tweet.medias]
        # удаляем твит
        await db_session.delete(tweet)

        # удаляем медиа
        for file_path in media_file_paths:
            if file_path.exists():
                os.remove(file_path)

    # если твит отсутствует, то все равно возвращает `True`,
    # чтобы соблюсти идемпотентность метода DELETE
    return ResultModel(result=True)


@tweets_router.post(
    "/{tweet_id}/likes",
    summary="Поставить лайк",
    status_code=201,
    response_model=ResultModel,
    responses={
        200: {"model": ResultModel, "description": "Already Liked"},
        404: {"model": HTTPErrorModel, "description": "Tweet Not Found"},
    },
    tags=likes_tags,
)
async def like_tweet(
    db_session: Annotated[AsyncSession, Depends(models.db_session)],
    auth_user: Annotated[models.User, Depends(get_authorized_user)],
    tweet_id: Annotated[int, Path(description="Id твита")],
    response: Response,
) -> ResultModel:
    """Поставить лайк."""
    tweet_qs = await db_session.execute(
        select(models.Tweet).where(models.Tweet.id == tweet_id)
    )
    tweet = tweet_qs.scalar_one_or_none()
    if tweet is None:
        # попытка лайкнуть несуществующий твит
        raise http_exception(TweetNotFound(f"tweet {tweet_id} doesn't exist"), status_code=404)

    like_qs = await db_session.execute(
        select(models.Like)
        .where(
            and_(
                models.Like.tweet_id == tweet_id,
                models.Like.user_id == auth_user.id
            )
        )
    )
    like = like_qs.scalar_one_or_none()

    if like is not None:
        # если пользователь уже лайкал этот твит
        response.status_code = 200
    else:
        # если не лайкал, то ставим лайк
        new_like = models.Like(
            tweet_id=tweet_id,
            user_id=auth_user.id
        )
        db_session.add(new_like)
        await db_session.commit()

    return ResultModel(result=True)
