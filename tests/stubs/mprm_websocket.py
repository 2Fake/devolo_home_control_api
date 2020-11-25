import httpx

from devolo_home_control_api.backend.mprm_websocket import MprmWebsocket
from devolo_home_control_api.exceptions.gateway import GatewayOfflineError


class StubMprmWebsocket(MprmWebsocket):

    def __init__(self):
        super().__init__()
        self._test = None
        self._ws = None
        self._connected = True
        self._reachable = True
        self._event_sequence = 0
        self._url = "https://test.test"

    def detect_gateway_in_lan(self):
        pass

    def get_local_session(self):
        if self._test == "test__try_reconnect":
            raise GatewayOfflineError
        if self._test == "test__try_reconnect_with_detect":
            raise httpx.ConnectTimeout("", request=None)

    def get_remote_session(self):
        pass

    def on_update(self, message):
        pass

    def _post(self, data):
        pass
