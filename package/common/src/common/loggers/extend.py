import sys
from contextvars import ContextVar

from .base import Logger, ConfigModel, FilterConfigModel, Filter


class ConsoleLogger(Logger):
    TYPE = 'console'

    def _init_configs(self):
        if self.env == 'prod':
            return

        sh_keys = ['sh_format', 'sh_level', 'sh_colorize']
        sh_settings = self._merge_settings(self.common_settings, self.self_settings, sh_keys)
        self.configs = ConfigModel(**sh_settings)

    def _init_logger(self):
        if self.env == 'prod' or self.configs is None:
            return

        sh_configs = self.configs.model_dump(exclude_none=True)
        if sh_configs:
            self._logger.remove()
            self._logger.add(sink=sys.stdout, **sh_configs)


class FileLogger(Logger):
    def _init_configs(self):
        # 添加过滤器配置
        filter_keys = list(FilterConfigModel.model_fields)
        filter_settings = self._merge_settings(self.common_settings, self.self_settings, filter_keys)
        self.filter_configs = FilterConfigModel(**filter_settings)
        logger_filter = Filter(self.TYPE, self.filter_configs) if self.filter_configs else None

        fh_keys = [f'fh_{key}' for key in list(ConfigModel.model_fields)]
        fh_settings = self._merge_settings(self.common_settings, self.self_settings, fh_keys)
        self.configs = ConfigModel(filter=logger_filter, **fh_settings)

    def _init_logger(self):
        if self.configs is None:
            return

        fh_configs_dict = self.configs.model_dump(exclude_none=True)
        if fh_configs_dict and 'sink' in fh_configs_dict:
            self._logger.add(**fh_configs_dict)
        else:
            raise ValueError(f'Invalid file logger configs[{self.TYPE}], no sink configured')


class RunLogger(FileLogger):
    TYPE = 'run'


class ApiLogger(FileLogger):
    TYPE = 'api'


class AgentLogger(FileLogger):
    TYPE = 'agent'


class OperateLoggerContext:
    request_id_var = ContextVar('request_id', default='N/A')
    user_id_var = ContextVar('user_id', default='N/A')
    ip_var = ContextVar('ip', default='N/A')


class OperateLogger(FileLogger):
    TYPE = 'operate'

    def _init_configs(self):
        super()._init_configs()

        if self.configs is None:
            return
        self.configs.format = self._formatter

    @staticmethod
    def _formatter(record) -> str:
        # 获取基本审计日志信息, 操作时间、用户标识、操作类型、操作对象、来源地址
        request_id = OperateLoggerContext.request_id_var.get()
        user_id = OperateLoggerContext.user_id_var.get()
        ip = OperateLoggerContext.ip_var.get()
        operation_type = record['extra'].get('operation_type', 'N/A')
        operation_object = record['extra'].get('operation_object', 'N/A')

        # 组装日志消息，确保包含安全六要素, 获取基本审计日志信息, 操作时间、用户标识、操作类型、操作对象、来源地址
        _message = (
            '{time:YYYY-MM-DD HH:mm:ss:SSS} |{level: <8} |P-{process: <6} |T-{thread: <6} |'
            + f'R-{request_id} |U-{user_id} |IP-{ip} |{operation_type} |{operation_object} |'
            + '{message}\n'
        )
        return _message
