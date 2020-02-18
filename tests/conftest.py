import json
import sys

import pytest

from devolo_home_control_api.backend.mprm_rest import MprmRest
from devolo_home_control_api.backend.mprm_websocket import MprmWebsocket
from devolo_home_control_api.homecontrol import HomeControl
from devolo_home_control_api.mydevolo import Mydevolo, WrongUrlError

from .mocks.mock_gateway import Gateway
from .mocks.mock_homecontrol import mock__inspect_devices
from .mocks.mock_response import MockResponseConnectTimeout, MockResponseGet, MockResponseJsonError, MockResponsePost, MockResponseReadTimeout

try:
    with open('test_data.json') as file:
        test_data = json.load(file)
except FileNotFoundError:
    print("Please run tests from within the tests directory.")
    sys.exit(127)


@pytest.fixture(autouse=True)
def clear_mydevolo():
    Mydevolo.del_instance()


@pytest.fixture()
def fill_device_data(request):
    consumption_property = request.cls.homecontrol.devices.get(test_data.get('devices').get("mains").get("uid")) \
        .consumption_property
    consumption_property.get(f"devolo.Meter:{test_data.get('devices').get('mains').get('uid')}").current = 0.58
    consumption_property.get(f"devolo.Meter:{test_data.get('devices').get('mains').get('uid')}").total = 125.68

    binary_switch_property = \
        request.cls.homecontrol.devices.get(test_data.get('devices').get("mains").get("uid")).binary_switch_property
    binary_switch_property.get(f"devolo.BinarySwitch:{test_data.get('devices').get('mains').get('uid')}").state = False

    voltage_property = request.cls.homecontrol.devices.get(test_data.get('devices').get("mains").get("uid")).voltage_property
    voltage_property.get(f"devolo.VoltageMultiLevelSensor:{test_data.get('devices').get('mains').get('uid')}").current = 236


@pytest.fixture()
def instance_mydevolo():
    Mydevolo()


@pytest.fixture(autouse=True)
def mock_mydevolo_get_zwave_products(mocker, request):
    return_dict = {'href': 'https://dcloud-test.devolo.net/v1/zwave/products/0x0175/0x0001/0x0011',
                   'manufacturerId': '0x0175',
                   'productTypeId': '0x0001',
                   'productId': '0x0011',
                   'name': 'Metering Plug',
                   'brand': 'devolo',
                   'identifier': 'MT02646',
                   'isZWavePlus': True,
                   'deviceType': 'On/Off Power Switch',
                   'zwaveVersion': '6.51.00',
                   'specificDeviceClass': None,
                   'genericDeviceClass': None}

    if request.node.name not in ["test_get_zwave_products", "test_get_zwave_products_invalid"]:
        mocker.patch("devolo_home_control_api.mydevolo.Mydevolo.get_zwave_products", return_value=return_dict)


@pytest.fixture()
def mock_get_local_session(mocker):
    mocker.patch("devolo_home_control_api.backend.mprm_rest.MprmRest.get_local_session", return_value=True)


@pytest.fixture()
def mock_get_remote_session(mocker):
    mocker.patch("devolo_home_control_api.backend.mprm_rest.MprmRest.get_remote_session", return_value=True)


@pytest.fixture()
def mock_gateway(mocker):
    mocker.patch("devolo_home_control_api.devices.gateway.Gateway.__init__", Gateway.__init__)


@pytest.fixture()
def mock_inspect_devices_metering_plug(mocker):
    mocker.patch("devolo_home_control_api.homecontrol.HomeControl._inspect_devices", mock__inspect_devices)


@pytest.fixture()
def mock_mprmrest__detect_gateway_in_lan(mocker, request):
    if request.node.name not in ["test_detect_gateway_in_lan_valid"]:
        mocker.patch("devolo_home_control_api.backend.mprm_rest.MprmRest.detect_gateway_in_lan", return_value=None)


