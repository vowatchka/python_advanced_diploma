from typing import TypedDict

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
    def likes_route(tweet_id: int) -> str:
        """Возвращает роут лайков."""
        return f"/api/tweets/{tweet_id}/likes"

    @staticmethod
    def api_key_header(api_key: str) -> APIKeyHeader:
        """Возвращает заголовок `api-key`."""
        return {"api-key": api_key}

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


@pytest.fixture
def api_client(client: AsyncClient):
    yield APITestClient(client)
