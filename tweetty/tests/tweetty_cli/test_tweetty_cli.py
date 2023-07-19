from typing import Optional

import pytest
from pytest_mock import MockerFixture
from sqlalchemy import and_
from sqlalchemy.orm import Session
from typer.testing import CliRunner

from ...db import models as db_models
from ...settings import API_KEY_PREFIX
from ...tweetty_cli import users

pytestmark = [pytest.mark.cli]


@pytest.fixture(autouse=True)
def db_session_mocker(db_session: Session, mocker: MockerFixture):
    mock = mocker.patch("tweetty.tweetty_cli.users.db_session")
    mock.return_value.__enter__.return_value = db_session


@pytest.fixture(scope="session")
def cli_runner():
    yield CliRunner()


@pytest.mark.parametrize(
    "nickname, first_name, last_name",
    [
        ("test1", None, None),
        ("test1", "Test", None),
        ("test1", None, "Test"),
        ("test1", "Test", "Test"),
    ],
)
def test_add_user(cli_runner: CliRunner, nickname: str, first_name: Optional[str], last_name: Optional[str]):
    """Проверка добавления пользователя."""
    args = ["add", nickname]
    if first_name is not None:
        args.extend(["--first-name", first_name])
    if last_name is not None:
        args.extend(["--last-name", last_name])

    result = cli_runner.invoke(users.users_app, args)
    assert result.exit_code == 0

    assert "User added" in result.stdout
    assert nickname in result.stdout


def test_remove_user(cli_runner: CliRunner, test_user: db_models.User, db_session: Session):
    """Проверка удаления пользователя."""
    result = cli_runner.invoke(users.users_app, ["remove", test_user.nickname])
    assert result.exit_code == 0

    user = db_session.query(db_models.User).where(db_models.User.nickname == test_user.nickname).one_or_none()
    assert user is None

    assert f"User {test_user.nickname!r} deleted" in result.stdout


def test_remove_user_idempotent(cli_runner: CliRunner, test_user: db_models.User, db_session: Session):
    """Проверка идемпотентности удаления пользователя."""
    for _ in range(2):
        result = cli_runner.invoke(users.users_app, ["remove", test_user.nickname])
        assert result.exit_code == 0

        user = db_session.query(db_models.User).where(db_models.User.nickname == test_user.nickname).one_or_none()
        assert user is None

        assert f"User {test_user.nickname!r} deleted" in result.stdout


@pytest.mark.parametrize(
    "nickname, first_name, last_name",
    [
        ("test1", None, None),
        ("test1", "Test", None),
        ("test1", None, "Test"),
        ("test1", "Test", "Test"),
    ],
)
def test_update_user(
    cli_runner: CliRunner, db_session: Session, nickname: str, first_name: Optional[str], last_name: Optional[str]
):
    """Проверка обновления пользователя."""
    user = db_models.User(
        nickname=nickname,
        first_name="First",
        last_name="Last",
        api_key="t" * 30,
    )
    db_session.add(user)
    db_session.commit()

    args = ["update", nickname]

    if first_name is None:
        args.extend(["--reset-first-name"])
    else:
        args.extend(["--first-name", first_name])

    if last_name is None:
        args.extend(["--reset-last-name"])
    else:
        args.extend(["--last-name", last_name])

    result = cli_runner.invoke(users.users_app, args)
    assert result.exit_code == 0

    db_session.refresh(user)

    if first_name is None:
        assert user.first_name is None
    else:
        assert user.first_name == first_name

    if last_name is None:
        assert user.last_name is None
    else:
        assert user.last_name == last_name

    assert f"User {nickname!r} updated" in result.stdout


def test_update_not_existed_user(cli_runner: CliRunner):
    """Проверка невозможности обновить несуществующего пользователя."""
    nickname = "not_existed"

    result = cli_runner.invoke(users.users_app, ["update", nickname, "--first-name", "First"])
    assert result.exit_code == 1

    assert f"User {nickname!r} not found" in result.stdout


