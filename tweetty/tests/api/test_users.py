import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from ...db import models as db_models
from . import APITestClient, assert_http_error, assert_user

pytestmark = [pytest.mark.anyio, pytest.mark.users]


@pytest.fixture
async def requested_user(db_session: AsyncSession):
    """Тестовый пользователь, профиль которого нужно получить."""
    user = db_models.User(
        nickname="requested_user",
        api_key="ru" * 15,
    )
    db_session.add(user)
    await db_session.commit()

    yield user


@pytest.mark.get_user
@pytest.mark.parametrize(
    "own_profile, api_key",
    [
        (False, ""),
        (False, "no" * 15),
        (True, ""),
        (True, "no" * 15),
    ],
)
async def test_get_user_auth(
    api_client: APITestClient, requested_user: db_models.User, own_profile: bool, api_key: str
):
    """
    Проверка авторизации для получения профиля пользователя.

    :param own_profile: `True`, если пользователь запрашивает свой профиль,
        и `False`, если пользователь запрашивает чужой профиль.
    """
    if own_profile:
        response = await api_client.get_me(api_key)
    else:
        response = await api_client.get_user(requested_user.id, api_key)
    assert response.status_code == 401
    assert_http_error(response.json())


@pytest.mark.get_user
@pytest.mark.parametrize("own_profile", [True, False])
async def test_get_user(
    api_client: APITestClient, test_user: db_models.User, requested_user: db_models.User, own_profile: bool
):
    """
    Проверка получения профиля пользователя.

    :param own_profile: `True`, если пользователь запрашивает свой профиль,
        и `False`, если пользователь запрашивает чужой профиль.
    """
    if own_profile:
        user = test_user
        response = await api_client.get_me(test_user.api_key)
    else:
        user = requested_user
        response = await api_client.get_user(requested_user.id, test_user.api_key)
    assert response.status_code == 200

    resp = response.json()
    assert_user(resp, user.id, user.nickname)

    assert isinstance(resp["user"]["followers"], list)
    assert len(resp["user"]["followers"]) == 0
    assert isinstance(resp["user"]["following"], list)
    assert len(resp["user"]["following"]) == 0


@pytest.mark.get_user
@pytest.mark.parametrize("own_profile", [True, False])
async def test_get_user_with_followers(
    api_client: APITestClient,
    test_user: db_models.User,
    requested_user: db_models.User,
    db_session: AsyncSession,
    own_profile: bool,
):
    """
    Проверка получения профиля пользователя, у которого есть подписчики.

    :param own_profile: `True`, если пользователь запрашивает свой профиль,
        и `False`, если пользователь запрашивает чужой профиль.
    """
    user = test_user if own_profile else requested_user

    followers = [
        db_models.User(
            nickname=f"follower{i}",
            api_key=f"f{i}" * 15,
        )
        for i in range(3)
    ]
    db_session.add_all(followers)
    await db_session.commit()

    db_session.add_all([db_models.Follower(user_id=user.id, follower_id=follower.id) for follower in followers])
    await db_session.commit()

    if own_profile:
        response = await api_client.get_me(test_user.api_key)
    else:
        response = await api_client.get_user(requested_user.id, test_user.api_key)
    assert response.status_code == 200

    resp = response.json()
    assert_user(resp, user.id, user.nickname)

    assert isinstance(resp["user"]["followers"], list)
    assert len(resp["user"]["followers"]) == len(followers)

    for resp_follower in resp["user"]["followers"]:
        assert resp_follower["id"] is not None

        follower = list(filter(lambda f, fid=resp_follower["id"]: f.id == fid, followers))[0]  # type: ignore[arg-type]

        assert resp_follower["name"] == follower.nickname


@pytest.mark.get_user
@pytest.mark.parametrize("own_profile", [True, False])
async def test_get_user_with_following(
    api_client: APITestClient,
    test_user: db_models.User,
    requested_user: db_models.User,
    db_session: AsyncSession,
    own_profile: bool,
):
    """
    Проверка получения профиля пользователя, который на кого-то подписан.

    :param own_profile: `True`, если пользователь запрашивает свой профиль,
        и `False`, если пользователь запрашивает чужой профиль.
    """
    user = test_user if own_profile else requested_user

    followings = [
        db_models.User(
            nickname=f"following{i}",
            api_key=f"f{i}" * 15,
        )
        for i in range(3)
    ]
    db_session.add_all(followings)
    await db_session.commit()

    db_session.add_all([db_models.Follower(user_id=following.id, follower_id=user.id) for following in followings])
    await db_session.commit()

    if own_profile:
        response = await api_client.get_me(test_user.api_key)
    else:
        response = await api_client.get_user(requested_user.id, test_user.api_key)
    assert response.status_code == 200

    resp = response.json()
    assert_user(resp, user.id, user.nickname)

    assert isinstance(resp["user"]["following"], list)
    assert len(resp["user"]["following"]) == len(followings)

    for resp_following in resp["user"]["following"]:
        assert resp_following["id"] is not None

        following = list(filter(lambda f, fid=resp_following["id"]: f.id == fid, followings))[  # type: ignore[arg-type]
            0
        ]

        assert resp_following["name"] == following.nickname


@pytest.mark.get_user
async def test_get_user_not_exists(api_client: APITestClient, test_user: db_models.User):
    """
    Проверка получения профиля пользователя, которого не существует.
    """
    response = await api_client.get_user(100500, test_user.api_key)
    assert response.status_code == 404
    assert_http_error(response.json())


@pytest.mark.get_user
async def test_get_user_redirect(api_client: APITestClient, test_user: db_models.User):
    """Проверка редиректа на `/api/users/me` при запросе собственного профиля по id."""
    response = await api_client.get_user(test_user.id, test_user.api_key)
    assert response.status_code == 308