@pytest.fixture()
def mock_mprmrest__extract_data_from_element_uid(mocker, request):
    properties = {}
    properties['test_fetch_binary_switch_state_valid_on'] = {"properties": {"state": 1}}
    properties['test_fetch_binary_switch_state_valid_off'] = {"properties": {"state": 0}}
    properties['test_fetch_consumption_valid'] = {
        "properties": {"currentValue": test_data.get("devices").get("mains").get("current_consumption"),
                       "totalValue": test_data.get("devices").get("mains").get("total_consumption")}}
    properties['test_fetch_led_setting_valid'] = {
        "properties": {"led": test_data.get("devices").get("mains").get("led_setting")}}
    properties['test_fetch_param_changed_valid'] = {
        "properties": {"paramChanged": test_data.get("devices").get("mains").get("param_changed")}}
    properties['test_fetch_general_device_settings_valid'] = {
        "properties": {"eventsEnabled": test_data.get("devices").get("mains").get("events_enabled"),
                       "name": test_data.get("devices").get("mains").get("name"),
                       "icon": test_data.get("devices").get("mains").get("icon"),
                       "zoneID": test_data.get("devices").get("mains").get("zone_id")}}
    properties['test_fetch_protection_setting_valid'] = {
        "properties": {"localSwitch": test_data.get("devices").get("mains").get("local_switch"),
                       "remoteSwitch": test_data.get("devices").get("mains").get("remote_switch")}}
    properties['test_fetch_voltage_valid'] = {
        "properties": {"value": test_data.get("devices").get("mains").get("voltage")}}
    properties['test_update_consumption_valid'] = {
        "properties": {"currentValue": test_data.get("devices").get("mains").get("current_consumption"),
                       "totalValue": test_data.get("devices").get("mains").get("total_consumption")}}

    mocker.patch("devolo_home_control_api.backend.mprm_rest.MprmRest.extract_data_from_element_uid",
                 return_value=properties.get(request.node.name))


@pytest.fixture()
def mock_mprmrest__post(mocker, request):
    properties = {}
    properties["test_get_name_and_element_uids"] = {"result": {"items": [{"properties":
                                                                          {"itemName": "test_name",
                                                                           "zone": "test_zone",
                                                                           "batteryLevel": "test_battery",
                                                                           "icon": "test_icon",
                                                                           "elementUIDs": "test_element_uids",
                                                                           "settingUIDs": "test_setting_uids",
                                                                           "deviceModelUID": "test_device_model_uid",
                                                                           "status": "test_status"}}]}}
    properties["test_extract_data_from_element_uid"] = {"result": {"items": [{"properties": {"itemName": "test_name"}}]}}
    properties["test_get_all_devices"] = {"result": {"items": [{"properties": {"deviceUIDs": "deviceUIDs"}}]}}

    mocker.patch("devolo_home_control_api.backend.mprm_rest.MprmRest.post", return_value=properties.get(request.node.name))


@pytest.fixture()
def mock_session_post(mocker, request):
    properties = {}
    properties["test_get_local_session_valid"] = {"link": "test_link"}

    mocker.patch("requests.Session.get", return_value=properties.get(request.node.name))


@pytest.fixture()
def mock_response_json(mocker):
    mocker.patch("requests.Session", return_value=MockResponseGet({"link": "test_link"}, status_code=200))


@pytest.fixture()
def mock_response_json_ConnectTimeout(mocker):
    mocker.patch("requests.Session", return_value=MockResponseConnectTimeout({"link": "test_link"}, status_code=200))


@pytest.fixture()
def mock_response_json_JSONDecodeError(mocker):
    mocker.patch("requests.Session", return_value=MockResponseJsonError({"link": "test_link"}, status_code=200))


@pytest.fixture()
def mock_response_requests_ReadTimeout(mocker):
    mocker.patch("requests.Session", return_value=MockResponseReadTimeout({"link": "test_link"}, status_code=200))


