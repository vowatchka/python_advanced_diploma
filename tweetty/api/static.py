from ..settings import STATIC_DIR, STATIC_URL


def static_uri(path: str) -> str:
    """Преобразует переданный путь `path` в URI для статических файлов."""
    if path.startswith(STATIC_DIR):
        return path.replace(STATIC_DIR, STATIC_URL, 1)
    return path
