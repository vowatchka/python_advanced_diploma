import pytest

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...api import models as api_models
from ...db import models as db_models


@pytest.mark.anyio
@pytest.mark.parametrize(
    "tweet_data",
    [
        "t",
        "test tweet"
    ]
)
async def test_publish_new_tweet(client: AsyncClient, test_user: db_models.User, tweet_data: str,
                                 db_session: AsyncSession):
    """Проверка публикации нового твита."""
    response = await client.post(
        "/api/tweets",
        json={"tweet_data": tweet_data},
        headers={"api-key": test_user.api_key}
    )
    assert response.status_code == 201

    resp = response.json()
    assert resp["result"] is True
    assert resp["tweet_id"] is not None

    # проверяем, что твит есть и в БД
    tweet_qs = await db_session.execute(
        select(db_models.Tweet).where(db_models.Tweet.id == resp["tweet_id"])
    )
    assert tweet_qs.scalar_one_or_none() is not None


@pytest.mark.anyio
@pytest.mark.parametrize(
    "tweet_data",
    [
        "",
        " ",
        "   ",
        "\r\n",
    ]
)
async def test_publish_empty_tweet(client: AsyncClient, test_user: db_models.User, tweet_data: str):
    """Проверка невозможности добавить твит без текста или состоящий только из пробельных символов."""
    response = await client.post(
        "/api/tweets",
        json={"tweet_data": tweet_data},
        headers={"api-key": test_user.api_key}
    )
    assert response.status_code == 422


@pytest.mark.anyio
async def test_truncate_tweet_text(client: AsyncClient, test_user: db_models.User, db_session: AsyncSession):
    """Проверка обрезания текста твита, если он слишком длинный."""
    tweet_max_length = api_models.NewTweetIn.ContentFieldConfig.curtail_length

    response = await client.post(
        "/api/tweets",
        json={"tweet_data": "t" * (tweet_max_length + 10)},
        headers={"api-key": test_user.api_key}
    )
    print(response.text)
    assert response.status_code == 201

    tweet_id = response.json()["tweet_id"]
    tweet_qs = await db_session.execute(
        select(db_models.Tweet).where(db_models.Tweet.id == tweet_id)
    )
    tweet = tweet_qs.scalar_one()
    assert len(tweet.content) == tweet_max_length


@pytest.mark.anyio
@pytest.mark.parametrize(
    "api_key",
    [
        "",
        "no" * 15,
    ]
)
async def test_publish_new_tweet_auth(client: AsyncClient, api_key: str):
    """Проверка авторизации для публикации нового твита."""
    response = await client.post(
        "/api/tweets",
        json={"tweet_data": "test"},
        headers={"api-key": api_key}
    )
    assert response.status_code == 401


@pytest.mark.anyio
@pytest.mark.parametrize(
    "media_count",
    [0, 1, 2, 3]
)
async def test_publish_new_tweet_with_medias(client: AsyncClient, test_user: db_models.User, db_session: AsyncSession,
                                             media_count: int):
    """Проверка добавления медиа к твиту."""
    # добавляем медиа
    medias = list()
    for i in range(media_count):
        medias.append(
            db_models.TweetMedia(
                rel_uri=f"/test{i}"
            )
        )
    db_session.add_all(medias)
    await db_session.commit()

    response = await client.post(
        "/api/tweets",
        json={
            "tweet_data": "test",
            "tweet_media_ids": [media.id for media in medias],
        },
        headers={"api-key": test_user.api_key},
    )
    assert response.status_code == 201

    resp = response.json()

    # обновляем данные по медиа
    for media in medias:
        await db_session.refresh(media)
        assert media.tweet_id == resp["tweet_id"]


@pytest.mark.anyio
async def test_publish_new_tweet_media_items(client: AsyncClient, test_user: db_models.User, db_session: AsyncSession):
    """Проверка ограничения количества медиа-файлов, прикрепляемых к твиту"""
    # добавляем медиа
    medias = list()
    for i in range(api_models.NewTweetIn.MediasFieldConfig.max_items + 1):
        medias.append(
            db_models.TweetMedia(
                rel_uri=f"/test{i}"
            )
        )
    db_session.add_all(medias)
    await db_session.commit()

    response = await client.post(
        "/api/tweets",
        json={
            "tweet_data": "test",
            "tweet_media_ids": [media.id for media in medias],
        },
        headers={"api-key": test_user.api_key},
    )
    assert response.status_code == 422
