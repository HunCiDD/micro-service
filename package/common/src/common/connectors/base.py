from typing import Type

from src.connectors.models import Infrastructure
from src.settings import APP_SETTINGS

from .connections.base import ConnectionType
from .pool import ConnectionPool

run_logger = APP_SETTINGS.run_logger


class Connector:
    def __init__(self, connection_type: Type[ConnectionType], infrastructure: Infrastructure, agent=None, **kwargs):
        run_logger.debug('start')
        self._connection_type = connection_type
        self._infrastructure = infrastructure
        self._kwargs = kwargs
        self._agent = agent
        self._pool = ConnectionPool[connection_type](
            self._connection_type, self._infrastructure, agent=self._agent, **self._kwargs
        )

    @property
    def pool(self) -> ConnectionPool:
        return self._pool
