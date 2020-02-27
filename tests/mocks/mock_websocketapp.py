class MockWebsocketapp:
    def __init__(self, ws_url, **kwargs):
        pass

    def run_forever(self, **kwargs):
        raise AssertionError
