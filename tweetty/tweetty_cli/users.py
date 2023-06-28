import secrets
from typing import Annotated, Optional

import typer
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from tweetty.settings import API_KEY_PREFIX, TOKEN_NBYTES

from ..db import models as db_models
from .db import db_session

users_app = typer.Typer(no_args_is_help=True, help="Manage users")


def _get_user_or_exit(session: Session, nickname: str) -> db_models.User:
    user: db_models.User = (session.query(db_models.User)
                            .where(db_models.User.nickname == nickname)
                            .one_or_none())

    if not user:
        print(f"User {nickname!r} not found")
        raise typer.Exit(code=1)

    return user


def _generate_api_key() -> str:
    api_key = secrets.token_urlsafe(TOKEN_NBYTES)
    if API_KEY_PREFIX:
        return API_KEY_PREFIX + api_key
    return api_key


def _print_user(user: db_models.User, show_api_key: bool = False, msg_prefix: str = ""):
    msg = (f"Nickname: {user.nickname}\n"
           f"First name: {user.first_name}\n"
           f"Last name: {user.last_name}\n")
    if show_api_key:
        msg = f"{msg}Api Key: {user.api_key}\n"
    if msg_prefix:
        msg = f"{msg_prefix}{msg}"

    print(msg)


def _print_users(users: list[db_models.User], page: int, limit: int, show_api_key: bool = False):
    print(f"Page {page}. Users per page: {limit}\n")
    [_print_user(user, show_api_key=show_api_key) for user in users]


@users_app.command(no_args_is_help=True)
def add(
    nickname: Annotated[str, typer.Argument(help="User nickname")],
    first_name: Annotated[Optional[str], typer.Option("-f", "--first-name", help="User first name")] = None,
    last_name: Annotated[Optional[str], typer.Option("-l", "--last-name", help="User last name")] = None,
):
    """Add new user"""
    with db_session() as session:
        new_user = db_models.User(
            nickname=nickname,
            first_name=first_name,
            last_name=last_name,
            api_key=_generate_api_key()
        )
        session.add(new_user)
        session.commit()

        _print_user(new_user, show_api_key=True, msg_prefix="User added.\n")


@users_app.command(no_args_is_help=True)
def remove(
    nickname: Annotated[str, typer.Argument(help="User nickname")],
):
    """Remove user"""
    with db_session() as session:
        (session.query(db_models.User)
         .where(db_models.User.nickname == nickname)
         .delete())

        session.commit()
        print(f"User {nickname!r} deleted")


@users_app.command(no_args_is_help=True)
def update(
    nickname: Annotated[str, typer.Argument(help="User nickname")],
    first_name: Annotated[Optional[str], typer.Option("-f", "--first-name", help="User first name")] = None,
    last_name: Annotated[Optional[str], typer.Option("-l", "--last-name", help="User last name")] = None,
    reset_first_name: Annotated[bool, typer.Option("-rf", "--reset-first-name", help="Reset first name")] = False,
    reset_last_name: Annotated[bool, typer.Option("-rl", "--reset-last-name", help="Reset last name")] = False,
):
    """Update user"""
    with db_session() as session:
        user: db_models.User = _get_user_or_exit(session, nickname)

        if reset_first_name:
            user.first_name = None
        elif first_name is not None:
            user.first_name = first_name

        if reset_last_name:
            user.last_name = None
        elif last_name is not None:
            user.last_name = last_name

        session.commit()

        print(f"User {nickname!r} updated")


@users_app.command(name="new_api_key", no_args_is_help=True)
def new_api_key(
    nickname: Annotated[str, typer.Argument(help="User nickname")],
):
    """Generate new Api Key for user and replace old"""
    with db_session() as session:
        user: db_models.User = _get_user_or_exit(session, nickname)

        user.api_key = _generate_api_key()
        session.commit()

        print(f"New Api Key for user {nickname!r}: {user.api_key}")


