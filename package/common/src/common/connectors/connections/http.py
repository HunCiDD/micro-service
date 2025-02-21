import json
from typing import Any

from requests import PreparedRequest, Request, Response, Session

from src.connectors.models import Infrastructure
from src.settings import APP_SETTINGS
from src.utils.enums import EnumStatus

from .base import BaseRequest, BaseResponse, Connection

api_logger = APP_SETTINGS.api_logger
run_logger = APP_SETTINGS.run_logger


class HttpResponse(BaseResponse): ...


class HttpRequest(BaseRequest):
    METHOD = 'GET'
    PROTOCOL = 'https'
    PATH = ''

    def __init__(self, **kwargs):
        self._url = ''
        self._path = self.PATH.strip()
        self._method = self.METHOD.upper()
        self._protocol = self.PROTOCOL.lower()
        self._headers: dict = {'Accept': 'application/json', 'User-Agent': 'Chrome/78.0', 'Charset': 'UTF-8'}
        self._files: dict = {}
        self._data: dict = {}
        self._json: dict = {}
        self._params: dict = {}
        super().__init__(**kwargs)

    @property
    def method(self) -> str:
        return self._get('method')

    @property
    def url(self) -> str:
        return self._get('url')

    @property
    def headers(self) -> dict:
        return self._get('headers', {})

    @property
    def files(self) -> dict:
        return self._get('files', {})

    @property
    def data(self) -> dict:
        return self._get('data', {})

    @property
    def params(self) -> dict:
        return self._get('params', {})

    @property
    def json(self) -> dict:
        return self._get('json', {})

    @property
    def request(self) -> PreparedRequest:
        req = Request(method=self.method, url=self.url, headers=self.headers, params=self.params, data=self.data)
        return req.prepare()

    def parser(self, data: Response) -> HttpResponse:
        run_logger.debug('start parser')
        if not data:
            # 没有响应
            return HttpResponse(code=500, status=EnumStatus.FAILURE, msg='No data')

        try:
            # 检查http响应状态码
            data.raise_for_status()
        except Exception as e:
            msg = f'{data.status_code}\n{e}\n'
            return HttpResponse(code=data.status_code, status=EnumStatus.FAILURE, msg=msg)

        if not isinstance(data.text, str):
            msg = 'response.text is not a string'
            return HttpResponse(code=500, data=f'{data.text}', status=EnumStatus.FAILURE, msg=msg)

        try:
            rsp_data = json.loads(data.text)
        except Exception:
            msg = 'respnse.text is not a JSON format'
            return HttpResponse(code=500, data=f'{data.text}', status=EnumStatus.FAILURE, msg=msg)

        return HttpResponse(code=200, data=rsp_data)

    def _init_request(self):
        self._init_url()
        self._init_headers()
        self._init_files()
        self._init_data()
        self._init_params()
        self._init_auth()
        self._init_cookies()
        self._init_json()

    def _init_url(self): ...

    def _init_headers(self): ...

    def _init_files(self): ...

    def _init_data(self): ...

    def _init_params(self): ...

    def _init_auth(self): ...

    def _init_cookies(self): ...

    def _init_json(self): ...


class HttpConnection(Connection):
    BASE_VERIFY = False

    def __init__(self, infrastructure: Infrastructure, agent: Any = None, **kwargs):
        super().__init__(infrastructure, agent, **kwargs)
        self._auth_session: dict = {}
        self._client = Session()
        self.verify = self.BASE_VERIFY

    def send(self, http_request: HttpRequest, **kwargs) -> HttpResponse:  # type: ignore
        run_logger.debug('start send.')
        if http_request.AUTH_NEED and not self.is_auth:
            # 命令需要认证，当前又未认证过
            self._auth(http_request, **kwargs)
        return self._send(http_request, **kwargs)

    def _auth(self, http_request: HttpRequest = None, **kwargs):  # type: ignore
        # 需要构建认证请求,并发送 eg：self._send(auth_request, **kwargs)
        # 更新认证信息到请求头
        if self._auth_session:
            http_request.headers.update(self._auth_session)

    def _send(self, http_request: HttpRequest, **kwargs) -> HttpResponse:  # type: ignore
        try:
            req = http_request.request
            response: Response = self._client.send(request=req, verify=self.verify)
            return http_request.parser(response)
        except Exception as e:
            api_logger.exception(f'{e}')
            return HttpResponse(data=None, **kwargs)
