import os
import uuid
from pathlib import Path as OsPath
from typing import Annotated, BinaryIO, Union

import aiofiles
from fastapi import APIRouter, Depends, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from ...db import models
from ..auth import get_authorized_user
from ..exceptions import UploadFileSizeError, http_exception
from ..models import HTTPErrorModel, NewMediaIn, NewMediaOut

medias_router = APIRouter(prefix="/medias")


class UploadFileSizeValidator:
    def __init__(self, min_size: int = 1, max_size: int = 100 * 1024 * 1024):
        """
        Валидатор размера загружаемого файла.

        :param min_size: минимальный размер файла в байтах.
        :param max_size: максимальный размер файла в байтах.
        """
        self.min_size = min_size
        self.max_size = max_size

    async def __call__(self, media: UploadFile):
        file_data = await media.read()

        if len(file_data) < self.min_size:
            raise http_exception(UploadFileSizeError(f"file size less than {self.min_size} bytes"), status_code=411)
        elif len(file_data) > self.max_size:
            raise http_exception(UploadFileSizeError(f"file size grower than {self.max_size} bytes"), status_code=413)

        # не забываем сместить курсор в начало,
        # потому что ранее прочитали весь файл
        await media.seek(0)

        return media


upload_file_size_validator = UploadFileSizeValidator()


def generate_mediafile_name(media: UploadFile) -> str:
    """Генерирует уникальное имя медиа-файла."""
    return f"{uuid.uuid4()}{OsPath(media.filename).suffix}"


async def save_mediafile(path: Union[str, os.PathLike], media: BinaryIO):
    """
    Сохраняет медиа-файл, автоматически создавая директории расположения файла,
    если их нет.

    :param path: путь к файлу.
    :param media: двоичное (байты) содержимое сохраняемого файла.
    """
    _path = OsPath(path).resolve()
    os.makedirs(_path.parent, exist_ok=True)

    async with aiofiles.open(path, "wb") as f:
        await f.write(media.read())


@medias_router.post(
    "",
    summary="Опубликовать новый медиа",
    status_code=201,
    response_model=NewMediaOut,
    responses={
        520: {"model": HTTPErrorModel}
    },
    tags=["medias"]
)
async def publish_new_media(
    db_session: Annotated[AsyncSession, Depends(models.db_session)],
    auth_user: Annotated[models.User, Depends(get_authorized_user)],
    media: Annotated[UploadFile, Depends(upload_file_size_validator)],
    mediafile_name: Annotated[str, Depends(generate_mediafile_name)],
) -> NewMediaOut:
    """Публикация нового медиа."""
    media_file = OsPath(NewMediaIn.get_file_upload_path(auth_user.nickname, mediafile_name))

    try:
        async with db_session.begin_nested():
            # сохраняем файл на сервере
            await save_mediafile(media_file, media.file)

            # сохраняем в БД
            new_media = models.TweetMedia(
                rel_uri=str(media_file),
            )
            db_session.add(new_media)
    except Exception as ex:
        # удаляем загруженный файл в случае проблем
        if media_file.exists():
            os.remove(media_file)

        raise http_exception(ex, status_code=520)
    else:
        return NewMediaOut(result=True, media_id=new_media.id)