def test_new_api_key(cli_runner: CliRunner, test_user: db_models.User, db_session: Session):
    """Проверка обновления Api Key."""
    old_api_key = test_user.api_key

    result = cli_runner.invoke(users.users_app, ["new_api_key", test_user.nickname])
    assert result.exit_code == 0

    db_session.refresh(test_user)

    assert test_user.api_key != old_api_key
    assert test_user.api_key.startswith(API_KEY_PREFIX)


def test_new_api_key_not_existed_user(cli_runner: CliRunner):
    """Проверка невозможности обновить Api Key у несуществующего пользователя."""
    nickname = "not_existed"

    result = cli_runner.invoke(users.users_app, ["new_api_key", nickname])
    assert result.exit_code == 1

    assert f"User {nickname!r} not found" in result.stdout


@pytest.mark.parametrize("show_api_key", [True, False])
def test_get_user(cli_runner: CliRunner, test_user: db_models.User, show_api_key: bool):
    """Проверка получения пользоватля."""
    args = ["get", test_user.nickname]
    if show_api_key:
        args.append("-a")

    result = cli_runner.invoke(users.users_app, args)
    assert result.exit_code == 0

    assert test_user.nickname in result.stdout
    assert str(test_user.first_name) in result.stdout
    assert str(test_user.last_name) in result.stdout
    if show_api_key:
        assert test_user.api_key in result.stdout


def test_get_not_existed_user(cli_runner: CliRunner):
    """Проверка невозможности получить несуществующего пользователя."""
    nickname = "not_existed"

    result = cli_runner.invoke(users.users_app, ["get", nickname])
    assert result.exit_code == 1

    assert f"User {nickname!r} not found" in result.stdout


@pytest.mark.parametrize("show_api_key", [True, False])
def test_list_users(cli_runner: CliRunner, db_session: Session, show_api_key: bool):
    """Проверка получения списка пользователей."""
    new_users = sorted(
        [
            db_models.User(
                nickname=f"test{i}",
                api_key=f"t{i}" * 15,
            )
            for i in range(3)
        ],
        key=lambda user: user.nickname,
    )
    db_session.add_all(new_users)
    db_session.commit()

    args = ["list"]
    if show_api_key:
        args.append("-a")

    result = cli_runner.invoke(users.users_app, args)
    assert result.exit_code == 0

    assert len(new_users) == result.stdout.count("Nickname:")

    for user in new_users:
        assert user.nickname in result.stdout
        assert str(user.first_name) in result.stdout
        assert str(user.last_name) in result.stdout
        if show_api_key:
            assert user.api_key in result.stdout


@pytest.mark.parametrize("show_api_key", [True, False])
def test_list_users_with_page_and_limit(cli_runner: CliRunner, db_session: Session, show_api_key: bool):
    """Проверка получения списка пользователей с постраничной навигацией."""
    new_users = sorted(
        [
            db_models.User(
                nickname=f"test{i}",
                api_key=f"t{i}" * 15,
            )
            for i in range(3)
        ],
        key=lambda user: user.nickname,
    )
    db_session.add_all(new_users)
    db_session.commit()

    for idx, user in enumerate(new_users):
        limit = 1

        args = ["list", "--page", str(idx + 1), "--limit", str(limit)]
        if show_api_key:
            args.append("-a")

        result = cli_runner.invoke(users.users_app, args)
        assert result.exit_code == 0

        assert f"Page {idx + 1}" in result.stdout
        assert f"Users per page: {limit}" in result.stdout

        assert limit == result.stdout.count("Nickname:")

        assert user.nickname in result.stdout
        assert str(user.first_name) in result.stdout
        assert str(user.last_name) in result.stdout
        if show_api_key:
            assert user.api_key in result.stdout


