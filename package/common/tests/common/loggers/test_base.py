from pathlib import Path

import pytest

from common.loggers.base import ConfigModel, FilterConfigModel


class TestConfigModel:
    def test_default_001(self):
        lc = ConfigModel()
        data = lc.model_dump(exclude_none=True)

        assert data['level'] == 'INFO'
        assert data['format'] == '{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}'

    def test_sink_001(self):
        lc = ConfigModel(sink='a.log')
        assert lc.sink == Path('a.log')


class TestLoggerFilterConfigs:
    def test_default_001(self):
        lfc = FilterConfigModel()
        assert lfc.sensitive_fields == (
            '(password|token|key|secret|token|session|cookie|csrf|jwt|access_token|'
            'refresh_token|id_token|client_secret|client_id|api_key|secret_key)'
        )
        assert lfc.sensitive_fields_replacement == '********'
        assert lfc.max_length == 2000
        assert lfc.max_length_replacement == '......'

    def test_default_002(self):
        lfc = FilterConfigModel(
            sensitive_fields_replacement='$$$',
            max_length=100,
            max_length_replacement='...',
        )
        assert lfc.sensitive_fields_replacement == '$$$'
        assert lfc.max_length == 100
        assert lfc.max_length_replacement == '...'


if __name__ == '__main__':
    pytest.main()
