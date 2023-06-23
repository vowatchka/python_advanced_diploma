import os
import random
from pathlib import PosixPath, WindowsPath
from typing import BinaryIO, Union

import aiofiles
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...api import models as api_models
from ...db import models as db_models
from ...settings import STATIC_DIR, STATIC_URL
from . import APITestClient, assert_http_error, assert_tweet_list

pytestmark = [pytest.mark.anyio, pytest.mark.tweets]


@pytest.fixture
async def test_tweet(db_session: AsyncSession, test_user: db_models.User):
    """Тестовый твит."""
    tweet = db_models.Tweet(
        content="test",
        user_id=test_user.id
    )
    db_session.add(tweet)
    await db_session.commit()

    yield tweet


@pytest.mark.post_tweet
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


@pytest.mark.post_tweet
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


@pytest.mark.post_tweet
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


@pytest.mark.post_tweet
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


@pytest.mark.post_tweet
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


@pytest.mark.post_tweet
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


@pytest.mark.post_tweet
async def test_publish_new_tweet_with_not_unique_media_items(api_client: APITestClient, test_user: db_models.User,
                                                             db_session: AsyncSession):
    """Проверка, что список медиа должен состоять из уникальных элементов."""
    new_media = db_models.TweetMedia(
        rel_uri="/test",
    )
    db_session.add(new_media)
    await db_session.commit()

    response = await api_client.publish_tweet(
        {
            "tweet_data": "not unique medias",
            "tweet_media_ids": [new_media.id] * 3,
        },
        test_user.api_key,
    )
    assert response.status_code == 422


@pytest.mark.delete_tweet
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


@pytest.mark.delete_tweet
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


@pytest.mark.delete_tweet
async def test_delete_tweet_idempotency(api_client: APITestClient, test_user: db_models.User,
                                        test_tweet: db_models.Tweet):
    """Проверка идемпотентности удаления твита."""
    response = await api_client.delete_tweet(test_tweet.id, test_user.api_key)
    assert response.status_code == 200

    # повторно удаляем удаленный твит
    response = await api_client.delete_tweet(test_tweet.id, test_user.api_key)
    # метод DELETE должен быть идемпотентным
    assert response.status_code == 200


@pytest.mark.delete_tweet
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


@pytest.mark.get_tweets
async def test_get_tweets_without_any_tweet(api_client: APITestClient, test_user: db_models.User):
    """Проверка получения пустового списка твитов при отсутствии твитов у пользователя."""
    response = await api_client.get_tweets(test_user.api_key)
    assert response.status_code == 200

    assert_tweet_list(response.json(), 0)


@pytest.fixture
async def prepare_tweets(test_user: db_models.User, followed_user: db_models.User,
                         db_session: AsyncSession):
    """Тестовые твиты для тестов получения твитов."""
    async def _prepare_tweets(own_tweets: bool) -> tuple[db_models.User, list[db_models.Tweet]]:
        if not own_tweets:
            user = followed_user

            db_session.add(db_models.Follower(
                user_id=followed_user.id,
                follower_id=test_user.id,
            ))
            await db_session.commit()
        else:
            user = test_user

        tweets = [
            db_models.Tweet(content=f"test{i}", user_id=user.id)
            for i in range(3)
        ]
        db_session.add_all(tweets)
        await db_session.commit()

        return user, tweets

    yield _prepare_tweets


@pytest.mark.get_tweets
@pytest.mark.parametrize(
    "own_tweets",
    [True, False]
)
async def test_get_tweets(api_client: APITestClient, test_user: db_models.User, prepare_tweets, own_tweets: bool):
    """
    Проверка получения твитов пользователя.

    :param own_tweets: `True`, если выполнять тесты с собственными твитами пользователя,
        и `False`, если выполнять тесты с твитами читаемых пользователей.
    """
    user, tweets = await prepare_tweets(own_tweets)

    response = await api_client.get_tweets(test_user.api_key)
    assert response.status_code == 200

    resp = response.json()
    assert_tweet_list(resp, len(tweets))

    for tweet in resp["tweets"]:
        assert tweet["id"] is not None
        assert isinstance(tweet["content"], str)
        assert tweet["content"] is not None
        assert isinstance(tweet["author"], dict)
        assert tweet["author"]["id"] == user.id
        assert tweet["author"]["name"] == user.nickname
        assert isinstance(tweet["attachments"], list)
        assert len(tweet["attachments"]) == 0
        assert isinstance(tweet["likes"], list)
        assert len(tweet["likes"]) == 0


