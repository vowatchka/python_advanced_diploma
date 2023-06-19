import os
from pathlib import PosixPath, WindowsPath
from typing import BinaryIO, Union

import aiofiles
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...api import models as api_models
from ...db import models as db_models
from . import APITestClient, assert_http_error

pytestmark = [pytest.mark.anyio, pytest.mark.tweets]


@pytest.fixture
async def test_tweet(db_session: AsyncSession, test_user: db_models.User):
    tweet = db_models.Tweet(
        content="test",
        user_id=test_user.id
    )
    db_session.add(tweet)
    await db_session.commit()

    yield tweet


@pytest.mark.post_tweets
@pytest.mark.parametrize(
    "tweet_data",
    [
        "t",
        "test tweet"
    ]
)
async def test_publish_new_tweet(api_client: APITestClient, test_user: db_models.User, tweet_data: str,
                                 db_session: AsyncSession):
    """Проверка публикации нового твита."""
    response = await api_client.publish_tweet({"tweet_data": tweet_data}, test_user.api_key)
    assert response.status_code == 201

    resp = response.json()
    assert resp["result"] is True
    assert resp["tweet_id"] is not None

    # проверяем, что твит есть и в БД
    tweet_qs = await db_session.execute(
        select(db_models.Tweet).where(db_models.Tweet.id == resp["tweet_id"])
    )
    assert tweet_qs.scalar_one_or_none() is not None


@pytest.mark.post_tweets
@pytest.mark.parametrize(
    "tweet_data",
    [
        "",
        " ",
        "   ",
        "\r\n",
    ]
)
async def test_publish_empty_tweet(api_client: APITestClient, test_user: db_models.User, tweet_data: str):
    """Проверка невозможности добавить твит без текста или состоящий только из пробельных символов."""
    response = await api_client.publish_tweet({"tweet_data": tweet_data}, test_user.api_key)
    assert response.status_code == 422


@pytest.mark.post_tweets
async def test_truncate_tweet_text(api_client: APITestClient, test_user: db_models.User, db_session: AsyncSession):
    """Проверка обрезания текста твита, если он слишком длинный."""
    tweet_max_length = api_models.NewTweetIn.ContentFieldConfig.curtail_length

    response = await api_client.publish_tweet({"tweet_data": "t" * (tweet_max_length + 10)}, test_user.api_key)
    assert response.status_code == 201

    tweet_id = response.json()["tweet_id"]
    tweet_qs = await db_session.execute(
        select(db_models.Tweet).where(db_models.Tweet.id == tweet_id)
    )
    tweet = tweet_qs.scalar_one()
    assert len(tweet.content) == tweet_max_length


@pytest.mark.post_tweets
@pytest.mark.parametrize(
    "api_key",
    [
        "",
        "no" * 15,
    ]
)
async def test_publish_new_tweet_auth(api_client: APITestClient, api_key: str):
    """Проверка авторизации для публикации нового твита."""
    response = await api_client.publish_tweet({"tweet_data": "test"}, api_key)
    assert response.status_code == 401
    assert_http_error(response.json())


@pytest.mark.post_tweets
@pytest.mark.parametrize(
    "media_count",
    [0, 1, 2, 3]
)
async def test_publish_new_tweet_with_medias(api_client: APITestClient, test_user: db_models.User,
                                             db_session: AsyncSession, media_count: int):
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

    response = await api_client.publish_tweet(
        {
            "tweet_data": "test",
            "tweet_media_ids": [media.id for media in medias],
        },
        test_user.api_key
    )
    assert response.status_code == 201

    resp = response.json()

    # обновляем данные по медиа
    for media in medias:
        await db_session.refresh(media)
        assert media.tweet_id == resp["tweet_id"]


@pytest.mark.post_tweets
async def test_publish_new_tweet_media_items(api_client: APITestClient, test_user: db_models.User,
                                             db_session: AsyncSession):
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

    response = await api_client.publish_tweet(
        {
            "tweet_data": "test",
            "tweet_media_ids": [media.id for media in medias],
        },
        test_user.api_key
    )
    assert response.status_code == 422


@pytest.mark.delete_tweets
@pytest.mark.parametrize(
    "api_key",
    [
        "",
        "no" * 15,
    ]
)
async def test_delete_tweet_auth(api_client: APITestClient, api_key: str):
    """Проверка авторизации для удаления твита."""
    response = await api_client.delete_tweet(1, api_key)
    assert response.status_code == 401
    assert_http_error(response.json())


@pytest.mark.delete_tweets
async def test_delete_tweet(api_client: APITestClient, test_user: db_models.User, test_tweet: db_models.Tweet,
                            db_session: AsyncSession, test_file: tuple[str, BinaryIO],
                            test_file_uploaded_path: Union[PosixPath, WindowsPath]):
    """Проверка удаления существующего твита."""
    # создаем медиа к твиту
    os.makedirs(test_file_uploaded_path.resolve().parent, exist_ok=True)
    async with aiofiles.open(test_file_uploaded_path, "wb") as f:
        await f.write(test_file[1].read())

    new_media = db_models.TweetMedia(
        rel_uri=str(test_file_uploaded_path),
        tweet_id=test_tweet.id
    )
    db_session.add(new_media)
    await db_session.commit()

    response = await api_client.delete_tweet(test_tweet.id, test_user.api_key)
    assert response.status_code == 200

    resp = response.json()
    assert resp["result"] is True

    # проверяем, что твита нет
    tweet_qs = await db_session.execute(
        select(db_models.Tweet).where(db_models.Tweet.id == test_tweet.id)
    )
    assert tweet_qs.scalar_one_or_none() is None
    # поверяем, что медиа тоже удалено
    media_qs = await db_session.execute(
        select(db_models.TweetMedia).where(db_models.TweetMedia.tweet_id == test_tweet.id)
    )
    assert len(media_qs.scalars().all()) == 0
    assert not test_file_uploaded_path.exists()


@pytest.mark.delete_tweets
async def test_delete_tweet_idempotency(api_client: APITestClient, test_user: db_models.User,
                                        test_tweet: db_models.Tweet):
    """Проверка идемпотентности удаления твита."""
    response = await api_client.delete_tweet(test_tweet.id, test_user.api_key)
    assert response.status_code == 200

    # повторно удаляем удаленный твит
    response = await api_client.delete_tweet(test_tweet.id, test_user.api_key)
    # метод DELETE должен быть идемпотентным
    assert response.status_code == 200


@pytest.mark.delete_tweets
async def test_delete_someone_else_tweet(api_client: APITestClient, test_tweet: db_models.Tweet,
                                         db_session: AsyncSession):
    """Проверка запрета на удаление чужого твита."""
    # создаем юзера, который будет удалять твит
    hacker = db_models.User(
        nickname="hacker",
        api_key="h" * 30
    )
    db_session.add(hacker)
    await db_session.commit()

    response = await api_client.delete_tweet(test_tweet.id, hacker.api_key)
    assert response.status_code == 403

    assert_http_error(response.json())


@pytest.mark.get_tweets
@pytest.mark.parametrize(
    "api_key",
    [
        "",
        "no" * 15,
    ]
)
async def test_get_tweets_auth(api_client: APITestClient, api_key: str):
    """Проверка авторизации для получения ленты твитов."""
    response = await api_client.get_tweets(api_key)
    assert response.status_code == 401
    assert_http_error(response.json())
