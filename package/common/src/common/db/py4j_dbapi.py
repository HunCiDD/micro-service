from datetime import date
from typing import Any, List, Optional, Tuple

from py4j.java_gateway import JavaGateway

# DB-API 2.0 Module
apilevel = '2.0'  # 支持 DB-API 2.0
threadsafety = 1  # 线程安全级别（1 表示线程可以共享模块，但不能共享连接）
paramstyle = 'qmark'  # 参数风格，使用问号占位符（如 "SELECT * FROM table WHERE id = ?"）


class TypeConverter:
    def __init__(self, gateway: JavaGateway) -> None:
        self.gateway = gateway
        self._jvm = gateway.jvm
        _j_types = self._jvm.Class.forName('java.sql.Types').getFields()  # type: ignore
        self._types = {x.getName(): x.getInt(None) for x in _j_types}

        self.strategies = {
            gateway.jvm.java.lang.Integer: int,  # type: ignore
            gateway.jvm.java.lang.String: str,  # type: ignore
            gateway.jvm.java.lang.Long: int,  # type: ignore
            gateway.jvm.java.lang.Boolean: bool,  # type: ignore
            gateway.jvm.java.lang.Double: float,  # type: ignore
            gateway.jvm.java.lang.Float: float,  # type: ignore
            gateway.jvm.java.sql.Date: date.fromisoformat,  # type: ignore
        }

    def convert(self, java_obj) -> Any:
        """将 Java 类型转换为 Python 类型"""
        if java_obj is None:
            return None

        java_cls = java_obj.getClass()
        for cls, strategy_func in self.strategies.items():
            if cls.isAssignableFrom(java_cls):  # type: ignore
                return strategy_func(java_obj)  # 调用策略函数并返回结果
        return str(java_obj)


# DB-API 2.0 Module Interface Exceptions
# 异常类
class Error(Exception):
    pass


class Warning(Exception):
    pass


class InterfaceError(Error):
    pass


class DatabaseError(Error):
    pass


class DataError(DatabaseError):
    pass


class OperationalError(DatabaseError):
    pass


class IntegrityError(DatabaseError):
    pass


class InternalError(DatabaseError):
    pass


class ProgrammingError(DatabaseError):
    pass


class NotSupportedError(DatabaseError):
    pass


# 连接对象
class Connection:
    def __init__(self, gateway: JavaGateway, db_type: str, host: str, port: int,
                 username: str, password: str, database: str, **kwargs):
        self.gateway = gateway
        self.db_type = db_type
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.database = database
        self.kwargs = kwargs

        self.jdbc_url = f'jdbc:{self.db_type}://{self.host}:{self.port}/{self.database}'

        self.closed = False
        self.j_connection = None
        self._init_j_connection()

    def _init_j_connection(self) -> None:
        """初始化 Java 连接"""
        try:
            # 加载 MySQL JDBC 驱动
            driver_class = self.gateway.jvm.Class
            driver_class.forName('com.mysql.cj.jdbc.Driver')  # type: ignore

            # 通过 Py4J 调用 Java 的 JDBC 接口
            self.j_connection = self.gateway.jvm.java.sql.DriverManager.getConnection(  # type: ignore
                self.jdbc_url,  # type: ignore
                self.username,
                self.password,
            )
            self.j_connection.setAutoCommit(False)  # type: ignore
        except Exception as e:
            raise OperationalError(f'Failed to connect to database: {e}')

    def close(self) -> None:
        """关闭连接"""
        if self.j_connection:
            self.j_connection.close()  # type: ignore
        self.closed = True

    def commit(self) -> None:
        """提交事务"""
        if self.closed:
            raise InterfaceError('Connection is closed')
        if self.j_connection is None:
            raise InterfaceError('Connection is not established')
        self.j_connection.commit()  # type: ignore

    def rollback(self) -> None:
        """回滚事务"""
        if self.closed:
            raise InterfaceError('Connection is closed')
        if self.j_connection is None:
            raise InterfaceError('Connection is not established')
        self.j_connection.rollback()  # type: ignore

    def cursor(self) -> 'Cursor':
        """创建游标对象"""
        if self.closed:
            raise InterfaceError('Connection is closed')
        return Cursor(self)