@users_app.command(no_args_is_help=True)
def get(
    nickname: Annotated[str, typer.Argument(help="User nickname")],
    show_api_key: Annotated[bool, typer.Option("-a", "--show-api-key", help="Show Api Key")] = False
):
    """Get user"""
    with db_session() as session:
        user: db_models.User = _get_user_or_exit(session, nickname)

        _print_user(user, show_api_key=show_api_key)


@users_app.command(name="list")
def _list(
    page: Annotated[int, typer.Option("-p", "--page", help="Page")] = 1,
    limit: Annotated[int, typer.Option("-l", "--limit", help="Users per page")] = 10,
    show_api_key: Annotated[bool, typer.Option("-a", "--show-api-key", help="Show Api Key")] = False
):
    """Get users list"""
    with db_session() as session:
        users: list[db_models.User] = (
            session.query(db_models.User)
            .order_by(db_models.User.nickname)
            .offset(limit * (page - 1))
            .limit(limit)
            .all()
        )

        _print_users(users, page, limit, show_api_key=show_api_key)


@users_app.command(no_args_is_help=True)
def search(
    text: Annotated[str, typer.Argument(help="Searched text")],
    page: Annotated[int, typer.Option("-p", "--page", help="Page")] = 1,
    limit: Annotated[int, typer.Option("-l", "--limit", help="Users per page")] = 10,
    show_api_key: Annotated[bool, typer.Option("-a", "--show-api-key", help="Show Api Key")] = False
):
    """Search users"""
    with db_session() as session:
        like_expr = f"%{text}%"

        users: list[db_models.User] = (
            session.query(db_models.User)
            .where(
                or_(
                    db_models.User.nickname.like(like_expr),
                    db_models.User.first_name.like(like_expr),
                    db_models.User.last_name.like(like_expr)
                )
            )
            .order_by(db_models.User.nickname)
            .offset(limit * (page - 1))
            .limit(limit)
            .all()
        )

        _print_users(users, page, limit, show_api_key=show_api_key)


@users_app.command(no_args_is_help=True)
def follow(
    user_nickname: Annotated[str, typer.Argument(help="User nickname")],
    follower_nickname: Annotated[str, typer.Argument(help="Follower nickname")],
):
    """Follow user to user"""
    if user_nickname == follower_nickname:
        print("Follow to himself is not acceptable")
        raise typer.Exit(code=1)

    with db_session() as session:
        user = _get_user_or_exit(session, user_nickname)
        follower = _get_user_or_exit(session, follower_nickname)

        session.add(
            db_models.Follower(
                user_id=user.id,
                follower_id=follower.id,
            )
        )
        session.commit()

        print(f"User {follower_nickname!r} is now follow to user {user_nickname!r}")


@users_app.command(no_args_is_help=True)
def unfollow(
    user_nickname: Annotated[str, typer.Argument(help="User nickname")],
    follower_nickname: Annotated[str, typer.Argument(help="Follower nickname")],
):
    """Unfollow user from user"""
    with db_session() as session:
        user = _get_user_or_exit(session, user_nickname)
        follower = _get_user_or_exit(session, follower_nickname)

        db_follower = (
            session.query(db_models.Follower)
            .where(
                and_(
                    db_models.Follower.user_id == user.id,
                    db_models.Follower.follower_id == follower.id
                )
            )
            .one_or_none()
        )
        if db_follower:
            session.delete(db_follower)
            session.commit()

        if user_nickname != follower_nickname:
            print(f"User {follower_nickname!r} is now unfollow from user {user_nickname!r}")


@users_app.command(no_args_is_help=True)
def followed(
    user_nickname: Annotated[str, typer.Argument(help="User nickname")],
    follower_nickname: Annotated[str, typer.Argument(help="Follower nickname")],
):
    """Check that user follow to user"""
    with db_session() as session:
        user = _get_user_or_exit(session, user_nickname)
        follower = _get_user_or_exit(session, follower_nickname)

        db_follower = (
            session.query(db_models.Follower)
            .where(
                and_(
                    db_models.Follower.user_id == user.id,
                    db_models.Follower.follower_id == follower.id
                )
            )
            .one_or_none()
        )

        if db_follower:
            print("followed")
        else:
            print("not followed")
