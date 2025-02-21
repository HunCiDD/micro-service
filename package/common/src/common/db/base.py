from sqlalchemy.engine import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase): ...


class DataBase:
    def __init__(self, url: str):
        self._url = url
        self.engine: Engine = create_engine(self._url, echo=True)
        self.session_factory = sessionmaker(self.engine, autoflush=False)

    def session(self) -> Session:
        return self.session_factory()

    def init(self, drop: bool = False):
        with self.engine.begin() as conn:
            if drop:
                Base.metadata.drop_all(conn)
            Base.metadata.create_all(conn)

    def create(self):
        with self.engine.begin() as conn:
            Base.metadata.create_all(conn)

    def drop(self):
        with self.engine.begin() as conn:
            Base.metadata.drop_all(conn)