# 游标对象
class Cursor:
    def __init__(self, connection: Connection):
        self.connection = connection

        self.closed = False
        self._rs = None  # 结果集
        self._description: Optional[List[Tuple[str, str, None, None, None, None, None]]] = None  # 结果集的描述
        self._rowcount = -1  # 最近一次 execute 返回数据的行数或影响行数
        self._meta = None  # 元数据
        self._prep_stmt = None  # 预处理语句

    @property
    def description(self) -> Optional[List[Tuple[str, str, None, None, None, None, None]]]:
        """获取结果集的描述信息"""
        if self._description:
            return self._description

        descriptions = []
        if self._meta:
            meta_count = self._meta.getColumnCount()
            for i in range(1, meta_count + 1):
                column_name = self._meta.getColumnName(i)
                column_type = self._meta.getColumnTypeName(i)
                descriptions.append((column_name, column_type, None, None, None, None, None))
        self._description = descriptions
        return self._description

    def close(self) -> None:
        """关闭游标"""
        if not self.closed:
            self._close_rs()
            self._close_prep_stmt()
            self.closed = True

    def execute(self, sql: str, parameters: Optional[List[Any]] = None) -> None:
        """执行 SQL 语句"""
        self._before_execute()

        if self.closed:
            raise InterfaceError('Cursor is closed')
        if not sql.strip().upper().startswith(('SELECT', 'INSERT', 'UPDATE', 'DELETE')):
            raise ProgrammingError('Unsupported SQL statement')

        try:
            # 创建 PreparedStatement
            self._prep_stmt = self.connection.j_connection.prepareStatement(sql)  # type: ignore
            # 设置超时时间
            # if self.timeout > 0:
            #     self._prep_stmt.setQueryTimeout(self.timeout)
            # 参数预处理
            if parameters:
                self._set_prep_stmt(parameters)

            is_rs = self._prep_stmt.execute()
            if is_rs:
                self._rs = self._prep_stmt.getResultSet()
                self._meta = self._rs.getMetaData()
                self._rowcount = -1
            else:
                self._rowcount = self._prep_stmt.getUpdateCount()

        except Exception as e:
            raise DatabaseError(f'Failed to execute SQL: {e}')

    def fetchone(self) -> Optional[Tuple[Any, ...]]:
        """获取一条结果"""
        if self.closed or not self._rs:
            raise InterfaceError('Cursor is closed or no result set')
        if self._rs.next():
            return tuple(self._rs.getObject(i) for i in range(1, len(self.description) + 1))  # type: ignore
        return None

    def fetchall(self) -> List[Tuple[Any, ...]]:
        """获取所有结果"""
        if self.closed or not self._rs:
            raise InterfaceError('Cursor is closed or no result set')
        rows = []
        while self._rs.next():
            rows.append(tuple(self._rs.getObject(i) for i in range(1, len(self.description) + 1)))  # type: ignore
        return rows

    def fetchmany(self, size: Optional[int] = None) -> List[Tuple[Any, ...]]:
        """获取多条结果"""
        if self.closed or not self._rs:
            raise InterfaceError('Cursor is closed or no result set')
        if size is None:
            size = 1
        rows = []
        for _ in range(size):
            if self._rs.next():
                rows.append(tuple(self._rs.getObject(i) for i in range(1, len(self.description) + 1)))  # type: ignore
            else:
                break
        return rows

    def _before_execute(self) -> None:
        """执行 SQL 前的清理工作"""
        self._close_rs()
        self._close_prep_stmt()
        self._meta = None
        self._description = None

    def _close_rs(self) -> None:
        """关闭结果集"""
        if self._rs:
            self._rs.close()
        self._rs = None

    def _close_prep_stmt(self) -> None:
        """关闭预处理语句"""
        if self._prep_stmt:
            self._prep_stmt.close()
        self._prep_stmt = None

    def _set_prep_stmt(self, parameters: List[Any]) -> None:
        """设置预处理语句的参数"""
        for i, param in enumerate(parameters, start=1):
            self._prep_stmt.setObject(i, param)  # type: ignore


def connect(gateway: JavaGateway, db_type: str, host: str, port: int,
            username: str, password: str, database: str, **kwargs) -> Connection:
    """创建数据库连接"""
    return Connection(gateway, db_type, host, port, username, password, database, **kwargs)
