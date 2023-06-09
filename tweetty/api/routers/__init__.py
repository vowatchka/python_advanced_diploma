from fastapi import APIRouter

from .medias import medias_router
from .tweets import tweets_router
from .users import users_router

api_router = APIRouter(prefix="/api")
api_router.include_router(tweets_router)
api_router.include_router(medias_router)
api_router.include_router(users_router)
