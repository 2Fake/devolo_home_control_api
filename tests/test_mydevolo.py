import pytest

from devolo_home_control_api.mydevolo import Mydevolo


class TestMydevolo():

    def test_uuid(self, mocker):
        def _call_mock(url):
            return {"uuid": "535512AB-165D-11E7-A4E2-000C29D76CCA"}

        mocker.patch("devolo_home_control_api.mydevolo.Mydevolo._call", side_effect=_call_mock)
        Mydevolo.del_instance()
        mydevolo = Mydevolo.get_instance()
        assert mydevolo.uuid == "535512AB-165D-11E7-A4E2-000C29D76CCA"

    def test_gateway_ids(self, mocker):
        def _call_mock(url):
            return {"items": [{"gatewayId": "1409301750000598"}]}

        mocker.patch("devolo_home_control_api.mydevolo.Mydevolo._call", side_effect=_call_mock)
        Mydevolo.del_instance()
        mydevolo = Mydevolo.get_instance()
        mydevolo._uuid = "535512AB-165D-11E7-A4E2-000C29D76CCA"

        assert mydevolo.gateway_ids == ["1409301750000598"]

    def test_gateway_ids_empty(self, mocker):
        def _call_mock(url):
            return {"items": []}

        mocker.patch("devolo_home_control_api.mydevolo.Mydevolo._call", side_effect=_call_mock)
        Mydevolo.del_instance()
        mydevolo = Mydevolo.get_instance()
        mydevolo._uuid = "535512AB-165D-11E7-A4E2-000C29D76CCA"

        with pytest.raises(IndexError):
            mydevolo.gateway_ids
