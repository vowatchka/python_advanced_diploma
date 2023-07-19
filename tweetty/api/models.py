from typing import Any

from fastapi.params import File
from pydantic import BaseModel, Field, constr
from pydantic.utils import GetterDict

from ..db import models as db_models
from ..settings import STATIC_DIR
from .static import static_uri


class ResultModel(BaseModel):
    """Модель результата."""

    result: bool = Field(
        ...,
        title="Результат",
        description="Результат выполнения операции",
    )


class ErrorModel(ResultModel):
    """Модель ошибки."""

    type: str = Field(
        ...,
        title="Тип ошибки",
        description="Тип ошибки",
        alias="error_type",
    )
    message: str = Field(
        ...,
        title="Сообщение об ошибке",
        description="Подробное сообщение об ошибке",
        alias="error_message",
    )

    class Config:
        allow_population_by_field_name = True
        schema_extra = {
            "example": {
                "result": False,
                "error_type": "string",
                "error_message": "string",
            }
        }


class HTTPErrorModel(BaseModel):
    """Модель ответа при ошибке."""

    detail: ErrorModel


class NewTweetIn(BaseModel):
    """Модель запроса нового твита."""

    class ContentFieldConfig:
        min_length: int = 1
        curtail_length: int = 280

    class MediasFieldConfig:
        min_items: int = 0
        max_items: int = 10

    content: constr(  # type: ignore[valid-type]
        strip_whitespace=True,
        min_length=ContentFieldConfig.min_length,
        curtail_length=ContentFieldConfig.curtail_length,
    ) = Field(
        ...,
        title="Содержимое твита",
        description="Содержимое твита",
        alias="tweet_data",
    )
    medias: list[int] = Field(
        default=list(),
        min_items=MediasFieldConfig.min_items,
        max_items=MediasFieldConfig.max_items,
        title="Медиа-файлы",
        description="Список медиа, прикрепленных к твиту",
        alias="tweet_media_ids",
        unique_items=True,
        exclude=True,
    )


class NewTweetOut(ResultModel):
    """Модель ответа нового твита."""

    tweet_id: int = Field(
        ...,
        title="Id твита",
        description="Id добавленного твита",
    )


class NewMediaIn(File):
    """Модель запроса нового медиа."""

    class MediaConfig:
        upload_path = STATIC_DIR + "/upload"
        upload_path_template = upload_path + "/{nickname}/medias/{filename}"

    def __init__(self):
        super().__init__(
            title="Медиа-файл",
            description="Медиа-файл, прикрепляемый к твиту",
        )

    @classmethod
    def get_file_upload_path(cls, nickname: str, filename: str) -> str:
        """Возвращает путь к загружаемому файлу для пользователя."""
        return cls.MediaConfig.upload_path_template.format(nickname=nickname, filename=filename)


class NewMediaOut(ResultModel):
    """Модель ответа нового медиа."""

    media_id: int = Field(
        ...,
        title="Id медиа",
        description="Id добавленного медиа",
    )


class BaseUser(BaseModel):
    """Базовая модель пользователя."""

    id: int = Field(
        ...,
        title="Id автора твита",
        description="Id автора твита",
    )
    nickname: str = Field(
        ...,
        title="Имя автора твита",
        description="Имя автора твита",
        alias="name",
    )

    class Config:
        orm_mode = True
        allow_population_by_field_name = True


class UserGetter(GetterDict):
    """
    Класс `UserGetter` служит для получения `tweetty.db.models.User`
    в модели Pydantic.
    """

    def get(self, key: Any, default: Any = None) -> Any:
        value = super().get(key, default=default)

        if isinstance(self._obj, db_models.User):
            if key == "followers":
                return [BaseUser.from_orm(follower.follower) for follower in self._obj.followers]
            elif key == "following":
                return [BaseUser.from_orm(following.user) for following in self._obj.followings]

        return value


class UserWithFollowers(BaseUser):
    """Модель пользователя с подписчиками."""

    followers: list[BaseUser] = Field(
        list(),
        title="Подписчики",
        description="Подписчики",
        unique_items=True,
        example=[BaseUser(id=0, name="string")],
    )
    following: list[BaseUser] = Field(
        list(),
        title="На кого подписан",
        description="На кого подписан",
        unique_items=True,
        example=[BaseUser(id=0, name="string")],
    )

    class Config:
        orm_mode = True
        getter_dict = UserGetter


class TweetGetter(GetterDict):
    """
    Класс `TweetGetter` служит для получения `tweetty.db.models.Tweet`
    в модели Pydantic.
    """

    def get(self, key: Any, default: Any = None) -> Any:
        value = super().get(key, default=default)

        if isinstance(self._obj, db_models.Tweet):
            if key == "medias":
                return [static_uri(media.rel_uri) for media in self._obj.medias]
            elif key == "likes":
                return [BaseUser.from_orm(user) for user in self._obj.liked_by_users]

        return value


class TweetOut(BaseModel):
    """Модель твита."""

    id: int = Field(
        ...,
        title="Id твита",
        description="Id твита",
    )
    content: str = Field(
        ...,
        title="Содержимое твита",
        description="Содержимое твита",
    )
    user: BaseUser = Field(
        ...,
        title="Автор твита",
        description="Автор твита",
        alias="author",
    )
    medias: list[str] = Field(
        list(),
        title="Список медиа",
        description="Список медиа, прикрепленных к твиту",
        alias="attachments",
    )
    likes: list[BaseUser] = Field(
        list(),
        title="Лайки",
        description="Лайки",
        unique_items=True,
    )

    class Config:
        orm_mode = True
        allow_population_by_field_name = True
        getter_dict = TweetGetter


class TweetListOut(ResultModel):
    """Модель списка твитов."""

    tweets: list[TweetOut] = Field(
        list(),
        title="Список твитов",
        description="Список твитов пользователя",
        example=[
            TweetOut(
                id=0,
                content="string",
                user=BaseUser(
                    id=0,
                    name="tring",
                ),
                attachments=["string"],
                likes=[
                    BaseUser(
                        id=0,
                        name="string",
                    ),
                ],
            ).dict(by_alias=True)
        ],
    )


class UserResultOut(ResultModel):
    """Модель результата запроса пользователя."""

    user: UserWithFollowers = Field(
        ...,
        title="Пользователь",
        description="Пользователь",
    )
