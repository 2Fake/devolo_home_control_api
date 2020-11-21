from devolo_home_control_api.backend.mprm_websocket import MprmWebsocket
from urllib3.connection import ConnectTimeoutError


class StubMprmWebsocket(MprmWebsocket):
    def __init__(self):
        super().__init__()
        self._ws = None
        self._connected = True
        self._reachable = True
        self._event_sequence = 0
        self._url = "https://test.test"

    def close(self):
        pass

    def get_local_session(self):
        raise ConnectTimeoutError

    def get_remote_session(self):
        pass

    def on_update(self, message):
        pass

    def _post(self, data):
        pass
