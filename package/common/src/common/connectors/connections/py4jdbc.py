from typing import Any, Optional

from py4j.java_gateway import GatewayConnection, GatewayParameters, JavaGateway, java_import

from src.connectors.models import Infrastructure
from src.settings import APP_SETTINGS, Paths
from src.utils.schemes import AddressModel

from .base import BaseRequest, BaseResponse, Connection

api_logger = APP_SETTINGS.api_logger
run_logger = APP_SETTINGS.run_logger


class GatewayConfigsModel(AddressModel):
    db_type: str
    url: str
    driver: str
    jar: str

    class Config:
        extra = 'allow'


class Py4jdbcGateway:
    def __init__(self, configs: GatewayConfigsModel) -> None:
        self._configs = configs

        self._jar_path = Paths.LIB_JARS_DIR / self._configs.jar
        if not self._jar_path.exists() or not self._jar_path.is_file():
            raise ValueError(f'{self._jar_path} not exists or not file')

        if self._jar_path.suffix != '.jar':
            raise ValueError(f'{self._jar_path} not .jar')

        self._gw = None
        self._jvm = None
        self._gw_parameters = GatewayParameters(address=self._configs.ip, port=self._configs.port, read_timeout=60)
        run_logger.info(f'Initializing Py4j Java Gateway [{self}]...')

    def __str__(self) -> str:
        return f'Py4jdbc Gateway_{(self._configs.db_type, self._configs.port)}'

    @property
    def url(self) -> str:
        return self._configs.url

    @property
    def jvm(self):
        return self._jvm

    @property
    def is_running(self) -> bool:
        gw_conn = GatewayConnection(gateway_parameters=self._gw_parameters)
        try:
            gw_conn.socket.connect((gw_conn.address, gw_conn.port))
            return True
        except Exception as e:
            run_logger.error(f'{e}')
            return False

    def run(self):
        run_logger.info('run gw.')
        is_running = self.is_running
        run_logger.info(f'is running [{is_running}]')
        if is_running:
            self._gw = JavaGateway(gateway_parameters=self._gw_parameters)
            self._jvm = self._gw.jvm
        else:
            run_logger.info('launch..')
            self._gw = JavaGateway.launch_gateway(
                port=self._configs.port, classpath=str(self._jar_path), die_on_exit=True
            )
            self._jvm = self._gw.jvm
            java_import(self._jvm, 'java.sql.DriverManager')
            self._jvm.Class.forName(self._configs.driver)  # type: ignore

    def stop(self):
        run_logger.info('stop gw.')
        if self._gw:
            self._gw.shutdown()
            run_logger.info(f'Stop Py4j Java Gateway [{self}]')


class Py4jdbcResponse(BaseResponse): ...


class Py4jdbcRequest(BaseRequest): ...


class Py4jdbcConnection(Connection):
    def __init__(self, infrastructure: Infrastructure, agent: Any = None, **kwargs):
        super().__init__(infrastructure, agent, **kwargs)
        self.gateway = self._kwargs.get('gateway', None)
        if not self.gateway:
            raise ValueError

        self.db_name = self.infrastructure.kwargs.get('db_name')
        self.db_url = f'{self.gateway.url}://{self.infrastructure.ip}:{self.infrastructure.port}/{self.db_name}'

    @property
    def cursor(self):
        """
        Create a new cursor object.
        """
        return Py4jdbcCursor(self._client, self.gateway)

    def close(self):
        self._client.close()

    def commit(self):
        """
        Commit the current transaction.
        """
        self._client.commit()

    def rollback(self):
        """
        Roll back the current transaction.
        """
        self._client.rollback()

    def send(self, py4jdbc_request: Py4jdbcRequest, **kwargs) -> Py4jdbcResponse:  # type: ignore
        run_logger.debug('start.')
        if py4jdbc_request.AUTH_NEED and not self.is_auth:
            # 命令需要认证，当前又未认证过
            self._auth(py4jdbc_request, **kwargs)
        return self._send(py4jdbc_request, **kwargs)

    def _auth(self, py4jdbc_request: Optional[Py4jdbcRequest] = None, **kwargs):  # type: ignore
        try:
            self._client = self.gateway.jvm.java.sql.DriverManager.getConnection(
                self.db_url, self.infrastructure.username, self.infrastructure.password
            )
        except Exception:
            ...

    def _send(self, py4jdbc_request: Py4jdbcRequest, **kwargs) -> Py4jdbcResponse:  # type: ignore
        try:
            r = self.cursor.execute()  # type: ignore
        except Exception:
            ...


class Py4jdbcCursor:
    def __init__(self, connection, gateway):
        self._connection = connection
        self._gateway = gateway
        self._cursor = connection.createStatement()

    def close(self):
        """
        Close the cursor.
        """
        self._cursor.close()

    def execute(self, operation, parameters=None):
        """
        Execute an SQL query.

        :param operation: The SQL query to execute.
        :param parameters: The parameters to substitute into the query.
        """
        if parameters is not None:
            self._cursor.execute(operation, parameters)
        else:
            self._cursor.execute(operation)

    def fetchone(self):
        """
        Fetch the next row of the result set.
        """
        if self._cursor.next():
            return self._cursor.getString(1)
        else:
            return None

    def fetchall(self):
        """
        Fetch all rows of the result set.
        """
        result = []
        while self._cursor.next():
            result.append(self._cursor.getString(1))
        return result

    def fetchmany(self, size=0):
        """
        Fetch the next set of rows of the result set.

        :param size: The number of rows to fetch.
        """
        result = []
        for i in range(size):
            if self._cursor.next():
                result.append(self._cursor.getString(1))
            else:
                break
        return result

    def setinputsizes(self, sizes):
        """
        Set the input sizes for the parameters in a query.

        :param sizes: The sizes of the parameters.
        """
        pass

    def setoutputsize(self, size, column=None):
        """
        Set the output size for the columns in a query.

        :param size: The size of the output.
        :param column: The column to set the output size for.
        """
        pass
