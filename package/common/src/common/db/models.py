from datetime import datetime
from typing import TypeVar

from sqlalchemy import Column, DateTime, String

from src.db.base import Base
from src.utils.data import UuidGenerator


class PKMixin:
    id = Column(
        String(length=64),
        primary_key=True,
        default=lambda: f'{UuidGenerator.by_value(datetime.now().isoformat(), True)}',
    )


class TimeAtMixin:
    created_at = Column(DateTime(), default=datetime.now)
    updated_at = Column(DateTime(), default=datetime.now, onupdate=datetime.now)


class BaseModel(Base):
    __abstract__ = True

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


ModelType = TypeVar('ModelType', bound=BaseModel)
