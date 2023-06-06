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
