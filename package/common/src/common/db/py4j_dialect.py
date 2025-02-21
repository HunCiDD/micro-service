import json

from py4j.java_gateway import JavaGateway
from sqlalchemy.dialects import registry
from sqlalchemy.engine.default import DefaultDialect
from sqlalchemy.engine.url import URL

from src.db import py4j_dbapi


# 自定义Dialect
class Py4jDialect(DefaultDialect):
    name = 'py4j'
    driver = 'py4j'

    paramstyle = 'qmark'

    def __init__(self, gateway: JavaGateway, **kwargs):
        super().__init__(**kwargs)

        self.gateway = gateway
        self._json_deserializer = json.loads

    def create_connect_args(self, url: URL):
        name, db_type = url.drivername.split('+')
        if name != self.name:
            raise ValueError

        return (
            [],
            {
                'gateway': self.gateway,
                'db_type': db_type,
                'host': url.host,
                'port': url.port,
                'username': url.username,
                'password': url.password,
                'database': url.database,
            },
        )

    def do_begin(self, dbapi_connection):
        return super().do_begin(dbapi_connection)

    def do_commit(self, dbapi_connection):
        return super().do_commit(dbapi_connection)

    @classmethod
    def dbapi(cls):
        # 返回自定义的 DB-API 2.0 模块
        return py4j_dbapi


# 注册 Dialect
registry.register('py4j.mysql', __name__, 'Py4jDialect')
registry.register('py4j.gauss', __name__, 'Py4jDialect')
registry.register('py4j.oracle', __name__, 'Py4jDialect')