@pytest.fixture()
def mock_response_requests_invalid_id(mocker):
    mocker.patch("requests.Session", return_value=MockResponsePost({"link": "test_link"}, status_code=200))


@pytest.fixture()
def mock_response_requests_valid(mocker):
    mocker.patch("requests.Session", return_value=MockResponsePost({"link": "test_link"}, status_code=200))


@pytest.fixture(autouse=True)
def mock_mprmwebsocket_websocket_connection(mocker, request):
    def mock_websocket_connection():
        pass

    mocker.patch("devolo_home_control_api.backend.mprm_websocket.MprmWebsocket.websocket_connection",
                 side_effect=mock_websocket_connection)


@pytest.fixture()
def mock_homecontrol_is_online(mocker):
    mocker.patch("devolo_home_control_api.homecontrol.HomeControl.is_online", return_value=False)


@pytest.fixture()
def mock_mprmrest__post_set(mocker, request):
    status = {}
    status['test_set_binary_switch_valid'] = {"result": {"status": 1}}
    status['test_set_binary_switch_error'] = {"result": {"status": 2}}

    mocker.patch("devolo_home_control_api.backend.mprm_rest.MprmRest.post", return_value=status.get(request.node.name))


@pytest.fixture()
def mock_publisher_dispatch(mocker):
    mocker.patch("devolo_home_control_api.publisher.publisher.Publisher.dispatch", return_value=None)


@pytest.fixture()
def mock_mydevolo__call(mocker, request):
    def _call_mock(url):
        uuid = test_data.get("user").get("uuid")
        gateway_id = test_data.get("gateway").get("id")
        full_url = test_data.get("gateway").get("full_url")

        response = {}
        response[f'https://www.mydevolo.com/v1/users/{uuid}/hc/gateways/{gateway_id}/fullURL'] = {"url": full_url}
        response['https://www.mydevolo.com/v1/users/uuid'] = {"uuid": uuid}
        response[f'https://www.mydevolo.com/v1/users/{uuid}/hc/gateways/status'] = {"items": []} \
            if request.node.name == "test_gateway_ids_empty" else {"items": [{"gatewayId": gateway_id}]}
        response[f'https://www.mydevolo.com/v1/users/{uuid}/hc/gateways/{gateway_id}'] = \
            {"gatewayId": gateway_id, "status": "devolo.hc_gateway.status.online", "state": "devolo.hc_gateway.state.idle"}
        response['https://www.mydevolo.com/v1/hc/maintenance'] = {"state": "off"} \
            if request.node.name == "test_maintenance_off" else {"state": "on"}
        response['https://www.mydevolo.com/v1/zwave/products/0x0060/0x0001/0x000'] = {"brand": "Everspring",
                                                                                      "deviceType": "Door Lock Keypad",
                                                                                      "genericDeviceClass": "Entry Control",
                                                                                      "identifier": "SP814-US",
                                                                                      "isZWavePlus": True,
                                                                                      "manufacturerId": "0x0060",
                                                                                      "name": "Everspring PIR Sensor SP814",
                                                                                      "productId": "0x0002",
                                                                                      "productTypeId": "0x0001",
                                                                                      "zwaveVersion": "6.51.07"}
        return response[url]

    mocker.patch("devolo_home_control_api.mydevolo.Mydevolo._call", side_effect=_call_mock)


@pytest.fixture()
def mock_mydevolo__call_raise_WrongUrlError(mocker):
    def mock_call(url):
        raise WrongUrlError

    mocker.patch("devolo_home_control_api.mydevolo.Mydevolo._call", side_effect=mock_call)


