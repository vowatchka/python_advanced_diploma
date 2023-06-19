from environs import Env

env = Env()

DEBUG = env.bool("DEBUG", False)

# URL для подключения к БД PostgreSQL
POSTGRES_URL = env("POSTGRES_URL")

# URL для обращения к статическим файлам
STATIC_URL = "/static"

# директория со статическими файлами
STATIC_DIR = "/app/tweetty/static"
