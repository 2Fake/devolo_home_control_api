import json

import pytest
import requests

from devolo_home_control_api.backend.mprm import Mprm
from devolo_home_control_api.backend.mprm_rest import MprmRest
from devolo_home_control_api.backend.mprm_websocket import MprmWebsocket

from ..mocks.mock_gateway import MockGateway
from ..mocks.mock_mprm import MockMprm
from ..mocks.mock_mprm_rest import try_local_connection
from ..mocks.mock_websocketapp import MockWebsocketapp


@pytest.fixture()
def mock_mprm__try_local_connection(mocker, request):
    """ Mock finding gateway's IP. """
    mocker.patch("devolo_home_control_api.backend.mprm.Mprm._try_local_connection", try_local_connection)


@pytest.fixture()
def mock_mprmrest_all_devices(mocker, request):
    if request.node.name not in ["test_all_devices"]:
        mocker.patch("devolo_home_control_api.backend.mprm_rest.MprmRest.all_devices", return_value=["hdm:ZWave:F6BF9812/2"])


@pytest.fixture()
def mock_mprmrest_get_data_from_uid_list(mocker, request):
    mocker.patch("devolo_home_control_api.backend.mprm_rest.MprmRest.get_data_from_uid_list",
                 return_value=[request.cls.devices.get("mains")])


@pytest.fixture()
def mock_mprmrest_zeroconf_cache_entries(mocker):
    """ Mock Zeroconf entries. """
    mocker.patch("zeroconf.DNSCache.entries", return_value=[1])


@pytest.fixture()
def mock_mprmrest__detect_gateway_in_lan(mocker, request):
    """ Mock detecting a gateway in the local area network to speed up tests. """
    if request.node.name not in ["test_detect_gateway_in_lan_valid", "test_detect_gateway_in_lan"]:
        mocker.patch("devolo_home_control_api.backend.mprm.Mprm.detect_gateway_in_lan", return_value=None)


@pytest.fixture()
def mock_mprmrest__extract_data_from_element_uid(mocker, request):
    """ Mock extracting device data. """
    properties = {}
    properties['test_fetch_binary_switch_state_valid_on'] = {"properties": {"state": 1}}
    properties['test_fetch_binary_switch_state_valid_off'] = {"properties": {"state": 0}}
    properties['test_fetch_consumption_valid'] = {
        "properties": {"currentValue": request.cls.devices.get("mains").get("properties").get("current_consumption"),
                       "totalValue": request.cls.devices.get("mains").get("properties").get("total_consumption")}}
    properties['test_fetch_led_setting_valid'] = {
        "properties": {"led": request.cls.devices.get("mains").get("properties").get("led_setting")}}
    properties['test_fetch_param_changed_valid'] = {
        "properties": {"paramChanged": request.cls.devices.get("mains").get("properties").get("param_changed")}}
    properties['test_fetch_general_device_settings_valid'] = {
        "properties": {"eventsEnabled": request.cls.devices.get("mains").get("properties").get("events_enabled"),
                       "name": request.cls.devices.get("mains").get("properties").get("name"),
                       "icon": request.cls.devices.get("mains").get("properties").get("icon"),
                       "zoneID": request.cls.devices.get("mains").get("properties").get("zone_id")}}
    properties['test_fetch_protection_setting_valid'] = {
        "properties": {"localSwitch": request.cls.devices.get("mains").get("properties").get("local_switch"),
                       "remoteSwitch": request.cls.devices.get("mains").get("properties").get("remote_switch")}}
    properties['test_fetch_voltage_valid'] = {
        "properties": {"value": request.cls.devices.get("mains").get("properties").get("voltage")}}
    properties['test_update_consumption_valid'] = {
        "properties": {"currentValue": request.cls.devices.get("mains").get("properties").get("current_consumption"),
                       "totalValue": request.cls.devices.get("mains").get("properties").get("total_consumption")}}
    properties['test__inspect_device'] = None

    mocker.patch("devolo_home_control_api.backend.mprm_rest.MprmRest.get_data_from_uid_list",
                 return_value=properties.get(request.node.name))


