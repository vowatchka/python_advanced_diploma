import pytest
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ...db import models as db_models
from . import APITestClient, assert_http_error

pytestmark = [pytest.mark.anyio, pytest.mark.follows]


@pytest.fixture
async def followed_user(db_session: AsyncSession):
    """Тестовый пользователь, на которого подписываются."""
    user = db_models.User(
        nickname="Followed User",
        api_key="f" * 30,
    )
    db_session.add(user)
    await db_session.commit()

    yield user


@pytest.fixture
async def test_subscription(db_session: AsyncSession, test_user: db_models.User, followed_user: db_models.User):
    """Тестовая подписка одного пользователя на другого."""
    follow = db_models.Follower(
        user_id=followed_user.id,
        follower_id=test_user.id,
    )
    db_session.add(follow)
    await db_session.commit()

    yield follow


@pytest.mark.post_follows
@pytest.mark.parametrize(
    "api_key",
    [
        "",
        "no" * 15,
    ]
)
async def test_follow_auth(api_client: APITestClient, followed_user: db_models.User, api_key: str):
    """Проверка аворизации для подписки на пользователя."""
    response = await api_client.follow(followed_user.id, api_key)
    assert response.status_code == 401
    assert_http_error(response.json())


@pytest.mark.post_follows
async def test_follow(api_client: APITestClient, test_user: db_models.User, followed_user: db_models.User,
                      db_session: AsyncSession):
    """Проверка подписи на другого пользователя."""
    response = await api_client.follow(followed_user.id, test_user.api_key)
    assert response.status_code == 201

    resp = response.json()
    assert resp["result"] is True

    # проверяем, что подписка есть
    follow_qs = await db_session.execute(
        select(db_models.Follower)
        .where(
            and_(
                db_models.Follower.user_id == followed_user.id,
                db_models.Follower.follower_id == test_user.id
            )
        )
    )
    follows = follow_qs.scalars().all()
    assert len(follows) == 1
    assert follows[0] is not None


@pytest.mark.post_follows
async def test_follow_again(api_client: APITestClient, test_user: db_models.User, followed_user: db_models.User,
                            db_session: AsyncSession):
    """Проверка подписи на другого пользователя, на которого уже подписаны."""
    # подписываемся
    response = await api_client.follow(followed_user.id, test_user.api_key)
    assert response.status_code == 201

    # подписываемся еще раз
    response = await api_client.follow(followed_user.id, test_user.api_key)
    assert response.status_code == 200

    resp = response.json()
    assert resp["result"] is True

    # проверяем, что подписка по-прежнему одина
    follow_qs = await db_session.execute(
        select(db_models.Follower)
        .where(
            and_(
                db_models.Follower.user_id == followed_user.id,
                db_models.Follower.follower_id == test_user.id
            )
        )
    )
    follows = follow_qs.scalars().all()
    assert len(follows) == 1
    assert follows[0] is not None


@pytest.mark.post_follows
async def test_follow_self(api_client: APITestClient, test_user: db_models.User):
    """Проверка невоможности подписаться на самого себя."""
    response = await api_client.follow(test_user.id, test_user.api_key)
    assert response.status_code == 406
    assert_http_error(response.json())


@pytest.mark.post_follows
async def test_follow_not_existed_user(api_client: APITestClient, test_user: db_models.User):
    """Проверка подписки на несуществующего пользователя."""
    response = await api_client.follow(100500, test_user.api_key)
    assert response.status_code == 404
    assert_http_error(response.json())
