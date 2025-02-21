__all__ = ['Paths', 'Dirs', 'AppSettings', 'APP_SETTINGS']

import os
from pathlib import Path
from typing import Any, Dict, Union

from common.db.base import DataBase
from common.utils.configs import FileConfigsDict
from common.utils.designs import SingletonMeta
from common.utils.files import Dir, YamlFile
from common.utils.loggers import AgentLogger, ApiLogger, OperateLogger, RunLogger


class ENV:
    APP_NAME = os.environ.get('APP_NAME', 'default')


# 全局配置
# 相关路径配置
class Paths:
    # 项目根目录
    PROJECT_DIR = Path(__file__).parent.parent
    # 代码目录
    SRC_DIR = PROJECT_DIR / 'src'
    # 项目配置文件目录
    CONFIG_DIR = PROJECT_DIR / 'configs'
    # 项目日志目录
    LOG_DIR = PROJECT_DIR / 'logs'
    # 项目脚本目录
    SCRIPT_DIR = PROJECT_DIR / 'scripts'
    # 库目录
    LIB_DIR = PROJECT_DIR / 'libs'
    LIB_JARS_DIR = LIB_DIR / 'jars'
    # 输出目录
    OUTPUT_DIR = PROJECT_DIR / 'output'
    # 临时目录
    TEMP_DIR = OUTPUT_DIR / 'temp'
    # 报告目录
    REPORT_DIR = OUTPUT_DIR / 'report'
    #
    APPS_DIR = PROJECT_DIR / 'apps'


# 相关目录
class Dirs:
    LOG_DIR = Dir(Paths.LOG_DIR)
    OUTPUT_DIR = Dir(Paths.OUTPUT_DIR)
    TEMP_DIR = Dir(Paths.TEMP_DIR)
    REPORT_DIR = Dir(Paths.REPORT_DIR)


LOGGER_CLS_MAP = {'run': RunLogger, 'operate': OperateLogger, 'api': ApiLogger, 'agent': AgentLogger}


class AppSettings(metaclass=SingletonMeta):
    def __init__(self, app_name: str = 'default') -> None:
        self._load(app_name)

    def reload(self, app_name: str = 'default') -> None:
        self._load(app_name)

    def _load(self, app_name: str = 'default') -> None:
        self.app_name = app_name
        self.app_dir = Paths.APPS_DIR / app_name

        self.app_file = YamlFile(Paths.CONFIG_DIR / f'{app_name}.yaml')
        self.app_configs = FileConfigsDict(self.app_file)

        self.app_settings: Dict[str, Any] = self.app_configs.get('App', {})
        self.app_env = self.app_settings.get('env', 'dev')

        self.logger_settings: Dict[str, Any] = self.app_configs.get('Logger', {})
        self._logger_map: Dict[str, Union[RunLogger, ApiLogger, OperateLogger, AgentLogger]] = {}
        self._load_loggers()

        self.db_settings: Dict[str, Any] = self.app_configs.get('DB', {})
        self._load_database()

        self.celery_settings: Dict[str, Any] = self.app_configs.get('Celery', {})

        self.connectors_settings: Dict[str, Any] = self.app_configs.get('Connectors', {})

        self.services_settings: Dict[str, Any] = self.app_configs.get('Services', {})

    def _load_loggers(self):
        for key, logger_cls in LOGGER_CLS_MAP.items():
            if key not in self.logger_settings:
                continue

            if key == 'console' and self.app_env != 'dev':
                continue

            _logger = logger_cls(self.logger_settings)
            self._logger_map[key] = _logger

    def _load_database(self):
        url = self.db_settings.get('url', '')
        if not url:
            self.run_logger.warning('not url')
            return

        self._db = DataBase(url=url)

    @property
    def host(self) -> str:
        return self.app_settings.get('host', '127.0.0.1')

    @property
    def port(self) -> int:
        return self.app_settings.get('port', 8000)

    @property
    def run_logger(self):
        return self._logger_map['run']

    @property
    def operate_logger(self):
        return self._logger_map['operate']

    @property
    def api_logger(self):
        return self._logger_map['api']

    @property
    def agent_logger(self):
        return self._logger_map['agent']

    @property
    def db(self) -> DataBase:
        return self._db


APP_SETTINGS = AppSettings(ENV.APP_NAME)
