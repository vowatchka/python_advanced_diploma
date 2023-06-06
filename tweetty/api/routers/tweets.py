import os
from pathlib import Path as OsPath
from typing import Annotated

from fastapi import APIRouter, Depends, Path
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...db import models
from ..auth import get_authorized_user
from ..exceptions import HTTP_403_FORBIDDEN_DESC, HTTP_500_INTERNAL_SERVER_ERROR_DESC, ForbiddenError, http_exception
from ..models import HTTPErrorModel, NewTweetIn, NewTweetOut, ResultModel

tweets_router = APIRouter(prefix="/tweets")
_tags = ["tweets"]


@tweets_router.post(
    "",
    summary="Опубликовать новый твит",
    response_model=NewTweetOut,
    status_code=201,
    tags=_tags,
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
        500: {"model": HTTPErrorModel, "description": HTTP_500_INTERNAL_SERVER_ERROR_DESC},
    },
    tags=_tags,
)
async def delete_tweet(
    db_session: Annotated[AsyncSession, Depends(models.db_session)],
    auth_user: Annotated[models.User, Depends(get_authorized_user)],
    tweet_id: Annotated[int, Path(description="Id твита")],
) -> ResultModel:
    """Удаление твита."""
    async with db_session.begin_nested():
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
                    ForbiddenError(f"User {auth_user.nickname} can't delete someone else tweet"),
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
