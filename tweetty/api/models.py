from fastapi.params import File
from pydantic import BaseModel, constr, Field


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

    content: constr(
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
        upload_path = "/app/tweetty/static/upload"
        upload_path_template = upload_path + "/{nickname}/medias/{filename}"

    def __init__(self):
        super().__init__(
            title="Медиа-файл",
            description="Медиа-файл, прикрепляемый к твиту",
        )

    @classmethod
    def get_file_upload_path(cls, nickname: str, filename: str) -> str:
        """Возвращает путь к загружаемому файлу для пользователя."""
        return cls.MediaConfig.upload_path_template.format(
            nickname=nickname,
            filename=filename
        )


class NewMediaOut(ResultModel):
    """Модель ответа нового медиа."""

    media_id: int = Field(
        ...,
        title="Id медиа",
        description="Id добавленного медиа",
    )
