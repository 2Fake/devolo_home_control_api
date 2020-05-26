from devolo_home_control_api.backend.mprm_rest import MprmRest


class MockWebsocket(MprmRest):
    def __init__(self):
        super(MprmRest, self).__init__()
        self._ws = None
        self._connected = True
        self._reachable = True
        self._event_sequence = 0

    def close(self):
        pass


class MockWebsocketError:
    def close(self):
        raise AssertionError


def try_reconnect(self, sleep_interval):
    self._reachable = True
