import select
import time
from typing import Any, Dict, Optional

from paramiko import AutoAddPolicy, Channel, SSHClient
from paramiko.ssh_exception import AuthenticationException
from pydantic import BaseModel

from src.connectors.models import Infrastructure
from src.settings import APP_SETTINGS
from src.utils.enums import EnumStatus

from .base import BaseRequest, BaseResponse, Connection

api_logger = APP_SETTINGS.api_logger
run_logger = APP_SETTINGS.run_logger

__all__ = ['SshResponse', 'SshRequest', 'SshConnection']


class SshResponse(BaseResponse): ...


class SshRequest(BaseRequest):
    INVOKE = False  # 是否交互

    def __init__(self, **kwargs):
        self._text: str = ''
        self._endflag: str = ''
        self._invokes_text: Dict[str, str] = {}
        super().__init__(**kwargs)

    @property
    def text(self) -> str:
        return self._get('text')

    @property
    def endflag(self) -> str:
        return self._get('endflag', default='')

    def invoke_text(self, data: str) -> str:
        _invokes_text = self._get('invokes_text', default={})
        for key, _ in _invokes_text.items():
            if key in data:
                return self._invokes_text[key]
        return ''

    def parser(self, data: Any) -> SshResponse:
        return SshResponse(code=200, status=EnumStatus.SUCCESS, data=data)

    def _init_request(self):
        self._init_text()
        self._init_invokes()

    def _init_text(self): ...

    def _init_invokes(self): ...


class ConfigsModels(BaseModel):
    timeout: int = 5
    banner_timeout: int = 60

    class Config:
        extra = 'allow'


class SshConnection(Connection):
    def __init__(self, infrastructure: Infrastructure, agent: Any = None, **kwargs):
        super().__init__(infrastructure, agent, **kwargs)
        self._configs = ConfigsModels(**self.settings)

    @property
    def is_available(self) -> bool:
        try:
            transport = self._client.get_transport()
            if transport is None or not transport.is_active():
                return False
            return True
        except Exception as e:
            run_logger.exception(f'{e}')
            return False

    def close(self):
        if not self._client:
            return

        if not hasattr(self._client, 'close'):
            return

        if not callable(self._client.close):
            return

        try:
            self._client.close()
        except Exception as e:
            run_logger.exception(f'{e}')
        return

    def send(self, ssh_request: SshRequest, **kwargs) -> SshResponse:  # type: ignore
        run_logger.debug('start.')
        if not ssh_request.text:
            return SshResponse(code=0, status=EnumStatus.FAILURE, msg='No text')

        if ssh_request.AUTH_NEED and not (self.is_auth and self._client):
            self._auth(ssh_request, **kwargs)

            if not self.is_auth:
                return SshResponse(code=0, status=EnumStatus.FAILURE, msg='No auth')

        return self._send(ssh_request, **kwargs)

    def _get_channel(self) -> Optional[Channel]:
        _channel = None
        try:
            _channel = self._client.invoke_shell()
        except Exception as e:
            run_logger.exception(f'{e}')
        return _channel

    def _auth(self, ssh_request: Optional[SshRequest] = None, **kwargs):  # type: ignore
        run_logger.info('start auth.')
        try:
            self._client = SSHClient()
            self._client.set_missing_host_key_policy(AutoAddPolicy())
            self._client.connect(
                hostname=self.infrastructure.ip,
                port=self.infrastructure.port,
                username=self.infrastructure.username,
                password=self.infrastructure.password,
                timeout=self._configs.timeout,
                banner_timeout=self._configs.banner_timeout,
            )
            self._is_auth = True
        except AuthenticationException as e:
            run_logger.exception(f'{e}')
            api_logger.exception(f'{e}')
        return

    def _send(self, ssh_request: SshRequest, **kwargs) -> SshResponse:  # type: ignore
        try:
            # 打开一个交互式 shell
            channel = self._client.invoke_shell()

            # 检查通道是否准备好，避免硬编码的 sleep
            while not channel.recv_ready():
                time.sleep(0.1)

            # 发送初始命令
            channel.send((ssh_request.text + '\n').encode('utf-8'))
            output = self._recv(ssh_request, channel)

            invoke_text = ssh_request.invoke_text(output) if ssh_request.INVOKE else ''
            if invoke_text:
                channel.send((invoke_text + '\n').encode('utf-8'))
                output += self._recv(ssh_request, channel)

            return ssh_request.parser(output)

        except Exception as e:
            run_logger.exception(f'Exception in SSH send operation: {e}')
            return SshResponse(code=500, status=EnumStatus.FAILURE, msg=f'{e}')

    def _recv(self, ssh_request: SshRequest, channel: Channel, **kwargs) -> str:
        result = ''
        max_loops, cur_loop = 100, 0
        while True:
            if cur_loop >= max_loops:
                run_logger.warning('Exceute max loop count, exiting.')
                break

            reads = [channel]
            timeout = 1
            ready, _, _ = select.select(reads, [], [], timeout)

            if not ready:
                # 处理通道没有准备好，或者超时了
                run_logger.debug('No data ready, waiting for channel.')
                cur_loop += 1
                continue

            for ch in ready:
                if ch is not channel:
                    continue

                output = ch.recv(1024).decode('utf-8')
                run_logger.debug(f'output: {output}')

                if output == '':
                    # 远端关闭连接，退出循环
                    run_logger.debug('Received empty output, channel might be closed')
                    break

                result += output

            # 检查提示 （）
            if channel.exit_status_ready():
                break

            if ssh_request.endflag and ssh_request.endflag in result:
                break

            cur_loop += 1

        return result
