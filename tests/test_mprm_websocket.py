import pytest


class TestWebsocket:
    @pytest.mark.usefixtures("mprm_instance")
    def test__on_message(self):
        # We raise an error here, for which we can check in test
        def inner(message):
            raise FileExistsError
        self.mprm.on_update = inner
        message = '{"properties": {"com.prosyst.mbs.services.remote.event.sequence.number": 0}}'
        with pytest.raises(FileExistsError):
            self.mprm._on_message(message)

    @pytest.mark.usefixtures("mprm_instance")
    def test__on_message_event_sequence(self):
        event_sequence = self.mprm._event_sequence
        message = '{"properties": {"com.prosyst.mbs.services.remote.event.sequence.number": 5}}'
        self.mprm._on_message(message)
        assert event_sequence != self.mprm._event_sequence
        assert self.mprm._event_sequence == 5

    @pytest.mark.usefixtures("mprm_instance")
    def test__on_update_not_set(self):
        # TypeError should be caught by _on_message
        self.mprm.on_update = None
        message = '{"properties": {"com.prosyst.mbs.services.remote.event.sequence.number": 0}}'
        self.mprm._on_message(message)

    @pytest.mark.usefixtures("mprm_instance")
    @pytest.mark.usefixtures("mock_get_remote_session")
    @pytest.mark.usefixtures("mock_websocket_connection")
    def test__on_error(self):
        class Inner:
            def close(self):
                pass

        self.mprm._ws = Inner()
        self.mprm._on_error("error")

    @pytest.mark.usefixtures("mprm_instance")
    @pytest.mark.usefixtures("mock_get_remote_session")
    @pytest.mark.usefixtures("mock_websocket_connection")
    @pytest.mark.usefixtures("mock_get_local_session_json_decode_error")
    def test__on_error_errors(self):
        import threading
        import time

        class Inner:
            def close(self):
                pass

        self.mprm._ws = Inner()

        def inner_func():
            self.mprm._on_error("error")

        self.mprm._local_ip = "123.456.789.123"
        threading.Thread(target=inner_func).start()
        # local ip is set --> self.get_local_session() will throw an error because of the fixture.
        # After first run we remove the local ip and self.get_remote_session() will pass
        # TODO: There are 403 logged in thread. Mock them.
        time.sleep(2)
        self.mprm._local_ip = None