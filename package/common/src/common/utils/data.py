import json
import secrets
import string
import time
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Tuple
from uuid import NAMESPACE_DNS, UUID, uuid5

from numpy import int64, issubdtype, number
from pandas import DataFrame

__all__ = [
    'ConvertException',
    'FloatConverter',
    'StringConverter',
    'ListConverter',
    'DatetimeConverter',
    'JsonEncoder',
    'RandomStringGenerator',
    'RandomFloatGenerator',
    'UuidGenerator',
    'StringProcessor',
    'ListProcessor',
    'DictProcessor',
]


class ConvertException(Exception): ...


def convert_exception(func):
    def wrapper(data, **kwargs):
        try:
            return func(data, **kwargs)
        except Exception as e:
            if 'default' in kwargs:
                return kwargs['default']
            raise ConvertException(e) from e

    return wrapper


class ToIntMixin:
    @convert_exception
    @staticmethod
    def to_int(data, **kwargs) -> int:
        return int(data)


class ToDataFrameMixin:
    @convert_exception
    @staticmethod
    def to_dataframe(data, **kwargs) -> DataFrame:
        _columns = kwargs.get('columns', [])
        if _columns:
            return DataFrame(data, columns=_columns)
        return DataFrame(data)


class FloatConverter(ToIntMixin): ...


class StringConverter(ToIntMixin):
    @convert_exception
    @staticmethod
    def to_datetime(data: str, **kwargs) -> datetime:
        _format = kwargs.get('format', '%Y-%m-%d %H:%M:%S')
        return datetime.strptime(data, _format)


class ListConverter(ToDataFrameMixin):
    @convert_exception
    @staticmethod
    def to_string(data: list, **kwargs) -> str:
        _sep = str(kwargs.get('sep', ''))
        return _sep.join(data)


class DatetimeConverter:
    @convert_exception
    @staticmethod
    def to_string(data: datetime, **kwargs) -> str:
        _format = kwargs.get('format', '%Y-%m-%d %H:%M:%S')
        return data.strftime(_format)


class JsonEncoder(json.JSONEncoder):
    def default(self, o):
        result = None
        if isinstance(o, datetime):
            result = str(o)
        elif isinstance(o, Decimal):
            result = float(o)
        elif isinstance(o, UUID):
            result = str(o)
        elif isinstance(o, DataFrame):
            result = o.to_dict()
        elif isinstance(o, bytes):
            result = o.decode(encoding='utf-8')
        elif issubdtype(type(o), number):
            return float(o) if issubdtype(type(o), int64) else int(o)
        else:
            result = str(o)
        return result


class RandomIntGenerator:
    @staticmethod
    def by_range(start: int = 0, end: int = 10) -> int:
        secrets_generator = secrets.SystemRandom()
        return secrets_generator.randint(start, end)


class RandomStringGenerator:
    @staticmethod
    def by_length(length: int = 10) -> str:
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))


class RandomFloatGenerator:
    # Generate random floating-point numbers

    @staticmethod
    def by_range(start: float = 0.0, end: float = 1.0) -> float:
        secrets_generator = secrets.SystemRandom()
        return secrets_generator.uniform(start, end)


class UuidGenerator:
    @staticmethod
    def by_value(value: str, random: bool = False) -> UUID:
        random_num = RandomIntGenerator.by_range(0, 10000) if random else 0
        return uuid5(NAMESPACE_DNS, f'{value}{random_num}')

    @staticmethod
    def by_time(random: bool = False) -> UUID:
        random_num = RandomIntGenerator.by_range(0, 10000) if random else 0
        return uuid5(NAMESPACE_DNS, f'{time.time()}{random_num}')


class StringProcessor:
    @staticmethod
    def replace_keys(data: str, keys: Optional[List[Tuple[str, str]]] = None) -> str:
        if not keys:
            return data
        for old_key, new_key in keys:
            data = data.replace(old_key, new_key)
        return data


class ListProcessor:
    @staticmethod
    def deduplicate(data: list) -> list:
        return list(set(data))

    @staticmethod
    def range(data: list, limit: int = 0, offset: int = -1) -> list:
        return data[limit:offset]


class DictProcessor:
    @staticmethod
    def rename_keys(data: dict, key_map: Optional[dict] = None) -> dict:
        if not key_map:
            return data

        new_dict = {}
        for key, value in data.items():
            if key in key_map:
                new_dict[key_map[key]] = value
            else:
                new_dict[key] = value
        return new_dict

    @staticmethod
    def filter_keys(data: dict, keys: Optional[list] = None) -> dict:
        if not keys:
            return data
        return {k: v for k, v in data.items() if k in keys}

    @staticmethod
    def delete_keys(data: dict, keys: Optional[list] = None) -> dict:
        if not keys:
            return data
        return {k: v for k, v in data.items() if k not in keys}
