import pytest

from devolo_home_control_api.backend.mprm_websocket import MprmWebsocket
from devolo_home_control_api.homecontrol import HomeControl

from ..mocks.mock_homecontrol import mock__inspect_devices


@pytest.fixture()
def home_control_instance(request, mydevolo, mock_gateway, mock_mprmwebsocket_websocket_connection,
                          mock_inspect_devices_metering_plug, mock_mprmrest__detect_gateway_in_lan):
    """ Create a mocked Home Control instance with static test data. """
    request.cls.homecontrol = HomeControl(request.cls.gateway.get("id"))
    request.cls.homecontrol.devices['hdm:ZWave:F6BF9812/4'] \
        .binary_switch_property['devolo.BinarySwitch:hdm:ZWave:F6BF9812/4'].is_online = request.cls.homecontrol.is_online
    yield
    MprmWebsocket.del_instance()


@pytest.fixture()
def mock_inspect_devices_metering_plug(mocker, mock_mydevolo__call):
    """ Create a mocked Home Control setup with a Metering Plug. """
    mocker.patch("devolo_home_control_api.homecontrol.HomeControl._inspect_devices", mock__inspect_devices)


@pytest.fixture()
def mock_homecontrol_is_online(mocker):
    """ Let the gateway be offline all the time. """
    mocker.patch("devolo_home_control_api.homecontrol.HomeControl.is_online", return_value=False)