@pytest.mark.get_tweets
@pytest.mark.parametrize(
    "own_tweets",
    [True, False]
)
async def test_get_tweets_with_attachments(api_client: APITestClient, test_user: db_models.User,
                                           db_session: AsyncSession, prepare_tweets, own_tweets: bool):
    """
    Проверка получения твитов пользователя с вложениями.

    :param own_tweets: `True`, если выполнять тесты с собственными твитами пользователя,
        и `False`, если выполнять тесты с твитами читаемых пользователей.
    """
    user, tweets = await prepare_tweets(own_tweets)

    for idx, tweet in enumerate(tweets):
        medias = [
            db_models.TweetMedia(
                rel_uri=STATIC_DIR + f"/test{i}.png",
                tweet_id=tweet.id
            )
            for i in range(idx + 1)
        ]
        db_session.add_all(medias)
        await db_session.commit()
        await db_session.refresh(tweet, attribute_names=["medias"])

    response = await api_client.get_tweets(test_user.api_key)
    assert response.status_code == 200

    resp = response.json()
    assert_tweet_list(resp, len(tweets))

    for resp_tweet in resp["tweets"]:
        tweet = list(filter(lambda t, tid=resp_tweet["id"]: t.id == tid, tweets))[0]  # type: ignore[arg-type]

        assert isinstance(resp_tweet["attachments"], list)
        assert len(resp_tweet["attachments"]) == len(tweet.medias)

        for attach in resp_tweet["attachments"]:
            assert attach.startswith(STATIC_URL)


@pytest.mark.get_tweets
@pytest.mark.parametrize(
    "own_tweets",
    [True, False]
)
async def test_get_tweets_with_likes(api_client: APITestClient, test_user: db_models.User,
                                     db_session: AsyncSession, prepare_tweets, own_tweets: bool):
    """
    Проверка получения собственных твитов пользователя с лайками.

    :param own_tweets: `True`, если выполнять тесты с собственными твитами пользователя,
        и `False`, если выполнять тесты с твитами читаемых пользователей.
    """
    user, tweets = await prepare_tweets(own_tweets)

    users = [
        db_models.User(
            nickname="test_liker_1",
            api_key="b" * 30,
        ),
        db_models.User(
            nickname="test_liker_2",
            api_key="c" * 30,
        ),
    ]
    db_session.add_all(users)
    await db_session.commit()

    # пользователь может лайкать сам себя
    users.append(test_user)

    for tweet in tweets:
        likers = users[:random.randint(1, len(users))]

        likes = [
            db_models.Like(
                tweet_id=tweet.id,
                user_id=liker.id,
            )
            for liker in likers
        ]
        db_session.add_all(likes)
        await db_session.commit()
        await db_session.refresh(tweet, attribute_names=["likes"])

    response = await api_client.get_tweets(test_user.api_key)
    assert response.status_code == 200

    resp = response.json()
    assert_tweet_list(resp, len(tweets))

    for resp_tweet in resp["tweets"]:
        tweet = list(filter(lambda t, tid=resp_tweet["id"]: t.id == tid, tweets))[0]  # type: ignore[arg-type]

        assert isinstance(resp_tweet["likes"], list)
        assert len(resp_tweet["likes"]) == len(tweet.likes)

        for user_like in resp_tweet["likes"]:
            assert user_like["id"] is not None

            likers = list(
                filter(lambda u, uid=user_like["id"]: u.id == uid, tweet.liked_by_users)  # type: ignore[arg-type]
            )
            assert user_like["name"] == likers[0].nickname


@pytest.mark.get_tweets
async def test_get_tweets_likes_sorted_desc(api_client: APITestClient, test_user: db_models.User,
                                            test_tweet: db_models.Tweet, followed_user: db_models.User,
                                            db_session: AsyncSession):
    """Проверка, что твиты в ленте отсортированы по убыванию лайков."""
    # создаем твит пользователю, на которого подпишемся
    followed_user_tweets = [
        db_models.Tweet(
            content=f"followed user tweet {i}",
            user_id=followed_user.id,
        )
        for i in range(3)
    ]
    db_session.add_all(followed_user_tweets)
    await db_session.commit()

    # подписываемся
    db_session.add(
        db_models.Follower(
            user_id=followed_user.id,
            follower_id=test_user.id,
        )
    )
    await db_session.commit()

    # создаем пользователя, который просто лайкает
    liker = db_models.User(
        nickname="licker",
        api_key="l" * 30,
    )
    db_session.add(liker)
    await db_session.commit()

    # твиты
    tweets = [test_tweet]
    tweets.extend(followed_user_tweets)
    # пользователи
    users = [test_user, followed_user, liker]

    # ставим лайки
    for idx, tweet in enumerate(tweets):
        if idx < len(users):
            likes = [
                db_models.Like(
                    tweet_id=tweet.id,
                    user_id=user.id,
                )
                for user in users[:idx + 1]
            ]
            db_session.add_all(likes)
            await db_session.commit()

        await db_session.refresh(tweet, attribute_names=["likes"])

    # сортируем твиты по убыванию количества лайков
    tweets = sorted(tweets, key=lambda t: len(t.likes), reverse=True)

    response = await api_client.get_tweets(test_user.api_key)
    assert response.status_code == 200

    resp = response.json()
    assert_tweet_list(resp, len(tweets))

    # проверяем правильность сортировки
    for idx, resp_tweet in enumerate(resp["tweets"]):
        tweet = tweets[idx]

        assert len(resp_tweet["likes"]) == len(tweet.likes)
        assert resp_tweet["id"] == tweet.id
