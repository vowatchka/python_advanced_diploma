import os
from pathlib import Path as OsPath
from typing import Annotated, Optional, Sequence

from fastapi import APIRouter, Depends, Path, Query, Response
from sqlalchemy import Select, and_, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased, selectinload

from ...db import models
from ...shortcuts import get_object_or_none
from ..auth import get_authorized_user
from ..exceptions import (
    HTTP_403_FORBIDDEN_DESC,
    HTTP_500_INTERNAL_SERVER_ERROR_DESC,
    ForbiddenError,
    NotFoundError,
    http_exception,
)
from ..models import HTTPErrorModel, NewTweetIn, NewTweetOut, ResultModel, TweetListOut

tweets_router = APIRouter(
    prefix="/tweets",
    responses={
        500: {"model": HTTPErrorModel, "description": HTTP_500_INTERNAL_SERVER_ERROR_DESC},
    },
)
tweets_tags = ["tweets"]
likes_tags = tweets_tags + ["likes"]

TweetId = Annotated[int, Path(description="Id твита")]


async def get_tweet_or_none(
    db_session: Annotated[AsyncSession, Depends(models.db_session)], tweet_id: TweetId
) -> Optional[models.Tweet]:
    """Возвращает твит или `None`."""
    return await get_object_or_none(db_session, models.Tweet, models.Tweet.id == tweet_id)


async def get_tweet_or_404(
    tweet: Annotated[Optional[models.Tweet], Depends(get_tweet_or_none)], tweet_id: TweetId
) -> models.Tweet:
    """Возвращает твит или возбуждает `404 Not Found`, если твита нет."""
    if tweet is None:
        raise http_exception(NotFoundError(f"tweet {tweet_id} doesn't exist"), status_code=404)
    return tweet


async def get_like_or_none(
    db_session: Annotated[AsyncSession, Depends(models.db_session)],
    tweet: Annotated[models.Tweet, Depends(get_tweet_or_404)],
    auth_user: Annotated[models.User, Depends(get_authorized_user)],
) -> Optional[models.Like]:
    """Возвращает лайк или `None`."""
    return await get_object_or_none(
        db_session, models.Like, and_(models.Like.tweet_id == tweet.id, models.Like.user_id == auth_user.id)
    )


@tweets_router.post(
    "",
    summary="Опубликовать новый твит",
    status_code=201,
    response_model=NewTweetOut,
    response_description="Tweet Created",
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
            .where(models.TweetMedia.id.in_(set(new_tweet_body.medias)))
            .values(tweet_id=new_tweet.id)
        )

        await db_session.commit()

    return NewTweetOut(result=True, tweet_id=new_tweet.id)


@tweets_router.delete(
    "/{tweet_id}",
    summary="Удалить твит",
    status_code=200,
    response_model=ResultModel,
    response_description="Tweet Deleted",
    responses={
        403: {"model": HTTPErrorModel, "description": HTTP_403_FORBIDDEN_DESC},
    },
    tags=tweets_tags,
)
async def delete_tweet(
    db_session: Annotated[AsyncSession, Depends(models.db_session)],
    auth_user: Annotated[models.User, Depends(get_authorized_user)],
    tweet: Annotated[Optional[models.Tweet], Depends(get_tweet_or_none)],
) -> ResultModel:
    """Удаление твита."""
    # пытаемся удалить твит, если он существует
    if tweet is not None:
        # запрет на удаление чужого твита
        if tweet.user_id != auth_user.id:
            raise http_exception(
                ForbiddenError(f"user {auth_user.nickname} can't delete someone else tweet"),
                status_code=403,
            )

        # получаем пути до медиа, прикрепленных к удаляемому твиту
        await db_session.refresh(tweet, attribute_names=["medias"])
        media_file_paths = [OsPath(media.rel_uri).resolve() for media in tweet.medias]

        # удаляем твит
        await db_session.delete(tweet)
        await db_session.commit()

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
    response_description="Tweet Liked",
    responses={
        200: {"model": ResultModel, "description": "Already Liked"},
        404: {"model": HTTPErrorModel, "description": "Tweet Not Found"},
    },
    tags=likes_tags,
)
async def like_tweet(
    db_session: Annotated[AsyncSession, Depends(models.db_session)],
    auth_user: Annotated[models.User, Depends(get_authorized_user)],
    tweet_id: TweetId,
    like: Annotated[Optional[models.Like], Depends(get_like_or_none)],
    response: Response,
) -> ResultModel:
    """Поставить лайк."""
    if like is not None:
        # если пользователь уже лайкал этот твит
        response.status_code = 200
    else:
        # если не лайкал, то ставим лайк
        new_like = models.Like(tweet_id=tweet_id, user_id=auth_user.id)
        db_session.add(new_like)
        await db_session.commit()

    return ResultModel(result=True)


