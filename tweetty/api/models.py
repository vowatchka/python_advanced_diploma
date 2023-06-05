from pydantic import BaseModel, Field, constr


class ResultModel(BaseModel):
    """Модель результата."""

    result: bool = Field(
        ...,
        title="Результат",
        description="Результат выполнения операции",
    )


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
        exclude=True,
    )


class NewTweetOut(ResultModel):
    """Модель ответа нового твита."""

    tweet_id: int = Field(
        ...,
        title="Id твита",
        description="Id добавленного твита",
    )
