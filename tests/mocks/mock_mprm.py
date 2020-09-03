from devolo_home_control_api.backend.mprm_websocket import MprmWebsocket


class MockMprm(MprmWebsocket):
    def __init__(self):
        super(MprmWebsocket, self).__init__()
        self.detect_gateway_in_lan(None)
