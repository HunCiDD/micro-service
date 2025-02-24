import pytest


class TestRunLogger:
    def test_001(self):
        logger = app_settings.run_logger
        assert logger.configs

        sink = logger.configs.sink

        logger.debug('hello world debug')
        logger.info('hello world info')
        logger.warning('hello world warning')
        logger.error('hello world error')


# class TestApiLogger:
#     def test_logger(self):
#         logger = LoggerSettings.API_LOGGER
#         logger.debug('hello world debug')
#         logger.info('hello world info')
#         logger.warning('hello world warning')
#         logger.error('hello world error password xhhxhh wo')


# class TestOperateLogger:
#     def test_001(self):
#         logger = LoggerSettings.OPERATE_LOGGER
#         OperateLoggerContext.request_id_var.set('001')
#         OperateLoggerContext.user_id_var.set('user001')
#         OperateLoggerContext.ip_var.set('127.0.0.1')
#         logger.debug('hello world debug', operation_type='add', operation_object='test')
#         logger.info('hello world info', operation_type='add', operation_object='test')
#         logger.warning('hello world warning', operation_type='add', operation_object='test')
#         logger.error('hello world error password xhhxhh wo', operation_type='add', operation_object='test')


if __name__ == '__main__':
    pytest.main()