@tweets_router.delete(
    "/{tweet_id}/likes",
    summary="Убрать лайк",
    status_code=200,
    response_model=ResultModel,
    response_description="Tweet Unliked",
    responses={
        404: {"model": HTTPErrorModel, "description": "Tweet Not Found"},
    },
    tags=likes_tags,
)
async def unlike_tweet(
    db_session: Annotated[AsyncSession, Depends(models.db_session)],
    auth_user: Annotated[models.User, Depends(get_authorized_user)],  # `auth_user` нужен, чтобы 401 срабатывал раньше
    like: Annotated[Optional[models.Like], Depends(get_like_or_none)],
) -> ResultModel:
    """Убрать лайк."""
    if like is not None:
        await db_session.delete(like)
        await db_session.commit()

    # если лайк отсутствует, то все равно возвращает `True`,
    # чтобы соблюсти идемпотентность метода DELETE
    return ResultModel(result=True)


@tweets_router.get(
    "",
    summary="Получить ленту твитов пользователя",
    status_code=200,
    response_model=TweetListOut,
    response_description="Success",
    tags=tweets_tags,
)
async def get_tweets(
    db_session: Annotated[AsyncSession, Depends(models.db_session)],
    auth_user: Annotated[models.User, Depends(get_authorized_user)],
    offset: Optional[int] = Query(default=None, description="Номер страницы", ge=1),
    limit: Optional[int] = Query(default=None, description="Количество твитов на странице", ge=1),
) -> TweetListOut:
    """Получить ленту твитов пользователя."""
    await db_session.refresh(auth_user, attribute_names=["followings"])

    user_ids = [auth_user.id]
    user_ids.extend([followed_user.user_id for followed_user in auth_user.followings])

    tweet_author = aliased(models.User)
    tweet_like = aliased(models.Like)
    liker = aliased(models.User)

    stmt: Select = (
        select(models.Tweet)
        .join(models.TweetMedia, models.TweetMedia.tweet_id == models.Tweet.id, isouter=True)
        .join(tweet_author, tweet_author.id == models.Tweet.user_id)
        .join(tweet_like, tweet_like.tweet_id == models.Tweet.id, isouter=True)
        .join(liker, liker.id == tweet_like.user_id, isouter=True)
        .where(models.Tweet.user_id.in_(user_ids))
        .group_by(models.Tweet.id)
    )
    if offset is not None and limit is not None:
        stmt = stmt.offset((offset - 1) * limit)  # type: ignore[operator]
    if limit is not None:
        stmt = stmt.limit(limit)
    stmt = stmt.order_by(
        func.count(tweet_like.id).desc(),
        models.Tweet.posted_at.desc(),
    )

    tweets_qs = await db_session.execute(
        stmt.options(
            selectinload(models.Tweet.medias),
            selectinload(models.Tweet.user),
            selectinload(models.Tweet.likes).options(selectinload(models.Like.user)),
        )
    )

    tweets: Sequence[models.Tweet] = tweets_qs.scalars().all()

    return TweetListOut(
        result=True,
        tweets=tweets,
    )
