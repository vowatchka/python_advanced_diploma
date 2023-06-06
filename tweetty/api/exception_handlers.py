from fastapi.requests import Request
from fastapi.responses import JSONResponse

from .models import ErrorModel, HTTPErrorModel


async def common_exception_handler(_: Request, ex: Exception) -> JSONResponse:
    """Общий обработчик исключений."""
    error_data = ErrorModel(
        result=False,
        type=ex.__class__.__name__,
        message=str(ex),
    )

    return JSONResponse(
        HTTPErrorModel(detail=error_data).dict(by_alias=True),
        status_code=500
    )
