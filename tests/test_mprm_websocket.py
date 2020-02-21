import threading
import time

import pytest

from .mocks.mock_websocket import MockWebsocket


@pytest.mark.usefixtures("mprm_instance")
class TestMprmWebsocket:

    def test_websocket_connection(self, mock_mprmwebsocket_websocketapp):
        with pytest.raises(AssertionError):
            self.mprm.websocket_connection()

    def test__on_message(self):
        message = '{"properties": {"com.prosyst.mbs.services.remote.event.sequence.number": 0}}'
        self.mprm.on_update = lambda: AssertionError()
        try:
            self.mprm._on_message(message)
            assert False
        except AssertionError:
            assert True

    def test__on_message_event_sequence(self):
        event_sequence = self.mprm._event_sequence
        message = '{"properties": {"com.prosyst.mbs.services.remote.event.sequence.number": 5}}'
        self.mprm._on_message(message)
        assert event_sequence != self.mprm._event_sequence
        assert self.mprm._event_sequence == 5

    def test__on_update_not_set(self):
        # TypeError should be caught by _on_message
        self.mprm.on_update = None
        message = '{"properties": {"com.prosyst.mbs.services.remote.event.sequence.number": 0}}'
        self.mprm._on_message(message)

    def test__on_error(self, mock_mprmrest_get_remote_session, mock_mprmwebsocket_websocket_connection):
        self.mprm._ws = MockWebsocket()
        self.mprm._on_error("error")

    def test__on_error_errors(self, mock_mprmrest_get_remote_session, mock_mprmwebsocket_websocket_connection,
                              mock_mprmrest_get_local_session_json_decode_error):
        self.mprm._ws = MockWebsocket()

        self.mprm._local_ip = "123.456.789.123"
        threading.Thread(target=self.mprm._on_error).start()
        # local ip is set --> self.get_local_session() will throw an error because of the fixture
        # mock_get_local_session_json_decode_error.
        # After first run we remove the local ip and self.get_remote_session() will pass.
        time.sleep(2)
        self.mprm._local_ip = None

        self.mprm.websocket_connection = lambda: None
