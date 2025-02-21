import time
from threading import Condition, Lock, current_thread
from typing import Any, Generic, List, Optional, Type

from src.settings import APP_SETTINGS

from .connections.base import Base, ConnectionType
from .models import Infrastructure

run_logger = APP_SETTINGS.run_logger


class ConnectionPoolNoIdle(Exception):
    pass


class ConnectionPoolFull(Exception):
    pass


class ConnectionPoolClosed(Exception):
    pass


# 连接池
class ConnectionPool(Generic[ConnectionType], Base):
    _instance = {}
    _lock: Lock = Lock()

    def __new__(
        cls,
        connection_type: Type[ConnectionType],
        infrastructure: Infrastructure,
        agent: Any = None,
        name: str = '',
        max_num_idle: int = 3,
        max_num_conn: int = 10,
        **kwargs,
    ):
        with cls._lock:
            pool_name = cls.__name__
            key = f'{pool_name}_{infrastructure.uuid}'
            run_logger.info(f'New connection pool {key}.')
            if key in cls._instance:
                instance = cls._instance[key]
            else:
                instance = super().__new__(cls)
                cls._instance[key] = instance
        return instance

    def __init__(
        self,
        connection_type: Type[ConnectionType],
        infrastructure: Infrastructure,
        agent: Any = None,
        name: str = '',
        max_num_idle: int = 3,
        max_num_conn: int = 10,
        **kwargs,
    ):
        if hasattr(self, '_initialized') and self._initialized:
            # 防止重复初始化
            return

        self._initialized = False
        self._connection_type = connection_type
        self._infrastructure = infrastructure
        self._agent = agent
        self._name = name
        self.kwargs = kwargs
        # 连接池数量配置
        self._num_init: int = 0  # 初始连接数
        self._max_num_idle: int = max_num_idle  # 最大空闲， 缓存个数
        self._max_num_conn: int = max_num_conn
        self._min_num_idle: int = 1
        self._cur_num_idle: int = 0  # 当前空闲连接数
        self._cur_num_active: int = 0

        self._idle_connections = []  # 空闲连接
        self._active_connections = []  # 活跃连接

        self._blocked_requests = []  # 阻塞请求
        self._condition = Condition()

        self.idle_timeout = 1000
        self.closed = False

        self._init_connections()
        self._initialized = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    @property
    def total(self) -> int:
        """统计连接总数

        Returns:
            int: _description_
        """
        return self._cur_num_idle + self._cur_num_active

    @property
    def idle(self) -> bool:
        return True if self._cur_num_idle > 0 else False

    @property
    def full(self) -> bool:
        """
        总连接数是否已经满了，满了将无法新增连接
        :return:
        """
        return True if self.total >= self._max_num_conn else False

    def available_connection(self, connection: Optional[ConnectionType] = None) -> bool:
        """连接是否可用

        Args:
            connection (ConnectionType): _description_

        Returns:
            bool: _description_
        """
        if connection is None or not isinstance(connection, self._connection_type):
            return False
        return connection.is_available

    def _new_connection(self) -> Optional[ConnectionType]:
        """创建新连接

        Returns:
            Optional[ConnectionType]: _description_
        """
        try:
            connection = self._connection_type(self._infrastructure, self._agent)
            if not connection.is_available:
                run_logger.debug(f'New {connection} is not available')
                connection.close()
                return None
            run_logger.debug(f'New {connection} created successfully')
            return connection
        except Exception as e:
            run_logger.error(f'Failed to create a new connection: {e}')
            return None

    def _init_connections(self):
        """初始化连接"""
        connections = []
        loop, max_loop = 0, 10
        size = 0
        while size < self._max_num_idle and loop < max_loop:
            loop += 1
            size += 1
            connection = self._new_connection()
            if self.available_connection(connection):
                connections.append(connection)

        cur_num_idle = len(connections)
        if cur_num_idle < self._max_num_idle:
            run_logger.debug(message=f'Only init connections [{cur_num_idle}]')

        self._idle_connections.extend(connections)
        self._cur_num_idle += cur_num_idle

    def _get_connection(self) -> Optional[ConnectionType]:
        try:
            connection = self._idle_connections.pop()
            self._cur_num_idle -= 1
        except IndexError:
            raise ConnectionPoolNoIdle('No idle connections available')

        run_logger.debug(f'Get {connection}')
        self._active_connections.append(connection)
        self._cur_num_active += 1
        return connection

    @staticmethod
    def _close_connections(connections: Optional[List[ConnectionType]] = None):
        """关闭连接
        Args:
            connections (Optional[List[ConnectionType]], optional): _description_. Defaults to None.
        """
        if not connections:
            return

        for connection in connections:
            if not connection:
                continue

            try:
                connection.close()
            except Exception as e:
                run_logger.error(f'Failed closing {connection}: {e}')
        return

    def _close_idle_connections(self):
        """关闭空闲连接"""
        self._close_connections(self._idle_connections)
        self._idle_connections = []
        self._cur_num_idle = 0

    def _close_active_connections(self):
        self._close_connections(self._active_connections)
        self._active_connections = []
        self._cur_num_active = 0

    def _clear_idle_connections(self):
        """清理空闲连接，如果已经超时"""
        with self._condition:
            cur_time = time.time()

            # 需要关闭的连接
            connections_to_close = []
            for connection in self._idle_connections:
                if cur_time - connection.last_time >= self.idle_timeout:
                    connections_to_close.append(connection)
                else:
                    break  # 假设列表按last_time排序

            if connections_to_close:
                self._close_connections(connections_to_close)
                self._idle_connections = self._idle_connections[len(connections_to_close) :]
                self._cur_num_idle -= len(connections_to_close)
                run_logger.debug(f'Cleared {len(connections_to_close)} idle connections')

    def release(self, connection: ConnectionType) -> None:
        """释放连接

        Args:
            connection (ConnectionType): _description_
        """
        run_logger.info(f'Release {connection}.')
        if self.closed:
            # 如果这个连接是在连接池关闭后才释放，那就不用回连接池了
            connection.close()
            return

        with self._condition:
            # 如果连接记录在活跃连接中，删除
            if connection in self._active_connections:
                self._active_connections.remove(connection)
                self._cur_num_active -= 1

            available = self.available_connection(connection)
            if not available:
                # 如果这个连接不可用了，关闭
                connection.close()

                if not self.full and not self.idle:
                    # 连接池未满，无可用空闲，需要创建新的连接。因为还有其他线程等着连接用
                    new_connection = self._new_connection()
                    if new_connection:
                        self._idle_connections.append(new_connection)
                        self._cur_num_idle += 1
            else:
                if self.full or self._cur_num_idle >= self._max_num_idle:
                    # 如果连接池满了，或者 空闲已满，关闭
                    connection.close()
                else:
                    # 丢回空闲列表
                    self._idle_connections.append(connection)
                    self._cur_num_idle += 1

            # 判断是否存在空闲连接，通知其它线程
            if self._cur_num_idle > 0 and len(self._blocked_requests) > 0:
                self._condition.notify()

    def acquire(self, blocking: bool = True, timeout: Optional[float] = None) -> Optional[ConnectionType]:
        run_logger.debug('Acquire connection...')
        if self.closed:
            raise ConnectionPoolClosed('Connection pool is closed.')

        with self._condition:
            start_time = time.time()

            while True:
                if self._cur_num_idle > 0:
                    return self._get_connection()
                elif not self.full:
                    new_connection = self._new_connection()
                    if new_connection:
                        self._active_connections.append(new_connection)
                        self._cur_num_active += 1
                        return new_connection
                else:
                    # 判断空闲链接是已经满了
                    if not blocking:
                        raise ConnectionPoolFull('Connection pool is full')

                    # 等待，直达超时时间，或有空闲
                    if timeout is not None:
                        remaining = timeout - (time.time() - start_time)
                        if remaining <= 0:
                            raise ConnectionPoolFull('Connection pool acquire timed out')
                        run_logger.debug(
                            f'Thread {current_thread().name} waiting for connection with {remaining} seconds timeout...'
                        )
                        self._condition.wait(timeout=remaining)
                    else:
                        run_logger.debug(f'Thread {current_thread().name} waiting for connection indefinitely...')
                        self._condition.wait()

    def close(self):
        with self._condition:
            run_logger.debug('Close pool..')
            # 关闭空闲和活跃连接
            self._close_idle_connections()
            self._close_active_connections()
            self._blocked_requests = []
            self.closed = True