@pytest.mark.parametrize("show_api_key", [True, False])
def test_search_users(cli_runner: CliRunner, db_session: Session, show_api_key: bool):
    """Проверка поиска пользователей."""
    new_users = [
        db_models.User(
            nickname="test_1",
            api_key="t1" * 15,
        ),
        db_models.User(
            nickname="test2",
            first_name="test_2",
            api_key="t2" * 15,
        ),
        db_models.User(
            nickname="test3",
            last_name="test_3",
            api_key="t3" * 15,
        ),
        db_models.User(
            nickname="not searched",
            api_key="ns" * 15,
        ),
    ]
    db_session.add_all(new_users)
    db_session.commit()

    searched_expr = "test_"
    founded_users = sorted(
        [
            user
            for user in new_users
            if (
                searched_expr in user.nickname
                or (user.first_name and searched_expr in user.first_name)
                or (user.last_name and searched_expr in user.last_name)
            )
        ],
        key=lambda user: user.nickname,
    )

    args = ["search", searched_expr]
    if show_api_key:
        args.append("-a")

    result = cli_runner.invoke(users.users_app, args)
    assert result.exit_code == 0

    assert len(founded_users) == result.stdout.count("Nickname:")

    for user in founded_users:
        assert user.nickname in result.stdout
        assert str(user.first_name) in result.stdout
        assert str(user.last_name) in result.stdout
        if show_api_key:
            assert user.api_key in result.stdout


@pytest.mark.parametrize("show_api_key", [True, False])
def test_search_users_with_page_and_limit(cli_runner: CliRunner, db_session: Session, show_api_key: bool):
    """Проверка поиска пользователей с постраничной навигацией."""
    new_users = [
        db_models.User(
            nickname="test_1",
            api_key="t1" * 15,
        ),
        db_models.User(
            nickname="test2",
            first_name="test_2",
            api_key="t2" * 15,
        ),
        db_models.User(
            nickname="test3",
            last_name="test_3",
            api_key="t3" * 15,
        ),
        db_models.User(
            nickname="not searched",
            api_key="ns" * 15,
        ),
    ]
    db_session.add_all(new_users)
    db_session.commit()

    searched_expr = "test_"
    founded_users = sorted(
        [
            user
            for user in new_users
            if (
                searched_expr in user.nickname
                or (user.first_name and searched_expr in user.first_name)
                or (user.last_name and searched_expr in user.last_name)
            )
        ],
        key=lambda user: user.nickname,
    )

    for idx, user in enumerate(founded_users):
        limit = 1

        args = ["search", searched_expr, "--page", str(idx + 1), "--limit", limit]
        if show_api_key:
            args.append("-a")

        result = cli_runner.invoke(users.users_app, args)
        assert result.exit_code == 0

        assert f"Page {idx + 1}" in result.stdout
        assert f"Users per page: {limit}" in result.stdout

        assert result.stdout.count("Nickname:") == limit

        assert user.nickname in result.stdout
        assert str(user.first_name) in result.stdout
        assert str(user.last_name) in result.stdout
        if show_api_key:
            assert user.api_key in result.stdout


def test_follow_to_user(
    cli_runner: CliRunner, test_user: db_models.User, followed_user: db_models.User, db_session: Session
):
    """Проверка подписки одного пользователя на другого."""
    result = cli_runner.invoke(users.users_app, ["follow", followed_user.nickname, test_user.nickname])
    assert result.exit_code == 0

    assert f"User {test_user.nickname!r} is now follow to user {followed_user.nickname!r}" in result.stdout

    follower_qs = db_session.query(db_models.Follower).where(
        and_(
            db_models.Follower.user_id == followed_user.id,
            db_models.Follower.follower_id == test_user.id,
        )
    )
    assert follower_qs.one_or_none() is not None


def test_follow_to_self(cli_runner: CliRunner, test_user: db_models.User):
    """Проверка невозможности подписаться на себя."""
    result = cli_runner.invoke(users.users_app, ["follow", test_user.nickname, test_user.nickname])
    assert result.exit_code == 1

    assert "Follow to himself is not acceptable" in result.stdout


@pytest.mark.parametrize(
    "user, follower",
    [
        ("test", "not_existed"),
        ("not_existed", "test"),
    ],
)
def test_follow_to_not_existed_users(cli_runner: CliRunner, test_user: db_models.User, user: str, follower: str):
    """Проверка невозможности подписаться на несуществующего пользователя."""
    user_nickname = test_user.nickname if user == "test" else follower
    follower_nickname = follower if user == "test" else test_user.nickname

    result = cli_runner.invoke(users.users_app, ["follow", user_nickname, follower_nickname])
    assert result.exit_code == 1

    expected_nickname = follower_nickname if user == "test" else user_nickname
    assert f"User {expected_nickname!r} not found" in result.stdout


