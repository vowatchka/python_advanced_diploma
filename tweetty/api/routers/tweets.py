from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from ...db import models
from ..auth import get_authorized_user
from ..models import NewTweetIn, NewTweetOut

tweets_router = APIRouter(prefix="/tweets")


@tweets_router.post(
    "",
    summary="Опубликовать новый твит",
    response_model=NewTweetOut,
    status_code=201,
    tags=["tweets"]
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
