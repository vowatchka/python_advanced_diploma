from fastapi import HTTPException

from .models import ErrorModel

# описания кодов HTTP
HTTP_403_FORBIDDEN_DESC = "Forbidden"
HTTP_500_INTERNAL_SERVER_ERROR_DESC = "Internal Server Error"


def http_exception(ex: Exception, status_code: int = 500) -> HTTPException:
    """
    Возвращает экземпляр `fastapi.HTTPException`,
    содержащий информацию об исключении `ex`.

    :param ex: исключение.
    :param status_code: код ответа HTTP.
    """
    return HTTPException(
        status_code=status_code,
        detail=ErrorModel(
            result=False,
            type=ex.__class__.__name__,
            message=str(ex),
        ).dict(by_alias=True)
    )


class UploadFileSizeError(Exception):
    """Ошибка превышения опустимого размера загружаемого файла."""
    pass


class ForbiddenError(Exception):
    """Ошибка, возникающая при недостатке прав доступа к чему-либо."""
    pass
