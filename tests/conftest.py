import pytest

from devolo_home_control_api.mydevolo import Mydevolo
from tests.mock_gateway import Gateway


uuid = "535512AB-165D-11E7-A4E2-000C29D76CCA"
gateway_id = "1409301750000598"


@pytest.fixture()
def mock_gateway(mocker):
    mocker.patch('devolo_home_control_api.devices.gateway.Gateway.__init__', Gateway.__init__)


@pytest.fixture()
def mock_inspect_devices(mocker):
    def mock_inspect_devices(self):
        pass
    mocker.patch('devolo_home_control_api.mprm_rest.MprmRest._inspect_devices', mock_inspect_devices)


@pytest.fixture()
def mock_mprmrest__detect_gateway_in_lan(mocker):
    def _detect_gateway_in_lan(self):
        return None
    mocker.patch('devolo_home_control_api.mprm_rest.MprmRest._detect_gateway_in_lan', _detect_gateway_in_lan)


@pytest.fixture()
def mock_mydevolo__call(mocker, request):
    def _call_mock(url):
        if url == f"https://www.mydevolo.com/v1/users/{uuid}/hc/gateways/{gateway_id}/fullURL":
            return {"url": "https://homecontrol.mydevolo.com/dhp/portal/fullLogin/?"
                           "token=1410000000002_1:ec73a059f398fa8b&X-MPRM-LB=1410000000002_1"}
        elif url == "https://www.mydevolo.com/v1/users/uuid":
            return {"uuid": uuid}
        elif url == f"https://www.mydevolo.com/v1/users/{uuid}/hc/gateways/status":
            if request.node.name == "test_gateway_ids_empty":
                return {"items": []}
            else:
                return {"items": [{"gatewayId": gateway_id}]}
        elif url == f"https://www.mydevolo.com/v1/users/{uuid}/hc/gateways/{gateway_id}":
            return {"gatewayId": gateway_id}
        else:
            print(url)

    mocker.patch("devolo_home_control_api.mydevolo.Mydevolo._call", side_effect=_call_mock)


@pytest.fixture(autouse=True)
def test_data(request):
    request.cls.uuid = uuid
    request.cls.gateway_id = gateway_id


@pytest.fixture(autouse=True)
def clear_mydevolo():
    Mydevolo.del_instance()
