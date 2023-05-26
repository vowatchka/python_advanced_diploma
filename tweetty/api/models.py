from dataclasses import dataclass

from pydantic import BaseModel, constr, Field


class ResultModel(BaseModel):
    """Модель результата."""

    result: bool = Field(
        ...,
        title="Результат",
        description="Результат выполнения операции",
    )


class NewTweetIn(BaseModel):
    """Модель запроса нового твита."""

    @dataclass(frozen=True)
    class _AvailContentLength:
        min: int = 1
        max: int = 280

    @dataclass(frozen=True)
    class _AvailMediaItems:
        min: int = 0
        max: int = 10

    content: constr(
        strip_whitespace=True,
        min_length=_AvailContentLength.min,
        curtail_length=_AvailContentLength.max
    ) = Field(
        ...,
        title="Содержимое твита",
        description="Содержимое твита",
        alias="tweet_data",
    )
    tweet_media_ids: list[int] = Field(
        default=list(),
        min_items=_AvailMediaItems.min,
        max_items=_AvailMediaItems.max,
        title="Медиа-файлы",
        description="Список медиа, прикрепленных к твиту",
        exclude=True,
    )

    @classmethod
    def avail_content_length(cls) -> _AvailContentLength:
        """Допустимая длина текста твита."""
        return cls._AvailContentLength()

    @classmethod
    def avail_media_items(cls) -> _AvailMediaItems:
        """Допустимое количество медиа-файлов, прикрепленных к твиту."""
        return cls._AvailMediaItems()


class NewTweetOut(ResultModel):
    """Модель ответа нового твита."""

    tweet_id: int = Field(
        ...,
        title="Id твита",
        description="Id добавленного твита",
    )
