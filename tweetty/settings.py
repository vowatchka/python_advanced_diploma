from environs import Env

env = Env()

DEBUG = env.bool("DEBUG", False)

# URL для подключения к БД PostgreSQL
POSTGRES_URL = env("POSTGRES_URL")

# URL для обращения к статическим файлам
STATIC_URL = "/static"

# директория со статическими файлами
STATIC_DIR = "/app/tweetty/static"

# Префикс Api Key
API_KEY_PREFIX = "tweetty_"

# Количество байт для генерации токена
TOKEN_NBYTES = 42  # Why? Read Douglas Adams
