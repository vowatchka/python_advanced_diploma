from fastapi import FastAPI
from fastapi.middleware import Middleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import tweetty

from ..settings import DEBUG, STATIC_DIR, STATIC_URL
from .exception_handlers import common_exception_handler
from .models import HTTPErrorModel
from .routers import api_router


def create_api() -> FastAPI:
    middlewares = [
        Middleware(
            cls=CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        ),
    ]

    api = FastAPI(
        title="Twetty API",
        description="Корпоративный сервис микроблогов",
        version=tweetty.__version__,
        contact={
            "name": tweetty.__author__,
            "url": "https://github.com/vowatchka",
            "email": tweetty.__email__,
        },
        license_info={
            "name": tweetty.__license__,
        },
        middleware=middlewares,
        exception_handlers={
            Exception: common_exception_handler,
        },
        responses={
            401: {"model": HTTPErrorModel, "description": "Unauthorized"},
        },
    )

    api.include_router(api_router)

    if DEBUG:
        api.mount(STATIC_URL, StaticFiles(directory=STATIC_DIR), name="static")

    return api
