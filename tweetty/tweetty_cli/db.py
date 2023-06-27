import contextlib
from typing import ContextManager, Iterator, Union

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from tweetty.settings import POSTGRES_URL

engine = create_engine(POSTGRES_URL, echo=False)
LocalSession = sessionmaker()


@contextlib.contextmanager  # type: ignore[arg-type]
def db_session() -> Union[ContextManager[Session], Iterator[Session]]:
    session: Session = LocalSession(bind=engine)
    try:
        yield session
    finally:
        session.close()
