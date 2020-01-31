import json

import pytest

from devolo_home_control_api.mprm_rest import MprmRest
from devolo_home_control_api.mprm_websocket import MprmWebsocket
from devolo_home_control_api.mydevolo import Mydevolo, WrongUrlError
from tests.mock_gateway import Gateway
from tests.mock_metering_plug import metering_plug

with open('test_data.json') as file:
    test_data = json.load(file)


@pytest.fixture()
def mock_gateway(mocker):
    mocker.patch("devolo_home_control_api.devices.gateway.Gateway.__init__", Gateway.__init__)


@pytest.fixture()
def mock_inspect_devices_metering_plug(mocker):
    def mock__inspect_devices(self):
        device_uid = test_data.get("device").get("mains").get("uid")
        self.devices[device_uid] = metering_plug(device_uid=device_uid)

    mocker.patch("devolo_home_control_api.mprm_rest.MprmRest._inspect_devices", mock__inspect_devices)


@pytest.fixture()
def mock_mprmrest__detect_gateway_in_lan(mocker):
    def _detect_gateway_in_lan(self):
        return None

    mocker.patch("devolo_home_control_api.mprm_rest.MprmRest._detect_gateway_in_lan", _detect_gateway_in_lan)


@pytest.fixture()
def mock_mydevolo__call(mocker, request):
    def _call_mock(url):
        uuid = test_data.get("user").get("uuid")
        gateway_id = test_data.get("gateway").get("id")
        full_url = test_data.get("gateway").get("full_url")

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
            raise WrongUrlError(f"This URL was not mocked: {url}")

    mocker.patch("devolo_home_control_api.mydevolo.Mydevolo._call", side_effect=_call_mock)


@pytest.fixture()
def mock_mprmrest__extract_data_from_element_uid(mocker, request):
    def _extract_data_from_element_uid(element_uid):
        if request.node.name == "test_get_binary_switch_state_valid_on":
            return {"properties": {"state": 1}}
        elif request.node.name == "test_get_binary_switch_state_valid_off":
            return {"properties": {"state": 0}}
        elif request.node.name == "test_get_consumption_valid":
            return {"properties": {"currentValue": test_data.get("device").get("mains").get("current_consumption"),
                                   "totalValue": test_data.get("device").get("mains").get("total_consumption")}}
        elif request.node.name == "test_get_led_setting_valid":
            return {"properties": {"led": test_data.get("device").get("mains").get("led_setting")}}
        elif request.node.name == "test_get_param_changed_valid":
            return {"properties": {"paramChanged": test_data.get("device").get("mains").get("param_changed")}}
        elif request.node.name == "test_get_general_device_settings_valid":
            return {"properties": {"eventsEnabled": test_data.get("device").get("mains").get("events_enabled"),
                                   "name": test_data.get("device").get("mains").get("name"),
                                   "icon": test_data.get("device").get("mains").get("icon"),
                                   "zoneID": test_data.get("device").get("mains").get("zone_id")}}
        elif request.node.name == "test_get_protection_setting_valid":
            return {"properties": {"localSwitch": test_data.get("device").get("mains").get("local_switch"),
                                   "remoteSwitch": test_data.get("device").get("mains").get("remote_switch")}}
        elif request.node.name == "test_get_voltage_valid":
            return {"properties": {"value": test_data.get("device").get("mains").get("voltage")}}
        elif request.node.name == "test_update_consumption_valid":
            return {"properties": {"currentValue": test_data.get("device").get("mains").get("current_consumption"),
                                   "totalValue": test_data.get("device").get("mains").get("total_consumption")}}

    mocker.patch("devolo_home_control_api.mprm_rest.MprmRest._extract_data_from_element_uid",
                 side_effect=_extract_data_from_element_uid)


@pytest.fixture()
def mock_mprmrest__post_set(mocker, request):
    def _post_mock(data):
        if request.node.name == "test_set_binary_switch_valid":
            return {"result": {"status": 1}}
        elif request.node.name == "test_set_binary_switch_error":
            return {"result": {"status": 3}}

    mocker.patch("devolo_home_control_api.mprm_rest.MprmRest._post", side_effect=_post_mock)


@pytest.fixture(autouse=True)
def test_data_fixture(request):
    request.cls.user = test_data.get("user")
    request.cls.gateway = test_data.get("gateway")
    request.cls.device = test_data.get("device")


@pytest.fixture()
def mprm_instance(request, mocker, mock_gateway, mock_inspect_devices_metering_plug, mock_mprmrest__detect_gateway_in_lan):
    if "TestMprmRest" in request.node.nodeid:
        request.cls.mprm = MprmRest(test_data.get("gateway").get("id"))
    else:
        def _websocket_connection_mock():
            pass
        mocker.patch("devolo_home_control_api.mprm_websocket.MprmWebsocket._websocket_connection",
                     side_effect=_websocket_connection_mock)
        request.cls.mprm = MprmWebsocket(test_data.get("gateway").get("id"))


@pytest.fixture()
def fill_device_data(request):
    consumption_property = request.cls.mprm.devices.get(test_data.get('device').get("mains").get("uid")).consumption_property
    consumption_property.get(f"devolo.Meter:{request.cls.device.get('mains').get('uid')}").current = 0.58
    consumption_property.get(f"devolo.Meter:{request.cls.device.get('mains').get('uid')}").total = 125.68

    binary_switch_property = request.cls.mprm.devices.get(test_data.get('device').get("mains").get("uid")).binary_switch_property
    binary_switch_property.get(f"devolo.BinarySwitch:{request.cls.device.get('mains').get('uid')}").state = False

    voltage_property = request.cls.mprm.devices.get(test_data.get('device').get("mains").get("uid")).voltage_property
    voltage_property.get(f"devolo.VoltageMultiLevelSensor:{request.cls.device.get('mains').get('uid')}").current = 236

@pytest.fixture(autouse=True)
def clear_mydevolo():
    Mydevolo.del_instance()
