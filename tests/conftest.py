import json
import sys

import pytest

from devolo_home_control_api.mprm_rest import MprmRest
from devolo_home_control_api.mprm_websocket import MprmWebsocket
from devolo_home_control_api.mydevolo import Mydevolo, WrongUrlError
from tests.mock_dummy_device import dummy_device
from tests.mock_gateway import Gateway
from tests.mock_metering_plug import metering_plug

try:
    with open('test_data.json') as file:
        test_data = json.load(file)
except FileNotFoundError:
    print("Please run tests from within the tests directory.")
    sys.exit(127)


@pytest.fixture()
def mock_gateway(mocker):
    mocker.patch("devolo_home_control_api.devices.gateway.Gateway.__init__", Gateway.__init__)


@pytest.fixture()
def mock_inspect_devices_metering_plug(mocker):
    def mock__inspect_devices(self):
        for device_type, device in test_data.get("devices").items():
            device_uid = device.get("uid")
            if device_type == "mains":
                self.devices[device_uid] = metering_plug(device_uid=device_uid)
            else:
                self.devices[device_uid] = dummy_device(key=device_type)

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
            return {"gatewayId": gateway_id,
                    "status": "devolo.hc_gateway.status.online",
                    "state": "devolo.hc_gateway.state.idle"}
        elif url == "https://www.mydevolo.com/v1/hc/maintenance":
            if request.node.name == "test_maintenance_off":
                return {"state": "off"}
            else:
                return {"state": "on"}
        else:
            raise WrongUrlError(f"This URL was not mocked: {url}")

    mocker.patch("devolo_home_control_api.mydevolo.Mydevolo._call", side_effect=_call_mock)


@pytest.fixture()
def mock_mprmrest__extract_data_from_element_uid(mocker, request):
    def _extract_data_from_element_uid(element_uid):
        properties = {}
        properties['test_get_binary_switch_state_valid_on'] = {
            "properties": {"state": 1}}
        properties['test_get_binary_switch_state_valid_off'] = {
            "properties": {"state": 0}}
        properties['test_get_consumption_valid'] = {
            "properties": {"currentValue": test_data.get("devices").get("mains").get("current_consumption"),
                           "totalValue": test_data.get("devices").get("mains").get("total_consumption")}}
        properties['test_get_led_setting_valid'] = {
            "properties": {"led": test_data.get("devices").get("mains").get("led_setting")}}
        properties['test_get_param_changed_valid'] = {
            "properties": {"paramChanged": test_data.get("devices").get("mains").get("param_changed")}}
        properties['test_get_general_device_settings_valid'] = {
            "properties": {"eventsEnabled": test_data.get("devices").get("mains").get("events_enabled"),
                           "name": test_data.get("devices").get("mains").get("name"),
                           "icon": test_data.get("devices").get("mains").get("icon"),
                           "zoneID": test_data.get("devices").get("mains").get("zone_id")}}
        properties['test_get_protection_setting_valid'] = {
            "properties": {"localSwitch": test_data.get("devices").get("mains").get("local_switch"),
                           "remoteSwitch": test_data.get("devices").get("mains").get("remote_switch")}}
        properties['test_get_voltage_valid'] = {
            "properties": {"value": test_data.get("devices").get("mains").get("voltage")}}
        properties['test_update_consumption_valid'] = {
            "properties": {"currentValue": test_data.get("devices").get("mains").get("current_consumption"),
                           "totalValue": test_data.get("devices").get("mains").get("total_consumption")}}
        return properties.get(request.node.name)

    mocker.patch("devolo_home_control_api.mprm_rest.MprmRest._extract_data_from_element_uid",
                 side_effect=_extract_data_from_element_uid)


@pytest.fixture()
def mock_mprmrest__post_set(mocker, request):
    def _post_mock(data):
        if request.node.name == "test_set_binary_switch_valid":
            return {"result": {"status": 1}}
        elif request.node.name == "test_set_binary_switch_error":
            return {"result": {"status": 2}}

    mocker.patch("devolo_home_control_api.mprm_rest.MprmRest._post", side_effect=_post_mock)


@pytest.fixture(autouse=True)
def test_data_fixture(request):
    request.cls.user = test_data.get("user")
    request.cls.gateway = test_data.get("gateway")
    request.cls.devices = test_data.get("devices")


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
    consumption_property = request.cls.mprm.devices.get(test_data.get('devices').get("mains").get("uid")).consumption_property
    consumption_property.get(f"devolo.Meter:{test_data.get('devices').get('mains').get('uid')}").current = 0.58
    consumption_property.get(f"devolo.Meter:{test_data.get('devices').get('mains').get('uid')}").total = 125.68

    binary_switch_property = \
        request.cls.mprm.devices.get(test_data.get('devices').get("mains").get("uid")).binary_switch_property
    binary_switch_property.get(f"devolo.BinarySwitch:{test_data.get('devices').get('mains').get('uid')}").state = False

    voltage_property = request.cls.mprm.devices.get(test_data.get('devices').get("mains").get("uid")).voltage_property
    voltage_property.get(f"devolo.VoltageMultiLevelSensor:{test_data.get('devices').get('mains').get('uid')}").current = 236


@pytest.fixture(autouse=True)
def clear_mydevolo():
    Mydevolo.del_instance()
