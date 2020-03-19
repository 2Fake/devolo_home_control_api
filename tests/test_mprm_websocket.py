import time

import pytest

from .mocks.mock_websocket import MockWebsocket, MockWebsocketError


@pytest.mark.usefixtures("mprm_instance")
class TestMprmWebsocket:
    def test_get_local_session(self):
        with pytest.raises(NotImplementedError):
            self.mprm.get_local_session()

    def test_get_remote_session(self):
        with pytest.raises(NotImplementedError):
            self.mprm.get_remote_session()

    def test_websocket_connect(self, mock_mprmwebsocket_websocketapp, mprm_session, gateway_instance):
        self.mprm._session = mprm_session
        self.mprm._gateway = gateway_instance
        with pytest.raises(AssertionError):
            self.mprm.websocket_connect()

    def test_websocket_disconnect(self):
        self.mprm._ws = MockWebsocketError()
        with pytest.raises(AssertionError):
            self.mprm.websocket_disconnect()

    def test__on_message(self):
        message = '{"properties": {"com.prosyst.mbs.services.remote.event.sequence.number": 0}}'
        with pytest.raises(NotImplementedError):
            self.mprm._on_message(message)

    def test__on_message_event_sequence(self, mock_mprmwebsocket_on_update):
        event_sequence = self.mprm._event_sequence
        message = '{"properties": {"com.prosyst.mbs.services.remote.event.sequence.number": 5}}'
        self.mprm._on_message(message)
        assert event_sequence != self.mprm._event_sequence
        assert self.mprm._event_sequence == 5

    def test__on_error(self, mock_mprmwebsocket_get_remote_session, mock_mprmwebsocket_websocket_connection):
        self.mprm._ws = MockWebsocket()
        self.mprm._on_error("error")

    def test__try_reconnect(self, mocker, mock_mprmwebsocket_get_local_session_json_decode_error):
        spy = mocker.spy(time, "sleep")
        self.mprm._ws = MockWebsocket()

        self.mprm._local_ip = self.gateway.get("local_ip")
        self.mprm._try_reconnect(0.1)
        spy.assert_called_once_with(0.1)
