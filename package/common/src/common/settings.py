__all__ = ['AppSettings', 'APP_SETTINGS']

from pathlib import Path
from typing import Any, Dict, Union

from .configs import FileConfigsDict
from .db.base import DataBase
from .files.extend import YamlFile
from .loggers.extend import AgentLogger, ApiLogger, OperateLogger, RunLogger


class AppSettings:
    LOGGER_CLS_MAP = {'run': RunLogger, 'operate': OperateLogger, 'api': ApiLogger, 'agent': AgentLogger}

    def __init__(self, app_name: str = 'default', app_dir: Path = Path(__file__).parent.parent.parent) -> None:
        self.app_name = app_name
        self.app_dir = app_dir
        self._load(self.app_name, self.app_dir)

    @property
    def src_dir(self) -> Path:
        # 代码目录
        return self.app_dir / 'src'

    @property
    def config_dir(self) -> Path:
        # 配置目录
        return self.app_dir / 'configs'

    @property
    def log_dir(self) -> Path:
        # 日志目录
        return self.app_dir / 'logs'

    @property
    def script_dir(self) -> Path:
        # 项目脚本目录
        return self.app_dir / 'scripts'

    @property
    def lib_dir(self) -> Path:
        return self.app_dir / 'libs'

    def reload(self, app_name: str = 'default', app_dir: Path = Path(__file__).parent.parent.parent) -> None:
        self._load(app_name, app_dir)

    def _load(self, app_name: str = 'default', app_dir: Path = Path(__file__).parent.parent.parent) -> None:
        self.app_name = app_name
        self.app_dir = app_dir

        self.app_file = YamlFile(self.config_dir / f'{app_name}.yaml')
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
        for key, logger_cls in self.LOGGER_CLS_MAP.items():
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


APP_SETTINGS = AppSettings('default')
