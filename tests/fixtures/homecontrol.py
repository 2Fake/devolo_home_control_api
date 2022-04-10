import pytest

from devolo_home_control_api.homecontrol import HomeControl

from ..mocks.mock_homecontrol import mock__inspect_devices
from ..mocks.mock_mprm_rest import mock_get_data_from_uid_list


@pytest.fixture()
def home_control_instance(
    request,
    mydevolo,
    mock_gateway,
    mock_mprmwebsocket_websocket_connection,
    mock_inspect_devices_metering_plug,
    mock_mprmrest_get_all_zones,
    mock_mprm__detect_gateway_in_lan,
    mock_mprmwebsocket_get_remote_session,
):
    """Create a mocked Home Control instance with static test data."""
    request.cls.homecontrol = HomeControl(request.cls.gateway.get("id"), mydevolo_instance=mydevolo)


@pytest.fixture()
def mock_inspect_devices_metering_plug(mocker, request, mock_mydevolo__call, mock_mprmrest_get_all_devices):
    """Create a mocked Home Control setup with a Metering Plug."""
    if request.node.name not in ["test__inspect_devices"]:
        mocker.patch("devolo_home_control_api.homecontrol.HomeControl._inspect_devices", mock__inspect_devices)


@pytest.fixture()
def mock_extract_data_from_element_uids(mocker, request):
    mocker.patch("devolo_home_control_api.backend.mprm_rest.MprmRest.get_data_from_uid_list", mock_get_data_from_uid_list)


@pytest.fixture()
def mock_inspect_devices(mocker):
    mocker.patch("devolo_home_control_api.homecontrol.HomeControl._inspect_devices", return_value=None)
