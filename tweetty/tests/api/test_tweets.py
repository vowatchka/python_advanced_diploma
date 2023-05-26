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
async def test_publish_new_tweet(client: AsyncClient, test_user: db_models.User, tweet_data: str):
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


@pytest.mark.anyio
@pytest.mark.parametrize(
    "tweet_data",
    [
        "",
        " ",
        "   ",
        "\r\n"
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
    tweet_max_length = api_models.NewTweetIn.avail_content_length().max

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
