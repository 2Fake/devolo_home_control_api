from devolo_home_control_api.backend.mprm_websocket import MprmWebsocket


class StubMprmWebsocket(MprmWebsocket):
    def __init__(self):
        super().__init__()
        self._ws = None
        self._connected = True
        self._reachable = True
        self._event_sequence = 0
        self._url = "https://test.test"

    def detect_gateway_in_lan(self):
        pass

    def get_local_session(self):
        # We are abusing this to raise the expected exception
        raise self._ws()

    def get_remote_session(self):
        pass

    def on_update(self, message):
        pass

    def _post(self, data):
        pass
