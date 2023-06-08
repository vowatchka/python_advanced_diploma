import pytest
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ...db import models as db_models
from . import APITestClient, assert_http_error

pytestmark = [pytest.mark.anyio, pytest.mark.likes]


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


@pytest.mark.post_likes
@pytest.mark.parametrize(
    "api_key",
    [
        "",
        "no" * 15,
    ]
)
async def test_like_auth(api_client: APITestClient, api_key: str, test_tweet: db_models.Tweet):
    """Проверка авторизации для добавления лайка."""
    response = await api_client.like(test_tweet.id, api_key)
    assert response.status_code == 401
    assert_http_error(response.json())


@pytest.mark.post_likes
@pytest.mark.parametrize(
    "own_tweet",
    [True, False]
)
async def test_like_tweet(api_client: APITestClient, test_user: db_models.User, test_tweet: db_models.Tweet,
                          liker_user: db_models.User, own_tweet: bool, db_session: AsyncSession):
    """
    Проверка добавления лайка твит.

    :param own_tweet: `True`, если пользователь лайкает свой твит,
        и `False`, если пользователь лайкает чужой твит.
    """
    user = test_user if own_tweet else liker_user

    response = await api_client.like(test_tweet.id, user.api_key)
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
    likes = like_qs.scalars().all()
    assert len(likes) == 1
    assert likes[0] is not None


@pytest.mark.post_likes
@pytest.mark.parametrize(
    "own_tweet",
    [True, False]
)
async def test_like_tweet_again(api_client: APITestClient, test_user: db_models.User, test_tweet: db_models.Tweet,
                                liker_user: db_models.User, own_tweet: bool, db_session: AsyncSession):
    """
    Проверка повторного лайка твита, который пользователь уже лайкнул.

    :param own_tweet: `True`, если пользователь лайкает свой твит,
        и `False`, если пользователь лайкает чужой твит.
    """
    user = test_user if own_tweet else liker_user

    # лайкаем
    response = await api_client.like(test_tweet.id, user.api_key)
    assert response.status_code == 201

    # лайкаем еще раз
    response = await api_client.like(test_tweet.id, user.api_key)
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
    likes = like_qs.scalars().all()
    assert len(likes) == 1
    assert likes[0] is not None


@pytest.mark.post_likes
async def test_like_not_existed_tweet(api_client: APITestClient, test_user: db_models.User):
    """Проверка лайка несуществующего твита."""
    response = await api_client.like(100500, test_user.api_key)
    assert response.status_code == 404

    assert_http_error(response.json())


@pytest.mark.delete_likes
@pytest.mark.parametrize(
    "api_key",
    [
        "",
        "no" * 15,
    ]
)
async def test_unlike_auth(api_client: APITestClient, api_key: str, test_tweet: db_models.Tweet):
    """Проверка авторизации при удалении лайка."""
    response = await api_client.unlike(test_tweet.id, api_key)
    assert response.status_code == 401
    assert_http_error(response.json())


@pytest.mark.delete_likes
@pytest.mark.parametrize(
    "own_tweet",
    [True, False]
)
async def test_unlike_tweet(api_client: APITestClient, test_user: db_models.User, test_tweet: db_models.Tweet,
                            liker_user: db_models.User, own_tweet: bool, db_session: AsyncSession):
    """
    Проверка удаления лайка с твита.

    :param own_tweet: `True`, если пользователь дизлайкает свой твит,
        и `False`, если пользователь дизлайкает чужой твит.
    """
    user = test_user if own_tweet else liker_user

    # создаем лайк
    like = db_models.Like(
        tweet_id=test_tweet.id,
        user_id=user.id,
    )
    db_session.add(like)
    await db_session.commit()

    response = await api_client.unlike(test_tweet.id, user.api_key)
    assert response.status_code == 200

    resp = response.json()
    assert resp["result"] is True

    # проверяем, что лайк удалился
    like_qs = await db_session.execute(
        select(db_models.Like)
        .where(
            and_(
                db_models.Like.tweet_id == test_tweet.id,
                db_models.Like.user_id == user.id
            )
        )
    )
    assert len(like_qs.scalars().all()) == 0


@pytest.mark.delete_likes
@pytest.mark.parametrize(
    "own_tweet",
    [True, False]
)
async def test_unlike_tweet_again(api_client: APITestClient, test_user: db_models.User, test_tweet: db_models.Tweet,
                                  liker_user: db_models.User, own_tweet: bool, db_session: AsyncSession):
    """
    Проверка повторного дизлайка твита, который пользователь уже дизлайкнул.

    :param own_tweet: `True`, если пользователь дизлайкает свой твит,
        и `False`, если пользователь дизлайкает чужой твит.
    """
    user = test_user if own_tweet else liker_user

    # создаем лайк
    like = db_models.Like(
        tweet_id=test_tweet.id,
        user_id=user.id,
    )
    db_session.add(like)
    await db_session.commit()

    # дизлайкаем
    response = await api_client.unlike(test_tweet.id, user.api_key)
    assert response.status_code == 200

    # дизлайкаем еще раз
    response = await api_client.unlike(test_tweet.id, user.api_key)
    # метод DELETE должен быть идемпотентным
    assert response.status_code == 200

    resp = response.json()
    assert resp["result"] is True


@pytest.mark.delete_likes
async def test_unlike_not_existed_tweet(api_client: APITestClient, test_user: db_models.User):
    """Проверка дизлайка несуществующего твита."""
    response = await api_client.unlike(100500, test_user.api_key)
    assert response.status_code == 404

    assert_http_error(response.json())
