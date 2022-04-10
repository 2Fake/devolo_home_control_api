import pytest
import requests

from devolo_home_control_api.backend.mprm_rest import MprmRest

from ..mocks.mock_gateway import MockGateway
from ..mocks.mock_mprm_rest import try_local_connection
from ..mocks.mock_service_browser import ServiceBrowser
from ..mocks.mock_websocket import try_reconnect
from ..mocks.mock_websocketapp import MockWebsocketapp
from ..mocks.mock_zeroconf import Zeroconf
from ..stubs.mprm import StubMprm
from ..stubs.mprm_websocket import StubMprmWebsocket


@pytest.fixture()
def mock_mprm_get_local_session(mocker):
    """Mock getting a local session to speed up tests."""
    mocker.patch("devolo_home_control_api.backend.mprm.Mprm.get_local_session", return_value=True)


@pytest.fixture()
def mock_mprm_service_browser(mocker):
    """Mock Zeroconf ServiceBrowser."""
    mocker.patch("zeroconf.ServiceBrowser.__init__", ServiceBrowser.__init__)
    mocker.patch("zeroconf.ServiceBrowser.cancel", ServiceBrowser.cancel)
    mocker.patch("zeroconf.Zeroconf.get_service_info", Zeroconf.get_service_info)


@pytest.fixture()
def mock_mprm__detect_gateway_in_lan(mocker, request):
    """Mock detecting a gateway in the local area network to speed up tests."""
    if request.node.name not in ["test_detect_gateway_in_lan_valid", "test_detect_gateway_in_lan"]:
        mocker.patch(
            "devolo_home_control_api.backend.mprm.Mprm.detect_gateway_in_lan", return_value=request.cls.gateway["local_ip"]
        )


@pytest.fixture()
def mock_mprm__try_local_connection(mocker):
    """Mock finding gateway's IP."""
    mocker.patch("devolo_home_control_api.backend.mprm.Mprm._try_local_connection", try_local_connection)


@pytest.fixture()
def mock_mprmrest_get_all_devices(mocker, request):
    """Mock getting all devices from the mPRM."""
    if request.node.name not in ["test_get_all_devices"]:
        mocker.patch(
            "devolo_home_control_api.backend.mprm_rest.MprmRest.get_all_devices", return_value=["hdm:ZWave:F6BF9812/2"]
        )


@pytest.fixture()
def mock_mprmrest_get_all_zones(mocker, request):
    """Mock getting all zones from the mPRM."""
    if request.node.name not in ["test_get_all_zones"]:
        mocker.patch(
            "devolo_home_control_api.backend.mprm_rest.MprmRest.get_all_zones", return_value=request.cls.gateway["zones"]
        )


@pytest.fixture()
def mock_mprmrest__extract_data_from_element_uid(mocker, request):
    """Mock extracting device data."""
    properties = {
        "test_fetch_binary_switch_state_valid_on": {"properties": {"state": 1}},
        "test_fetch_binary_switch_state_valid_off": {"properties": {"state": 0}},
        "test_fetch_consumption_valid": {
            "properties": {
                "currentValue": request.cls.devices.get("mains").get("properties").get("current_consumption"),
                "totalValue": request.cls.devices.get("mains").get("properties").get("total_consumption"),
            }
        },
        "test_fetch_led_setting_valid": {
            "properties": {"led": request.cls.devices.get("mains").get("properties").get("led_setting")}
        },
        "test_fetch_param_changed_valid": {
            "properties": {"paramChanged": request.cls.devices.get("mains").get("properties").get("param_changed")}
        },
        "test_fetch_general_device_settings_valid": {
            "properties": {
                "eventsEnabled": request.cls.devices.get("mains").get("properties").get("events_enabled"),
                "name": request.cls.devices.get("mains").get("properties").get("name"),
                "icon": request.cls.devices.get("mains").get("properties").get("icon"),
                "zoneID": request.cls.devices.get("mains").get("properties").get("zone_id"),
            }
        },
        "test_fetch_protection_setting_valid": {
            "properties": {
                "localSwitch": request.cls.devices.get("mains").get("properties").get("local_switch"),
                "remoteSwitch": request.cls.devices.get("mains").get("properties").get("remote_switch"),
            }
        },
        "test_fetch_voltage_valid": {
            "properties": {"value": request.cls.devices.get("mains").get("properties").get("voltage")}
        },
        "test_update_consumption_valid": {
            "properties": {
                "currentValue": request.cls.devices.get("mains").get("properties").get("current_consumption"),
                "totalValue": request.cls.devices.get("mains").get("properties").get("total_consumption"),
            }
        },
        "test__inspect_device": None,
    }

    mocker.patch(
        "devolo_home_control_api.backend.mprm_rest.MprmRest.get_data_from_uid_list",
        return_value=properties.get(request.node.name),
    )


