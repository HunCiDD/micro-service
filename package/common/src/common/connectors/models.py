from src.utils.data import UuidGenerator
from src.utils.schemes import AddressModel


class InfrastructureModel(AddressModel):
    username: str = ''
    password: str = ''
    name: str = ''
    category: str = ''
    model: str = ''
    version: str = 'V1.0'
    description: str = ''

    class Config:
        extra = 'allow'


# 基础设施
class Infrastructure:
    def __init__(self, ip: str, port: int = 8080, username: str = '', password: str = '', **kwargs):
        self._model = InfrastructureModel(ip=ip, port=port, username=username, password=password, **kwargs)
        self._uuid = UuidGenerator.by_value(self.key)
        self._kwargs = kwargs

    @property
    def ip(self) -> str:
        return str(self._model.ip)

    @property
    def port(self) -> int:
        return self._model.port

    @property
    def netloc(self) -> str:
        return f'{self.ip}:{self.port}'

    @property
    def username(self) -> str:
        return self._model.username

    @property
    def password(self) -> str:
        return self._model.password

    @property
    def name(self) -> str:
        return self._model.name

    @property
    def category(self) -> str:
        return self._model.category

    @property
    def model(self) -> str:
        return self._model.model

    @property
    def version(self) -> str:
        return self._model.version

    @property
    def description(self) -> str:
        return self._model.description

    @property
    def key(self) -> str:
        return f'{self.model}://{self.netloc}@{self.username}'

    @property
    def uuid(self) -> str:
        return str(self._uuid)

    @property
    def kwargs(self) -> dict:
        return self._kwargs
