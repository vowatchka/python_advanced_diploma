import pytest
from httpx import AsyncClient
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ...db import models as db_models
from . import assert_http_error

pytestmark = [pytest.mark.anyio, pytest.mark.post_likes]


@pytest.fixture
async def liker_user(db_session: AsyncSession):
    """Тестовый пользователь, лайкающий твиты."""
    liker = db_models.User(
        nickname="test_liker",
        api_key="l" * 30,
    )
    db_session.add(liker)
    await db_session.commit()

    yield liker


@pytest.mark.parametrize(
    "api_key",
    [
        "",
        "no" * 15,
    ]
)
async def test_like_auth(client: AsyncClient, api_key: str, test_tweet: db_models.Tweet):
    """Проверка авторизации для добавления лайка."""
    response = await client.post(
        f"/api/tweets/{test_tweet.id}/likes",
        headers={"api-key": api_key},
    )
    assert response.status_code == 401


@pytest.mark.parametrize(
    "own_tweet",
    [True, False]
)
async def test_like_tweet(client: AsyncClient, test_user: db_models.User, test_tweet: db_models.Tweet,
                          liker_user: db_models.User, own_tweet: bool, db_session: AsyncSession):
    """
    Проверка добавления лайка твит.

    :param own_tweet: `True`, если пользователь лайкает свой твит,
        и `False`, если пользователь лайкает чужой твит.
    """
    user = test_user if own_tweet else liker_user

    response = await client.post(
        f"/api/tweets/{test_tweet.id}/likes",
        headers={"api-key": user.api_key},
    )
    assert response.status_code == 201

    resp = response.json()
    assert resp["result"] is True

    # проверяем, что лайк добавился на твит и от имени
    # пользователя, который лайкал
    like_qs = await db_session.execute(
        select(db_models.Like)
        .where(
            and_(
                db_models.Like.tweet_id == test_tweet.id,
                db_models.Like.user_id == user.id
            )
        )
    )
    assert len(like_qs.scalars().all()) == 1
    assert like_qs.scalar_one_or_none() is not None


@pytest.mark.parametrize(
    "own_tweet",
    [True, False]
)
async def test_like_tweet_again(client: AsyncClient, test_user: db_models.User, test_tweet: db_models.Tweet,
                                liker_user: db_models.User, own_tweet: bool, db_session: AsyncSession):
    """Проверка повторного лайка твита, который пользователь уже лайкнул."""
    user = test_user if own_tweet else liker_user

    # лайкаем
    response = await client.post(
        f"/api/tweets/{test_tweet.id}/likes",
        headers={"api-key": user.api_key},
    )
    assert response.status_code == 201

    # лайкаем еще раз
    response = await client.post(
        f"/api/tweets/{test_tweet.id}/likes",
        headers={"api-key": user.api_key},
    )
    assert response.status_code == 200

    resp = response.json()
    assert resp["result"] is True

    # проверяем, что лайк от пользователя по-прежнему один
    like_qs = await db_session.execute(
        select(db_models.Like)
        .where(
            and_(
                db_models.Like.tweet_id == test_tweet.id,
                db_models.Like.user_id == user.id
            )
        )
    )
    assert len(like_qs.scalars().all()) == 1
    assert like_qs.scalar_one_or_none() is not None


async def test_like_not_existed_tweet(client: AsyncClient, test_user: db_models.User):
    """Проверка лайка несуществующего твита."""
    response = await client.post(
        "/api/tweets/100500/likes",
        headers={"api-key": test_user.api_key},
    )
    assert response.status_code == 404

    assert_http_error(response.json())
