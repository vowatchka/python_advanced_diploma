from fastapi import FastAPI

from .routers import api_router


def create_api() -> FastAPI:
    api = FastAPI(
        title="Twetty API",
        description="Корпоративный сервис микроблогов",
        version="1.0.0",
        contact={
            "name": "Владимир Салтыков",
            "url": "https://github.com/vowatchka",
            "email": "vowatchka@mail.ru"
        },
        license_info={
            "name": "MIT"
        },
    )

    api.include_router(api_router)

    return api
