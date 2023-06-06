import shutil
from pathlib import Path as OsPath
from pathlib import PosixPath, WindowsPath
from typing import BinaryIO, Union

import pytest
from fastapi import FastAPI, UploadFile
from httpx import AsyncClient
from pytest_mock import MockerFixture
from sqlalchemy import select
from sqlalchemy.exc import DatabaseError
from sqlalchemy.ext.asyncio import AsyncSession

from ...api import models as api_models
from ...api.routers import medias as media_routers
from ...db import models as db_models
from . import assert_http_error


class MockMediaConfig:
    """Конфиг, которым будем мокать."""
    upload_path = "/tests/static/upload"
    upload_path_template = upload_path + "/{nickname}/medias/{filename}"


@pytest.fixture(scope="session")
def test_file():
    """Тестовый файл для загрузки."""
    file_path = OsPath(__file__).parent.joinpath("imgs/test.png")
    _file = open(file_path, "rb")

    yield OsPath(_file.name).name, _file


@pytest.fixture
def test_file_uploaded_path(test_file: tuple[str, BinaryIO], test_user: db_models.User, mocker: MockerFixture):
    """Путь к загруженному тестовому файлу."""
    # мокаем конфиг
    mocker.patch.object(api_models.NewMediaIn, "MediaConfig", new=MockMediaConfig)

    # путь к загруженному тестовому файлу
    uploaded_file_path = OsPath(api_models.NewMediaIn.get_file_upload_path(
        nickname=test_user.nickname,
        filename=test_file[0]
    ))
    yield uploaded_file_path

    # удалаем загруженный тестовый файл после теста
    if OsPath(api_models.NewMediaIn.MediaConfig.upload_path).exists():
        shutil.rmtree(api_models.NewMediaIn.MediaConfig.upload_path)


def generate_mediafile_name(media: UploadFile) -> str:
    """
    Генерирует имя загружаемого файла для тестов.
    Данная функция должна использоваться для переопределения зависимостей приложения.
    """
    return media.filename


@pytest.mark.anyio
@pytest.mark.parametrize(
    "api_key",
    [
        "",
        "no" * 15,
    ]
)
async def test_publish_new_media_auth(client: AsyncClient, api_key: str, test_file: tuple[str, BinaryIO]):
    """Проверка авторизации для публикации нового медиа."""
    response = await client.post(
        "/api/medias",
        files={"media": test_file},
        headers={"api-key": api_key}
    )
    assert response.status_code == 401


@pytest.mark.anyio
async def test_publish_new_media(client: AsyncClient, test_user: db_models.User, test_file: tuple[str, BinaryIO],
                                 test_file_uploaded_path: Union[PosixPath, WindowsPath], db_session: AsyncSession):
    """Проверка публикации нового медиа."""
    response = await client.post(
        "/api/medias",
        files={"media": test_file},
        headers={"api-key": test_user.api_key},
    )
    assert response.status_code == 201

    resp = response.json()
    assert resp["result"] is True
    assert resp["media_id"] is not None

    # проверяем наличие загруженного тестового файла
    assert test_file_uploaded_path.exists()

    # проверяем, что медиа есть и в БД
    tweet_media_qs = await db_session.execute(
        select(db_models.TweetMedia).where(db_models.TweetMedia.id == resp["media_id"])
    )
    assert tweet_media_qs.scalar_one_or_none() is not None


@pytest.mark.anyio
async def test_rollback_uploaded_file(client: AsyncClient, test_user: db_models.User, test_file: tuple[str, BinaryIO],
                                      test_file_uploaded_path: Union[PosixPath, WindowsPath],
                                      mocker: MockerFixture, db_session: AsyncSession):
    """Проверка удаления загруженного файла, если не удается сохранить его в БД."""
    # мокаем объект БД
    error = DatabaseError("error", ("test",), TypeError("test"))
    mocker.patch.object(db_session, "add", autospec=True, side_effect=error)

    response = await client.post(
        "/api/medias",
        files={"media": test_file},
        headers={"api-key": test_user.api_key},
    )
    assert response.status_code == 520

    assert_http_error(response.json())

    assert not test_file_uploaded_path.exists()


@pytest.mark.anyio
async def test_save_mediafile(test_file_uploaded_path: Union[PosixPath, WindowsPath], test_file: tuple[str, BinaryIO]):
    """Проверка сохранения медиа-файла на диск."""
    assert not test_file_uploaded_path.exists()

    await media_routers.save_mediafile(str(test_file_uploaded_path), test_file[1])

    assert test_file_uploaded_path.exists()


@pytest.mark.anyio
@pytest.mark.parametrize(
    "min_size, max_size, expected_status_code",
    [
        (1, 5000, 413),
        (30000, 40000, 411),
    ]
)
async def test_upload_file_size(client: AsyncClient, test_user: db_models.User, test_file: tuple[str, BinaryIO],
                                api: FastAPI, min_size: int, max_size: int, expected_status_code: int):
    """Проверка ограничения размера загружаемого файла."""
    # мокаем зависимость
    mock_upload_file_size_validator = media_routers.UploadFileSizeValidator(min_size=min_size, max_size=max_size)
    api.dependency_overrides[media_routers.upload_file_size_validator] = mock_upload_file_size_validator

    response = await client.post(
        "/api/medias",
        files={"media": test_file},
        headers={"api-key": test_user.api_key},
    )
    assert response.status_code == expected_status_code
