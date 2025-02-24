import io
import re
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

from loguru import logger as loguru_logger
from pydantic import BaseModel, field_validator

# 日志级别
LOG_LEVELS = ['TRACE', 'DEBUG', 'INFO', 'SUCCESS', 'WARNING', 'ERROR', 'CRITICAL']


class ConfigModel(BaseModel):
    sink: Any = None
    level: str = 'INFO'
    format: Union[str, Callable, None] = '{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}'
    filter: Union[str, Callable, None] = None
    colorize: Union[str, bool, None] = None
    serialize: Union[str, bool, None] = None
    backtrace: Union[str, bool, None] = None
    diagnose: Union[str, bool, None] = None
    enqueue: Union[str, bool, None] = True
    catch: Union[str, bool, None] = None
    encoding: Optional[str] = None
    retention: Optional[str] = None
    rotation: Optional[str] = None
    compression: Optional[str] = None

    class Config:
        extra = 'allow'

    @field_validator('level')
    @classmethod
    def to_upper(cls, level: str) -> str:
        return level.upper()

    @field_validator('colorize', 'serialize', 'backtrace', 'diagnose', 'enqueue', 'catch')
    @classmethod
    def to_bool(cls, v: Union[str, bool]) -> bool:
        if isinstance(v, str):
            return v.lower() in ['true', '1']
        elif isinstance(v, bool):
            return v
        return False

    @field_validator('sink')
    @classmethod
    def validate_sink(cls, sink: Any) -> Any:
        if isinstance(sink, io.TextIOWrapper):
            return sink

        if isinstance(sink, str):
            sink_path = Path(sink)
        elif isinstance(sink, Path):
            sink_path = sink
        else:
            raise ValueError(f'Invalid sink type: {type(sink)}, must be one of [str, Path, io.TextIOWrapper]')

        if sink_path.exists() and not sink_path.is_file():
            raise ValueError(f'Invalid sink path: {sink_path}, must be a file')

        return sink_path

    @field_validator('level')
    @classmethod
    def validate_level(cls, level: str) -> str:
        _level = level.upper()
        if _level not in LOG_LEVELS:
            raise ValueError(f'Invalid log level: {level}, must be one of {LOG_LEVELS}')
        return _level


class FilterConfigModel(BaseModel):
    sensitive_fields: str = (
        '(password|token|key|secret|token|session|cookie|csrf|jwt|access_token|refresh_token'
        '|id_token|client_secret|client_id|api_key|secret_key)'
    )
    sensitive_fields_replacement: str = '********'
    max_length: int = 2000
    max_length_replacement: str = '......'

    class Config:
        extra = 'allow'

    @field_validator('sensitive_fields')
    @classmethod
    def validate_sensitive_fields(cls, sensitive_fields: str) -> str:
        if not re.match(r'^\((\w+\|)*\w+\)$', sensitive_fields):
            raise ValueError
        return sensitive_fields

    @field_validator('max_length')
    @classmethod
    def validate_max_length(cls, max_length: Union[int, str]) -> int:
        if isinstance(max_length, str):
            if not max_length.isdigit():
                raise ValueError
            _max_length = int(max_length)
        elif isinstance(max_length, int):
            _max_length = max_length
        else:
            raise ValueError
        return _max_length


class Filter:
    def __init__(self, name: str, configs: FilterConfigModel):
        self._name: str = name
        self._configs = configs
        self._funcs = []
        self._init_funcs()

    def __call__(self, record) -> bool:
        rst = True
        if record['extra'].get('name') != self._name:
            return False
        filter_funcs_name = [f for f in dir(self) if f.startswith('filter_')]
        for func_name in filter_funcs_name:
            if not hasattr(self, func_name):
                continue
            filter_func = getattr(self, func_name)
            rst = filter_func(record)
            if not rst:
                return rst
        return rst

    def _init_funcs(self):
        funcs_name = [i for i in dir(self) if i.startswith('filter_')]
        for func_name in funcs_name:
            if not hasattr(self, func_name):
                continue
            func = getattr(self, func_name)
            self._funcs.append(func)

    def filter_sensitive_fields(self, record) -> bool:
        message = record.get('message')
        if not message:
            return True

        pattern = re.compile(f'{self._configs.sensitive_fields}\\s+\\w+', re.IGNORECASE)
        new_message = re.sub(pattern, self._configs.sensitive_fields_replacement, message)
        record['message'] = new_message
        return True

    def filter_max_length(self, record) -> bool:
        message = record.get('message')
        if not message:
            return True

        max_length = self._configs.max_length
        if len(message) > max_length:
            record['message'] = f'{message[:max_length]}{self._configs.max_length_replacement}'
        return True


class Logger:
    TYPE = 'base'

    def __init__(self, configs_dict: Dict[str, Any], **kwargs):
        self.configs_dict = configs_dict
        self.kwargs = kwargs
        self.common_settings = self.configs_dict.get('common', {})
        self.self_settings = self.configs_dict.get(self.TYPE, {})
        self.env = self.kwargs.get('env', 'prod').lower()
        self._logger = loguru_logger.bind(name=self.TYPE)
        self.configs: Optional[ConfigModel] = None
        self.filter_configs: Optional[FilterConfigModel] = None
        self._init_configs()
        self._init_logger()

    def _init_configs(self): ...

    def _init_logger(self): ...

    @staticmethod
    def _merge_settings(com_settings: Dict[str, Any], self_settings: Dict[str, Any], keys: List[str]) -> Dict[str, Any]:
        _settings = {}
        for key in keys:
            com_value = com_settings.get(key, '')
            self_value = self_settings.get(key, '')
            value = self_value or com_value
            if value:
                new_key = key.replace('sh_', '').replace('fh_', '')
                _settings[new_key] = value
        return _settings

    def _log(self, level: str, message: str, *args: Any, **kwargs: Any):
        # 使用 opt 方法修正调用栈信息
        self._logger.opt(depth=2).log(level, message, *args, **kwargs)

    def trace(self, message: str, *args: Any, **kwargs: Any):
        self._log('TRACE', message, *args, **kwargs)

    def debug(self, message: str, *args: Any, **kwargs: Any):
        self._log('DEBUG', message, *args, **kwargs)

    def info(self, message: str, *args: Any, **kwargs: Any):
        self._log('INFO', message, *args, **kwargs)

    def warning(self, message: str, *args: Any, **kwargs: Any):
        self._log('WARNING', message, *args, **kwargs)

    def error(self, message: str, *args: Any, **kwargs: Any):
        self._log('ERROR', message, *args, **kwargs)

    def critical(self, message: str, *args: Any, **kwargs: Any):
        self._log('CRITICAL', message, *args, **kwargs)
