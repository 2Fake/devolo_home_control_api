import pytest

from devolo_home_control_api.mydevolo import Mydevolo


class TestMydevolo():

    _uuid = "535512AB-165D-11E7-A4E2-000C29D76CCA"
    _gateway = "1409301750000598"

    def test_uuid(self, mocker):
        def _call_mock(url):
            return {"uuid": TestMydevolo._uuid}

        mocker.patch("devolo_home_control_api.mydevolo.Mydevolo._call", side_effect=_call_mock)
        Mydevolo.del_instance()
        mydevolo = Mydevolo.get_instance()
        assert mydevolo.uuid == TestMydevolo._uuid

    def test_gateway_ids(self, mocker):
        def _call_mock(url):
            return {"items": [{"gatewayId": TestMydevolo._gateway}]}

        mocker.patch("devolo_home_control_api.mydevolo.Mydevolo._call", side_effect=_call_mock)
        Mydevolo.del_instance()
        mydevolo = Mydevolo.get_instance()
        mydevolo._uuid = TestMydevolo._uuid

        assert mydevolo.gateway_ids == [TestMydevolo._gateway]

    def test_gateway_ids_empty(self, mocker):
        def _call_mock(url):
            return {"items": []}

        mocker.patch("devolo_home_control_api.mydevolo.Mydevolo._call", side_effect=_call_mock)
        Mydevolo.del_instance()
        mydevolo = Mydevolo.get_instance()
        mydevolo._uuid = TestMydevolo._uuid

        with pytest.raises(IndexError):
            mydevolo.gateway_ids

    def test_get_gateway(self, mocker):
        def _call_mock(url):
            return {"gatewayId": TestMydevolo._gateway}

        mocker.patch("devolo_home_control_api.mydevolo.Mydevolo._call", side_effect=_call_mock)
        Mydevolo.del_instance()
        mydevolo = Mydevolo.get_instance()
        mydevolo._uuid = TestMydevolo._uuid

        details = mydevolo.get_gateway(TestMydevolo._gateway)

        assert details.get("gatewayId") == TestMydevolo._gateway

    def test_get_full_url(self, mocker):
        def _call_mock(url):
            return {"url": "https://homecontrol.mydevolo.com/dhp/portal/fullLogin/?token=1410000000002_1:ec73a059f398fa8b&X-MPRM-LB=1410000000002_1"}

        mocker.patch("devolo_home_control_api.mydevolo.Mydevolo._call", side_effect=_call_mock)
        Mydevolo.del_instance()
        mydevolo = Mydevolo.get_instance()
        mydevolo._uuid = "535512AB-165D-11E7-A4E2-000C29D76CCA"

        full_url = mydevolo.get_full_url(TestMydevolo._gateway)

        assert full_url == "https://homecontrol.mydevolo.com/dhp/portal/fullLogin/?token=1410000000002_1:ec73a059f398fa8b&X-MPRM-LB=1410000000002_1"