@pytest.fixture()
def mprm_instance(request, mocker, instance_mydevolo, mock_gateway,
                  mock_inspect_devices_metering_plug, mock_mprmrest__detect_gateway_in_lan):
    if "TestMprmRest" in request.node.nodeid:
        request.cls.mprm = MprmRest(gateway_id=test_data.get("gateway").get("id"), url="https://homecontrol.mydevolo.com")
    elif "TestMprmWebsocket" in request.node.nodeid:
        request.cls.mprm = MprmWebsocket(gateway_id=test_data.get("gateway").get("id"), url="https://homecontrol.mydevolo.com")
    else:
        def _websocket_connection_mock():
            pass

        mocker.patch("devolo_home_control_api.backend.mprm_websocket.MprmWebsocket.websocket_connection",
                     side_effect=_websocket_connection_mock)
        request.cls.mprm = MprmWebsocket(gateway_id=test_data.get("gateway").get("id"), url="https://homecontrol.mydevolo.com")
    yield
    request.cls.mprm.del_instance()


@pytest.fixture()
def home_control_instance(request, instance_mydevolo, mock_gateway,
                          mock_inspect_devices_metering_plug, mock_mprmrest__detect_gateway_in_lan):
    request.cls.homecontrol = HomeControl(test_data.get("gateway").get("id"))
    request.cls.homecontrol.devices['hdm:ZWave:F6BF9812/4'].binary_switch_property['devolo.BinarySwitch:hdm:ZWave:F6BF9812/4'] \
        .is_online = request.cls.homecontrol.is_online
    yield
    MprmWebsocket.del_instance()


@pytest.fixture(autouse=True)
def test_data_fixture(request):
    request.cls.user = test_data.get("user")
    request.cls.gateway = test_data.get("gateway")
    request.cls.devices = test_data.get("devices")


@pytest.fixture(autouse=True)
def mock_mprm_create_connection(mocker):
    mocker.patch("devolo_home_control_api.backend.mprm_websocket.MprmWebsocket.create_connection", return_value=None)


@pytest.fixture()
def mock_properties(mocker):
    mocker.patch("devolo_home_control_api.properties.consumption_property.ConsumptionProperty.fetch_consumption",
                 return_value=None)
    mocker.patch("devolo_home_control_api.properties.binary_switch_property.BinarySwitchProperty.fetch_binary_switch_state",
                 return_value=None)
    mocker.patch("devolo_home_control_api.properties.voltage_property.VoltageProperty.fetch_voltage",
                 return_value=None)
    mocker.patch("devolo_home_control_api.properties.settings_property.SettingsProperty.fetch_general_device_settings",
                 return_value=None)
    mocker.patch("devolo_home_control_api.properties.settings_property.SettingsProperty.fetch_param_changed_setting",
                 return_value=None)
    mocker.patch("devolo_home_control_api.properties.settings_property.SettingsProperty.fetch_protection_setting",
                 return_value=None)
    mocker.patch("devolo_home_control_api.properties.settings_property.SettingsProperty.fetch_led_setting",
                 return_value=None)


@pytest.fixture()
def mock_response_wrong_credentials_error(mocker):
    mocker.patch("requests.get", return_value=MockResponseGet({"link": "test_link"}, status_code=403))


@pytest.fixture()
def mock_response_wrong_url_error(mocker):
    mocker.patch("requests.get", return_value=MockResponseGet({"link": "test_link"}, status_code=404))


@pytest.fixture()
def mock_response_valid(mocker):
    mocker.patch("requests.get", return_value=MockResponseGet({"response": "response"}, status_code=200))


@pytest.fixture()
def mock_mydevolo_full_url(mocker):
    def full_URL(gateway_id):
        return gateway_id

    mocker.patch("devolo_home_control_api.mydevolo.Mydevolo.get_full_url", side_effect=full_URL)


@pytest.fixture()
def mock_get_local_session_json_decode_error(mocker):
    def inner():
        raise json.JSONDecodeError(msg="message", doc="doc", pos=1)

    mocker.patch("devolo_home_control_api.backend.mprm_rest.MprmRest.get_local_session", side_effect=inner)


@pytest.fixture()
def mock_websocket_connection(mocker):
    mocker.patch("devolo_home_control_api.backend.mprm_websocket.MprmWebsocket.websocket_connection", return_value=None)
