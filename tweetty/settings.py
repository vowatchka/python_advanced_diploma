from environs import Env

env = Env()

DEBUG = env.bool("DEBUG", False)

# URL для обращения к статическим файлам
STATIC_URL = "/static"

# директория со статическими файлами
STATIC_DIR = "/app/tweetty/static"
