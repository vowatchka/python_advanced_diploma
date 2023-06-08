from typing import BinaryIO, Optional, TypedDict

import pytest
from httpx import AsyncClient, Response


def assert_http_error(resp: dict):
    """Проверка ответа при ошибке."""
    assert "detail" in resp

    detail = resp["detail"]
    assert "result" in detail
    assert detail["result"] is False
    assert "error_type" in detail
    assert isinstance(detail["error_type"], str)
    assert "error_message" in detail
    assert isinstance(detail["error_message"], str)


APIKeyHeader = TypedDict("APIKeyHeader", {"api-key": str})


class APITestClient:
    def __init__(self, client: AsyncClient):
        """
        Клиент для доступа к API.

        :param client: оригинальный клиент httpx.
        """
        self._client = client

    @staticmethod
    def tweets_route(tweet_id: Optional[int] = None) -> str:
        """Возвращает роут твитов."""
        route = "/api/tweets"
        if tweet_id is not None:
            route += f"/{tweet_id}"
        return route

    @staticmethod
    def medias_route() -> str:
        """Возвращает роут медиа."""
        return "/api/medias"

    @staticmethod
    def likes_route(tweet_id: int) -> str:
        """Возвращает роут лайков."""
        return f"/api/tweets/{tweet_id}/likes"

    @staticmethod
    def follow_route(user_id: int) -> str:
        """Возвращает роут подписки."""
        return f"/api/users/{user_id}/follow"

    @staticmethod
    def api_key_header(api_key: str) -> APIKeyHeader:
        """Возвращает заголовок `api-key`."""
        return {"api-key": api_key}

    async def publish_tweet(self, json_data: dict, api_key: str) -> Response:
        """Опубликовать твит."""
        return await self._client.post(
            self.tweets_route(),
            json=json_data,
            headers=self.api_key_header(api_key),
        )

    async def delete_tweet(self, tweet_id: int, api_key: str) -> Response:
        """Удалить твит."""
        return await self._client.delete(
            self.tweets_route(tweet_id=tweet_id),
            headers=self.api_key_header(api_key),
        )

    async def upload_media(self, files: tuple[str, BinaryIO], api_key: str) -> Response:
        """Загрузить медиа."""
        return await self._client.post(
            self.medias_route(),
            files={"media": files},
            headers=self.api_key_header(api_key),
        )

    async def like(self, tweet_id: int, api_key: str) -> Response:
        """Поставить лайк."""
        return await self._client.post(
            self.likes_route(tweet_id),
            headers=self.api_key_header(api_key),
        )

    async def unlike(self, tweet_id: int, api_key: str) -> Response:
        """Снять лайк."""
        return await self._client.delete(
            self.likes_route(tweet_id),
            headers=self.api_key_header(api_key),
        )

    async def follow(self, user_id: int, api_key: str) -> Response:
        """Подписаться на пользователя."""
        return await self._client.post(
            self.follow_route(user_id),
            headers=self.api_key_header(api_key),
        )


@pytest.fixture
def api_client(client: AsyncClient):
    yield APITestClient(client)