@pytest.fixture()
def mock_mprmrest__post(mocker, request):
    """ Mock getting properties from the mPRM. """
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
    properties["test_get_data_from_uid_list"] = {"result": {"items": [{"properties": {"itemName": "test_name"}}]}}
    properties["test_all_devices"] = {"result": {"items": [{"properties": {"deviceUIDs": "deviceUIDs"}}]}}

    mocker.patch("devolo_home_control_api.backend.mprm_rest.MprmRest.post", return_value=properties.get(request.node.name))


@pytest.fixture()
def mock_mprmrest__post_set(mocker, request):
    """ Mock setting values. """
    status = {}
    status['test_set_binary_switch_valid'] = {"result": {"status": 1}}
    status['test_set_binary_switch_error'] = {"result": {"status": 2}}
    status['test_set_binary_switch_same'] = {"result": {"status": 3}}

    mocker.patch("devolo_home_control_api.backend.mprm_rest.MprmRest.post", return_value=status.get(request.node.name))


@pytest.fixture()
def mock_mprmwebsocket_get_local_session(mocker):
    """ Mock getting a local session to speed up tests. """
    mocker.patch("devolo_home_control_api.backend.mprm_websocket.MprmWebsocket.get_local_session", return_value=True)


@pytest.fixture()
def mock_mprmwebsocket_get_local_session_json_decode_error(mocker):
    """ Create an JSONDecodeError on getting a local session. """
    mocker.patch("devolo_home_control_api.backend.mprm_websocket.MprmWebsocket.get_local_session",
                 side_effect=json.JSONDecodeError("", "", 1))


@pytest.fixture()
def mock_mprmwebsocket_get_remote_session(mocker, request):
    """ Mock getting a remote session to speed up tests. """
    if request.node.name not in ["test_get_remote_session_JSONDecodeError"]:
        mocker.patch("devolo_home_control_api.backend.mprm_websocket.MprmWebsocket.get_remote_session", return_value=True)


@pytest.fixture()
def mock_mprmwebsocket_on_update(mocker):
    mocker.patch("devolo_home_control_api.backend.mprm_websocket.MprmWebsocket.on_update", return_value=None)


@pytest.fixture()
def mock_mprmwebsocket_websocketapp(mocker):
    """ Mock a websocket connection init. """
    mocker.patch("websocket.WebSocketApp.__init__", MockWebsocketapp.__init__)
    mocker.patch("websocket.WebSocketApp.run_forever", MockWebsocketapp.run_forever)


@pytest.fixture()
def mock_mprmwebsocket_websocket_connection(mocker, request):
    """ Mock a running websocket connection to speed up tests. """
    mocker.patch("devolo_home_control_api.backend.mprm_websocket.MprmWebsocket.websocket_connect", return_value=None)


@pytest.fixture()
def mprm_instance(request, mocker, mydevolo, mock_gateway, mock_inspect_devices_metering_plug,
                  mock_mprmrest__detect_gateway_in_lan):
    """ Create a mocked mPRM instance with static test data. """
    if "TestMprmRest" in request.node.nodeid:
        request.cls.mprm = MprmRest()
    elif "TestMprmWebsocket" in request.node.nodeid:
        request.cls.mprm = MprmWebsocket()
    else:
        mocker.patch("devolo_home_control_api.backend.mprm.Mprm.__init__", MockMprm.__init__)
        mocker.patch("devolo_home_control_api.backend.mprm_websocket.MprmWebsocket.websocket_connect", return_value=None)
        request.cls.mprm = Mprm()
        request.cls.mprm._gateway = MockGateway(request.cls.gateway.get("id"))


@pytest.fixture()
def mprm_session():
    session = requests.Session()
    session.url = "https://homecontrol.mydevolo.com"
    return session
