import pytest
from devolo_home_control_api.mydevolo import Mydevolo


class TestMydevolo():

    def test_uuid(self, mocker):
        def _call_mock(url):
            return {"uuid": "123456789"}

        mocker.patch("devolo_home_control_api.mydevolo.Mydevolo._call", side_effect=_call_mock)
        md = Mydevolo.get_instance()
        assert md.uuid == "123456789"
