from typing import Any, Callable, Dict, Optional, TypeVar

from src.connectors.models import Infrastructure
from src.settings import APP_SETTINGS
from src.utils.enums import EnumStatus
from src.utils.mixins import TypeMixin

run_logger = APP_SETTINGS.run_logger


class Base(TypeMixin):
    @property
    def settings(self) -> Dict[str, Any]:
        return APP_SETTINGS.connectors_settings.get(self.type, {})


# 响应
class BaseResponse(Base):
    def __init__(self, code: int, data: Any = None, status: EnumStatus = EnumStatus.SUCCESS, msg: str = '', **kwargs):
        self._code = code
        self._data = data
        self._status = status
        self._msg = msg
        self._kwargs = kwargs

    @property
    def code(self) -> int:
        return self._code

    @property
    def data(self) -> Any:
        return self._data

    @property
    def status(self) -> EnumStatus:
        return self._status

    @property
    def msg(self) -> str:
        return self._msg


# 请求
class BaseRequest(Base):
    """请求"""

    PROTOCOL = 'base'
    DESCRIBE = ''
    AUTH_NEED = True  # 请求是否需要认证

    def __init__(self, **kwargs):
        self._kwargs = kwargs
        self._init_request()

    @property
    def kwargs(self) -> dict:
        return self._kwargs

    def validator(self):
        """请求前校验"""
        ...

    def parser(self, data: Any) -> BaseResponse:
        """解析数据

        Args:
            data (Any, optional): _description_. Defaults to None.

        Returns:
            BaseResponse: _description_
        """
        return BaseResponse(code=100, data=data)

    def _get(self, key: str, default: Any = None, validator_func: Optional[Callable] = None) -> Any:
        """获取某个属性，通过key，并自动运行对应校验函数

        Args:
            key (str): _description_
            default (Any, optional): _description_. Defaults to None.
            validator_func (Optional[Callable], optional): _description_. Defaults to None.

        Returns:
            Any: _description_
        """

        # 优先类自定义的_key 获取， 其次从传参kwargs中获取
        if hasattr(self, f'_{key}'):
            value = getattr(self, f'_{key}')
        else:
            value = self._kwargs.get(key, default)

        # 是否存在自定义校验函数
        if validator_func and callable(validator_func):
            return validator_func(value)

        # 当前Request类中是否存在 已定义校验函数
        validator_func_name = f'_validator_{key}'
        if not hasattr(self, validator_func_name):
            # 不存在
            return value

        validator_func = getattr(self, validator_func_name)
        if not callable(validator_func):
            return value

        # 存在
        return validator_func(value)

    def _init_request(self): ...


class Connection(Base):
    """连接"""

    def __init__(self, infrastructure: Infrastructure, agent: Any = None, **kwargs):
        self._infrastructure = infrastructure
        self.netloc = self._infrastructure.netloc
        self._client = None
        self._agent = agent
        self._kwargs = kwargs
        self._is_auth = False

    def __str__(self) -> str:
        return f'{self.type}_{self.infrastructure.uuid}'

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    @property
    def infrastructure(self) -> Infrastructure:
        return self._infrastructure

    @property
    def is_auth(self) -> bool:
        return self._is_auth

    @property
    def is_available(self) -> bool:
        return True

    def close(self): ...

    def send(self, cmd_request: BaseRequest, **kwargs) -> BaseResponse:
        if not self.is_auth:
            self._auth(cmd_request, **kwargs)
        return self._send(cmd_request, **kwargs)

    def _auth(self, cmd_request: Optional[BaseRequest] = None, **kwargs):
        # 认证
        ...

    def _send(self, cmd_request: BaseRequest, **kwargs) -> BaseResponse: ...


# 连接类型
ConnectionType = TypeVar('ConnectionType', bound=Connection)
