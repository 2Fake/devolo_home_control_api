import pytest

from devolo_home_control_api.mydevolo import Mydevolo


class TestMydevolo:

    _uuid = "535512AB-165D-11E7-A4E2-000C29D76CCA"
    _gateway = "1409301750000598"

    def test_uuid(self, mock_mydevolo__call_uuid):
        mydevolo = Mydevolo.get_instance()
        assert mydevolo.uuid == TestMydevolo._uuid

    def test_gateway_ids(self, mock_mydevolo__call_gateway_ids):
        mydevolo = Mydevolo.get_instance()
        mydevolo._uuid = TestMydevolo._uuid

        assert mydevolo.gateway_ids == [TestMydevolo._gateway]

    def test_gateway_ids_empty(self, mock_mydevolo__call_gateway_ids_empty):
        mydevolo = Mydevolo.get_instance()
        mydevolo._uuid = TestMydevolo._uuid

        with pytest.raises(IndexError):
            mydevolo.gateway_ids

    def test_get_gateway(self, mock_mydevolo__call_get_gateways):
        mydevolo = Mydevolo.get_instance()
        mydevolo._uuid = TestMydevolo._uuid

        details = mydevolo.get_gateway(TestMydevolo._gateway)

        assert details.get("gatewayId") == TestMydevolo._gateway

    def test_get_full_url(self, mock_mydevolo__call_get_full_url):

        mydevolo = Mydevolo.get_instance()
        mydevolo._uuid = "535512AB-165D-11E7-A4E2-000C29D76CCA"

        full_url = mydevolo.get_full_url(TestMydevolo._gateway)

        assert full_url == "https://homecontrol.mydevolo.com/dhp/portal/fullLogin/?token=1410000000002_1:ec73a059f398fa8b&X-MPRM-LB=1410000000002_1"
