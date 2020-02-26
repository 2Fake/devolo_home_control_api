import json

import pytest

from devolo_home_control_api.backend.mprm_rest import MprmRest
from devolo_home_control_api.backend.mprm_websocket import MprmWebsocket

from ..mocks.mock_mprm_rest import try_local_connection
from ..mocks.mock_websocketapp import MockWebsocketapp


@pytest.fixture()
def mprm_instance(request, mocker, mydevolo, mock_gateway, mock_inspect_devices_metering_plug,
                  mock_mprmrest__detect_gateway_in_lan):
    """ Create a mocked mPRM instance with static test data. """
    if "TestMprmRest" in request.node.nodeid:
        request.cls.mprm = MprmRest(gateway_id=request.cls.gateway.get("id"), url="https://homecontrol.mydevolo.com")
    elif "TestMprmWebsocket" in request.node.nodeid:
        request.cls.mprm = MprmWebsocket(gateway_id=request.cls.gateway.get("id"), url="https://homecontrol.mydevolo.com")
    else:
        mocker.patch("devolo_home_control_api.backend.mprm_websocket.MprmWebsocket.websocket_connection", return_value=None)
        request.cls.mprm = MprmWebsocket(gateway_id=request.cls.gateway.get("id"), url="https://homecontrol.mydevolo.com")
    yield
    request.cls.mprm.del_instance()


@pytest.fixture()
def mock_mprmrest_get_local_session_json_decode_error(mocker):
    """ Create an JSONDecodeError on getting a local session. """
    mocker.patch("devolo_home_control_api.backend.mprm_rest.MprmRest.get_local_session", side_effect=json.JSONDecodeError)


@pytest.fixture()
def mock_mprmrest_get_local_session(mocker):
    """ Mock getting a local session to speed up tests. """
    mocker.patch("devolo_home_control_api.backend.mprm_rest.MprmRest.get_local_session", return_value=True)


@pytest.fixture(autouse=True)
def mock_mprmrest_get_remote_session(mocker, request):
    """ Mock getting a remote session to speed up tests. """
    if request.node.name not in ["test_get_remote_session_JSONDecodeError"]:
        mocker.patch("devolo_home_control_api.backend.mprm_rest.MprmRest.get_remote_session", return_value=True)


@pytest.fixture()
def mock_mprmrest_zeroconf_cache_entries(mocker):
    """ Mock Zeroconf entries. """
    mocker.patch("zeroconf.DNSCache.entries", return_value=[1])


@pytest.fixture()
def mock_mprmrest__detect_gateway_in_lan(mocker, request):
    """ Mock detecting a gateway in the local area network to speed up tests. """
    if request.node.name not in ["test_detect_gateway_in_lan_valid", "test_detect_gateway_in_lan"]:
        mocker.patch("devolo_home_control_api.backend.mprm_rest.MprmRest.detect_gateway_in_lan", return_value=None)


@pytest.fixture()
def mock_mprmrest__extract_data_from_element_uid(mocker, request):
    """ Mock extracting device data. """
    properties = {}
    properties['test_fetch_binary_switch_state_valid_on'] = {"properties": {"state": 1}}
    properties['test_fetch_binary_switch_state_valid_off'] = {"properties": {"state": 0}}
    properties['test_fetch_consumption_valid'] = {
        "properties": {"currentValue": request.cls.devices.get("mains").get("current_consumption"),
                       "totalValue": request.cls.devices.get("mains").get("total_consumption")}}
    properties['test_fetch_led_setting_valid'] = {
        "properties": {"led": request.cls.devices.get("mains").get("led_setting")}}
    properties['test_fetch_param_changed_valid'] = {
        "properties": {"paramChanged": request.cls.devices.get("mains").get("param_changed")}}
    properties['test_fetch_general_device_settings_valid'] = {
        "properties": {"eventsEnabled": request.cls.devices.get("mains").get("events_enabled"),
                       "name": request.cls.devices.get("mains").get("name"),
                       "icon": request.cls.devices.get("mains").get("icon"),
                       "zoneID": request.cls.devices.get("mains").get("zone_id")}}
    properties['test_fetch_protection_setting_valid'] = {
        "properties": {"localSwitch": request.cls.devices.get("mains").get("local_switch"),
                       "remoteSwitch": request.cls.devices.get("mains").get("remote_switch")}}
    properties['test_fetch_voltage_valid'] = {
        "properties": {"value": request.cls.devices.get("mains").get("voltage")}}
    properties['test_update_consumption_valid'] = {
        "properties": {"currentValue": request.cls.devices.get("mains").get("current_consumption"),
                       "totalValue": request.cls.devices.get("mains").get("total_consumption")}}
    properties['test__inspect_device'] = None

    mocker.patch("devolo_home_control_api.backend.mprm_rest.MprmRest.extract_data_from_element_uid",
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
    properties["test_extract_data_from_element_uid"] = {"result": {"items": [{"properties": {"itemName": "test_name"}}]}}
    properties["test_get_all_devices"] = {"result": {"items": [{"properties": {"deviceUIDs": "deviceUIDs"}}]}}

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
def mock_mprmrest__try_local_connection(mocker, request):
    """ Mock finding gateway's IP. """
    mocker.patch("devolo_home_control_api.backend.mprm_rest.MprmRest._try_local_connection", try_local_connection)


@pytest.fixture()
def mock_mprmwebsocket_websocketapp(mocker):
    """ Mock a websocket connection init. """
    mocker.patch("websocket.WebSocketApp.__init__", MockWebsocketapp.__init__)
    mocker.patch("websocket.WebSocketApp.run_forever", MockWebsocketapp.run_forever)


@pytest.fixture()
def mock_mprmwebsocket_websocket_connection(mocker, request):
    """ Mock a running websocket connection to speed up tests. """
    mocker.patch("devolo_home_control_api.backend.mprm_websocket.MprmWebsocket.websocket_connection", return_value=None)


@pytest.fixture()
def mock_mprmrest_get_all_devices(mocker):
    mocker.patch("devolo_home_control_api.backend.mprm_rest.MprmRest.get_all_devices", return_value=[1, 2])
