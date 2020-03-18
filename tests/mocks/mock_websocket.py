class MockWebsocket:
    def close(self):
        pass


class MockWebsocketError:
    def close(self):
        raise AssertionError