@pytest.fixture()
def mock_mprmrest__post(mocker, request):
    """Mock getting properties from the mPRM."""
    test_case = request.node.name.split("[")[0]
    properties = {
        "test_get_name_and_element_uids": {
            "result": {
                "items": [
                    {
                        "properties": {
                            "itemName": "test_name",
                            "zone": "test_zone",
                            "batteryLevel": "test_battery",
                            "icon": "test_icon",
                            "elementUIDs": "test_element_uids",
                            "settingUIDs": "test_setting_uids",
                            "deviceModelUID": "test_device_model_uid",
                            "status": "test_status",
                        }
                    }
                ]
            }
        },
        "test_get_data_from_uid_list": {"result": {"items": [{"properties": {"itemName": "test_name"}}]}},
        "test_get_all_devices": {"result": {"items": [{"properties": {"deviceUIDs": "deviceUIDs"}}]}},
        "test_get_all_zones": {"result": {"items": [{"properties": {"zones": [{"id": "hz_3", "name": "Office"}]}}]}},
        "test_set_success": {"result": {"status": 1}},
        "test_set_failed": {"result": {"status": 0}},
        "test_set_doubled": {"result": {"status": 2}},
    }

    mocker.patch("devolo_home_control_api.backend.mprm_rest.MprmRest._post", return_value=properties[test_case])


@pytest.fixture()
def mock_mprmwebsocket_get_remote_session(mocker, request):
    """Mock getting a remote session to speed up tests."""
    if request.node.name not in ["test_get_remote_session_JSONDecodeError"]:
        mocker.patch("devolo_home_control_api.backend.mprm.Mprm.get_remote_session", return_value=True)


@pytest.fixture()
def mock_mprmwebsocket_on_update(mocker):
    """Mock websocket message processing."""
    mocker.patch("devolo_home_control_api.backend.mprm_websocket.MprmWebsocket.on_update", return_value=None)


@pytest.fixture()
def mock_mprmwebsocket_try_reconnect(mocker):
    """Mock reconnect attemt as successful."""
    mocker.patch("devolo_home_control_api.backend.mprm_websocket.MprmWebsocket._try_reconnect", try_reconnect)


@pytest.fixture()
def mock_mprmwebsocket_websocketapp(mocker):
    """Mock a websocket connection init."""
    mocker.patch("websocket.WebSocketApp.__init__", MockWebsocketapp.__init__)
    mocker.patch("websocket.WebSocketApp.close", MockWebsocketapp.close)
    mocker.patch("websocket.WebSocketApp.run_forever", MockWebsocketapp.run_forever)


@pytest.fixture()
def mock_mprmwebsocket_websocket_connection(mocker):
    """Mock a running websocket connection to speed up tests."""
    mocker.patch(
        "devolo_home_control_api.backend.mprm_websocket.MprmWebsocket.wait_for_websocket_establishment", return_value=False
    )
    mocker.patch("devolo_home_control_api.backend.mprm_websocket.MprmWebsocket.websocket_connect", return_value=None)


@pytest.fixture()
def mock_mprmwebsocket_websocket_disconnect(mocker):
    """Mock closing a websocket connection."""
    mocker.patch("devolo_home_control_api.backend.mprm_websocket.MprmWebsocket.websocket_disconnect", return_value=None)


@pytest.fixture()
def mprm_instance(
    request, mocker, mydevolo, mock_gateway, mock_inspect_devices_metering_plug, mock_mprm__detect_gateway_in_lan
):
    """Create a mocked mPRM instance with static test data."""
    if "TestMprmRest" in request.node.nodeid:
        request.cls.mprm = MprmRest()
    elif "TestMprmWebsocket" in request.node.nodeid:
        request.cls.mprm = StubMprmWebsocket()
    else:
        mocker.patch("devolo_home_control_api.backend.mprm_websocket.MprmWebsocket.websocket_connect", return_value=None)
        request.cls.mprm = StubMprm()
        request.cls.mprm.gateway = MockGateway(request.cls.gateway.get("id"), mydevolo=mydevolo)


@pytest.fixture()
def mprm_session():
    """Mock a valid mPRM session."""
    session = requests.Session()
    session.url = "https://homecontrol.mydevolo.com"
    return session
