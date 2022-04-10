class MockWebsocketError:
    def close(self):
        raise AssertionError


def try_reconnect(self, sleep_interval):
    self._reachable = True
