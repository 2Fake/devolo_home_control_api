import time
from unittest.mock import patch

import pytest
from requests.exceptions import ConnectionError
from urllib3.connection import ConnectTimeoutError
from websocket import WebSocketApp

from devolo_home_control_api.backend.mprm_rest import MprmRest
from devolo_home_control_api.backend.mprm_websocket import MprmWebsocket

from .mocks.mock_websocket import MockWebsocketError
from .stubs.mprm_websocket import StubMprmWebsocket


@pytest.mark.usefixtures("mprm_instance")
class TestMprmWebsocket:
    @pytest.mark.usefixtures("mock_mprmwebsocket_websocketapp")
    def test_websocket_connect(self, mprm_session, gateway_instance):
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

    @pytest.mark.usefixtures("mock_mprmwebsocket_on_update")
    def test__on_message_event_sequence(self):
        event_sequence = self.mprm._event_sequence
        self.mprm._event_sequence = 5
        message = '{"properties": {"com.prosyst.mbs.services.remote.event.sequence.number": 5}}'
        self.mprm._on_message(None, message)
        assert event_sequence != self.mprm._event_sequence
        assert self.mprm._event_sequence == 6
        message = '{"properties": {"com.prosyst.mbs.services.remote.event.sequence.number": 7}}'
        self.mprm._on_message(None, message)
        assert self.mprm._event_sequence == 8

    @pytest.mark.usefixtures("mock_mprmwebsocket_get_remote_session")
    @pytest.mark.usefixtures("mock_mprmwebsocket_websocket_connection")
    @pytest.mark.usefixtures("mock_mprmwebsocket_try_reconnect")
    @pytest.mark.usefixtures("mock_mprmwebsocket_websocketapp")
    def test__on_error(self, mocker):
        close_spy = mocker.spy(WebSocketApp, "close")
        reconnect_spy = mocker.spy(MprmWebsocket, "_try_reconnect")
        connect_spy = mocker.spy(MprmWebsocket, "websocket_connect")
        self.mprm._ws = WebSocketApp()
        self.mprm._on_error(self.mprm._ws, "error")
        assert close_spy.call_count == 1
        assert reconnect_spy.call_count == 1
        assert connect_spy.call_count == 1

    @pytest.mark.usefixtures("mock_mprmwebsocket_websocketapp")
    @pytest.mark.usefixtures("mock_session_get")
    def test__on_pong(self, mocker, mprm_session, gateway_instance, mydevolo):
        spy = mocker.spy(MprmRest, "refresh_session")
        self.mprm._mydevolo = mydevolo
        self.mprm._session = mprm_session
        self.mprm.gateway = gateway_instance
        self.mprm._local_ip = self.gateway["local_ip"]
        self.mprm._on_pong(None)
        assert spy.call_count == 1

    @pytest.mark.usefixtures("mock_mprmwebsocket_websocketapp")
    def test__try_reconnect(self, mocker):
        spy = mocker.spy(time, "sleep")
        self.mprm._ws = ConnectTimeoutError
        self.mprm._local_ip = self.gateway["local_ip"]
        self.mprm._try_reconnect(0.1)
        spy.assert_called_once_with(0.1)

    @pytest.mark.usefixtures("mock_mprmwebsocket_websocketapp")
    def test__try_reconnect_with_detect(self, mocker):
        with patch("time.sleep") as sleep:
            spy_detect_gateway = mocker.spy(StubMprmWebsocket, "detect_gateway_in_lan")
            self.mprm._ws = ConnectionError
            self.mprm._local_ip = self.gateway["local_ip"]
            self.mprm._try_reconnect(4)
            sleep.assert_called_once_with(1)
            spy_detect_gateway.assert_called_once()