def test_unfollow_from_user(
    cli_runner: CliRunner, test_user: db_models.User, followed_user: db_models.User, db_session: Session
):
    """Проверка отписки одного пользователя от другого."""
    db_session.add(
        db_models.Follower(
            user_id=followed_user.id,
            follower_id=test_user.id,
        )
    )
    db_session.commit()

    result = cli_runner.invoke(users.users_app, ["unfollow", followed_user.nickname, test_user.nickname])
    assert result.exit_code == 0

    assert f"User {test_user.nickname!r} is now unfollow from user {followed_user.nickname!r}" in result.stdout

    follower_qs = db_session.query(db_models.Follower).where(
        and_(
            db_models.Follower.user_id == followed_user.id,
            db_models.Follower.follower_id == test_user.id,
        )
    )
    assert follower_qs.one_or_none() is None


def test_unfollow_from_self(cli_runner: CliRunner, test_user: db_models.User):
    """Проверка отписки от себя."""
    result = cli_runner.invoke(users.users_app, ["unfollow", test_user.nickname, test_user.nickname])
    assert result.exit_code == 0

    assert result.stdout == ""


@pytest.mark.parametrize(
    "user, follower",
    [
        ("test", "not_existed"),
        ("not_existed", "test"),
    ],
)
def test_unfollow_from_not_existed_users(cli_runner: CliRunner, test_user: db_models.User, user: str, follower: str):
    """Проверка невозможности отписаться от несуществующего пользователя."""
    user_nickname = test_user.nickname if user == "test" else follower
    follower_nickname = follower if user == "test" else test_user.nickname

    result = cli_runner.invoke(users.users_app, ["unfollow", user_nickname, follower_nickname])
    assert result.exit_code == 1

    expected_nickname = follower_nickname if user == "test" else user_nickname
    assert f"User {expected_nickname!r} not found" in result.stdout


def test_unfollow_from_user_again(
    cli_runner: CliRunner, test_user: db_models.User, followed_user: db_models.User, db_session: Session
):
    """Проверка идемпотентности команды отписки одного пользователя от другого."""
    db_session.add(
        db_models.Follower(
            user_id=followed_user.id,
            follower_id=test_user.id,
        )
    )
    db_session.commit()

    for _ in range(2):
        result = cli_runner.invoke(users.users_app, ["unfollow", followed_user.nickname, test_user.nickname])
        assert result.exit_code == 0

        assert f"User {test_user.nickname!r} is now unfollow from user {followed_user.nickname!r}" in result.stdout


@pytest.mark.parametrize("has_follow", [True, False])
def test_followed(
    cli_runner: CliRunner,
    test_user: db_models.User,
    followed_user: db_models.User,
    db_session: Session,
    has_follow: bool,
):
    """Проверка проверки наличия подписки одного пользователя на другого."""
    if has_follow:
        db_session.add(
            db_models.Follower(
                user_id=followed_user.id,
                follower_id=test_user.id,
            )
        )
        db_session.commit()

    result = cli_runner.invoke(users.users_app, ["followed", test_user.nickname, followed_user.nickname])
    assert result.exit_code == 0

    if has_follow:
        assert "followed" in result.stdout
    else:
        assert "not followed" in result.stdout


@pytest.mark.parametrize(
    "user, follower",
    [
        ("test", "not_existed"),
        ("not_existed", "test"),
    ],
)
def test_followed_not_existed_users(cli_runner: CliRunner, test_user: db_models.User, user: str, follower: str):
    """Проверка ошибки проверки подписки на несуществующего пользователя."""
    user_nickname = test_user.nickname if user == "test" else follower
    follower_nickname = follower if user == "test" else test_user.nickname

    result = cli_runner.invoke(users.users_app, ["followed", user_nickname, follower_nickname])
    assert result.exit_code == 1

    expected_nickname = follower_nickname if user == "test" else user_nickname
    assert f"User {expected_nickname!r} not found" in result.stdout
