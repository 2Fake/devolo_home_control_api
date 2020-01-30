import pytest

from devolo_home_control_api.mydevolo import Mydevolo
from devolo_home_control_api.mprm_rest import MprmRest
from tests.mock_gateway import Gateway
from tests.mock_metering_plug import metering_plug


user = "testuser@test.de"
password = "7fee3cdb598b45a459ffe2aa720c8532"
uuid = "535512AB-165D-11E7-A4E2-000C29D76CCA"
gateway_id = "1409301750000598"
full_url = "https://homecontrol.mydevolo.com/dhp/portal/fullLogin/?token=1410000000002_1:ec73a059f398fa8b"
device_uid = 'hdm:ZWave:CBC56091/3'

@pytest.fixture()
def mock_gateway(mocker):
    mocker.patch('devolo_home_control_api.devices.gateway.Gateway.__init__', Gateway.__init__)


@pytest.fixture()
def mock_inspect_devices_metering_plug(mocker):
    def mock__inspect_devices(self):
        self.devices[device_uid] = metering_plug(device_uid=device_uid)
    mocker.patch('devolo_home_control_api.mprm_rest.MprmRest._inspect_devices', mock__inspect_devices)


@pytest.fixture()
def mock_mprmrest__detect_gateway_in_lan(mocker):
    def _detect_gateway_in_lan(self):
        return None
    mocker.patch('devolo_home_control_api.mprm_rest.MprmRest._detect_gateway_in_lan', _detect_gateway_in_lan)


@pytest.fixture()
def mock_mydevolo__call(mocker, request):
    def _call_mock(url):
        if url == f"https://www.mydevolo.com/v1/users/{uuid}/hc/gateways/{gateway_id}/fullURL":
            return {"url": full_url}
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


@pytest.fixture()
def mock_mprmrest__extract_data_from_element_uid(mocker, request):
    def _extract_data_from_element_uid(element_uid):
        if request.node.name == "test_get_binary_switch_state_valid_on":
            return {"properties": {"state": 1}}
        elif request.node.name == "test_get_binary_switch_state_valid_off":
            return {"properties": {"state": 0}}
        elif request.node.name == "test_get_consumption_valid":
            return {"properties": {"currentValue": 0.58, "totalValue": 125.68}}

    mocker.patch("devolo_home_control_api.mprm_rest.MprmRest._extract_data_from_element_uid",
                 side_effect=_extract_data_from_element_uid)


@pytest.fixture(autouse=True)
def test_data(request):
    request.cls.user = user
    request.cls.password = password
    request.cls.uuid = uuid
    request.cls.gateway_id = gateway_id
    request.cls.full_url = full_url

    request.cls.device_uid = device_uid


@pytest.fixture()
def mprm_instance(request, mock_gateway, mock_inspect_devices_metering_plug, mock_mprmrest__detect_gateway_in_lan):
    request.cls.mprm = MprmRest(gateway_id)


@pytest.fixture(autouse=True)
def clear_mydevolo():
    Mydevolo.del_instance()
