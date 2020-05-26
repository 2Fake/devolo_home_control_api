import time

import pytest

from devolo_home_control_api.backend.mprm_rest import MprmRest
from devolo_home_control_api.backend.mprm_websocket import MprmWebsocket

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
        self.mprm.gateway = gateway_instance
        with pytest.raises(AssertionError):
            self.mprm.websocket_connect()

    def test_websocket_disconnect(self):
        self.mprm._ws = MockWebsocketError()
        with pytest.raises(AssertionError):
            self.mprm.websocket_disconnect()

    @pytest.mark.usefixtures("mock_mprmwebsocket_websocket_disconnect")
    def test__exit__(self, mocker):
        disconnect_spy = mocker.spy(MprmWebsocket, "websocket_disconnect")
        self.mprm.__exit__(None, None, None)
        assert disconnect_spy.call_count == 1

    def test__on_message(self):
        with pytest.raises(NotImplementedError):
            message = '{"properties": {"com.prosyst.mbs.services.remote.event.sequence.number": 0}}'
            self.mprm._on_message(message)

    def test__on_message_event_sequence(self, mock_mprmwebsocket_on_update):
        event_sequence = self.mprm._event_sequence
        message = '{"properties": {"com.prosyst.mbs.services.remote.event.sequence.number": 5}}'
        self.mprm._on_message(message)
        assert event_sequence != self.mprm._event_sequence
        assert self.mprm._event_sequence == 5

    @pytest.mark.usefixtures("mock_mprmwebsocket_get_remote_session")
    @pytest.mark.usefixtures("mock_mprmwebsocket_websocket_connection")
    @pytest.mark.usefixtures("mock_mprmwebsocket_try_reconnect")
    def test__on_error(self, mocker):
        close_spy = mocker.spy(MockWebsocket, "close")
        reconnect_spy = mocker.spy(MprmWebsocket, "_try_reconnect")
        connect_spy = mocker.spy(MprmWebsocket, "websocket_connect")
        self.mprm._ws = MockWebsocket()
        self.mprm._on_error("error")
        assert close_spy.call_count == 1
        assert reconnect_spy.call_count == 1
        assert connect_spy.call_count == 1

    @pytest.mark.usefixtures("mock_mprmwebsocket_websocketapp")
    @pytest.mark.usefixtures("mock_session_get")
    def test__on_pong(self, mocker, mprm_session, gateway_instance):
        spy = mocker.spy(MprmRest, "refresh_session")
        self.mprm._session = mprm_session
        self.mprm.gateway = gateway_instance
        self.mprm._local_ip = self.gateway.get("local_ip")
        self.mprm._on_pong()
        assert spy.call_count == 1

    @pytest.mark.usefixtures("mock_mprmwebsocket_get_local_session_json_decode_error")
    def test__try_reconnect(self, mocker):
        spy = mocker.spy(time, "sleep")
        self.mprm._ws = MockWebsocket()
        self.mprm._local_ip = self.gateway.get("local_ip")
        self.mprm._try_reconnect(0.1)
        spy.assert_called_once_with(0.1)
