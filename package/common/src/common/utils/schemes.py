from ipaddress import ip_address
from typing import Any, TypeVar

from pydantic import BaseModel, field_validator

AddSchemaType = TypeVar('AddSchemaType', bound=BaseModel)
SetSchemaType = TypeVar('SetSchemaType', bound=BaseModel)


class AddressModel(BaseModel):
    ip: str = ''
    port: int = 8080

    @field_validator('ip')
    @classmethod
    def vaildate_ip(cls, ip: str) -> str:
        try:
            _ip = ip_address(ip)
        except Exception as e:
            raise ValueError(f'{e}')
        return _ip.exploded

    @field_validator('port')
    @classmethod
    def vaildate_port(cls, port: int) -> int:
        if 1 <= port <= 65535:
            return port
        raise ValueError('Port must in 0 ~ 65535')


# 定义统一的响应模型
class ResponseModel(BaseModel):
    code: int
    message: str
    data: Any = None
