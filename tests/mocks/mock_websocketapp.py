class MockWebsocketapp:
    def __init__(self, ws_url, **kwargs):
        print("init")
        pass

    def run_forever(self, **kwargs):
        print("running")
        raise AssertionError