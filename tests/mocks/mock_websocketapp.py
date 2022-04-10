class MockWebsocketapp:
    def __init__(self, *args, **kwargs):
        pass

    def close(self, **kwargs):
        pass

    def run_forever(self, **kwargs):
        raise AssertionError
