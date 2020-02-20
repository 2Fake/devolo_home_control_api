import json
import sys

import pytest

from devolo_home_control_api.homecontrol import HomeControl
from devolo_home_control_api.backend.mprm_websocket import MprmWebsocket

from .mocks.mock_gateway import Gateway
from .mocks.mock_homecontrol import mock__inspect_devices


try:
    with open("test_data.json") as file:
        test_data = json.load(file)
except FileNotFoundError:
    print("Please run tests from within the tests directory.")
    sys.exit(127)


pytest_plugins = ['tests.fixtures.mprm', 'tests.fixtures.mydevolo', 'tests.fixtures.requests']


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
def mock_gateway(mocker):
    mocker.patch("devolo_home_control_api.devices.gateway.Gateway.__init__", Gateway.__init__)


@pytest.fixture()
def mock_inspect_devices_metering_plug(mocker, mock_mydevolo__call):
    mocker.patch("devolo_home_control_api.homecontrol.HomeControl._inspect_devices", mock__inspect_devices)


@pytest.fixture()
def mock_homecontrol_is_online(mocker):
    mocker.patch("devolo_home_control_api.homecontrol.HomeControl.is_online", return_value=False)


@pytest.fixture()
def mock_publisher_dispatch(mocker):
    mocker.patch("devolo_home_control_api.publisher.publisher.Publisher.dispatch", return_value=None)


@pytest.fixture()
def home_control_instance(request, mydevolo, mock_gateway, mock_mprmwebsocket_websocket_connection,
                          mock_inspect_devices_metering_plug, mock_mprmrest__detect_gateway_in_lan):
    request.cls.homecontrol = HomeControl(test_data.get("gateway").get("id"))
    request.cls.homecontrol.devices['hdm:ZWave:F6BF9812/4'] \
        .binary_switch_property['devolo.BinarySwitch:hdm:ZWave:F6BF9812/4'].is_online = request.cls.homecontrol.is_online
    yield
    MprmWebsocket.del_instance()


@pytest.fixture(autouse=True)
def test_data_fixture(request):
    request.cls.user = test_data.get("user")
    request.cls.gateway = test_data.get("gateway")
    request.cls.devices = test_data.get("devices")


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
