"""Configure tests."""
from socket import inet_aton
from typing import Generator
from unittest.mock import patch

import pytest
from requests_mock import Mocker
from syrupy.assertion import SnapshotAssertion
from zeroconf import ServiceInfo

from devolo_home_control_api.homecontrol import HomeControl
from devolo_home_control_api.mydevolo import Mydevolo

from . import (
    GATEWAY_DETAILS_URL,
    GATEWAY_FULLURL,
    GATEWAY_LOCATION_URL,
    GATEWAY_STATUS_URL,
    HOMECONTROL_URL,
    MAINTENANCE_URL,
    STANDARD_TIMEZONE_URL,
    UUID_URL,
    ZWAVE_PRODUCTS_URL,
    DifferentDirectoryExtension,
    load_fixture,
)
from .mocks import MockServiceBrowser, MockWebSocketApp


@pytest.fixture(autouse=True)
def block_communication(gateway_ip: str) -> Generator[None, None, None]:
    """Block unwanted external communication."""
    service_info = ServiceInfo(
        type_="_dvl-deviceapi._tcp.local.",
        name="dvl-deviceapi._dvl-deviceapi._tcp.local.",
        server="devolo-homecontrol.local.",
        addresses=[inet_aton(gateway_ip)],
    )
    with patch("devolo_home_control_api.backend.mprm.ServiceBrowser", MockServiceBrowser), patch(
        "devolo_home_control_api.backend.mprm_websocket.websocket.WebSocketApp", MockWebSocketApp
    ), patch("devolo_home_control_api.backend.mprm.Zeroconf.get_service_info", return_value=service_info):
        yield


@pytest.fixture
def disable_external_access() -> Generator[None, None, None]:
    """Temporary forbidd external access."""
    gateway_details = load_fixture("mydevolo_gateway_details")
    gateway_details["externalAccess"] = False
    yield
    gateway_details["externalAccess"] = True


@pytest.fixture
def gateway_id() -> str:
    """Get a valid gateway ID."""
    details = load_fixture("mydevolo_gateway_details")
    return details["gatewayId"]


@pytest.fixture
def gateway_ip() -> str:
    """Get the gateway's IP address."""
    return "192.0.2.1"


@pytest.fixture
def local_gateway(
    mydevolo: Mydevolo, gateway_id: str, gateway_ip: str, requests_mock: Mocker
) -> Generator[HomeControl, None, None]:
    """Emulate a local gateway connection."""
    connection = load_fixture("homecontrol_local_session")
    connection["link"] = f"http://{gateway_ip}/dhlp/portal/full/?token=54e8c82fc921ee7e&"
    requests_mock.get(f"http://{gateway_ip}/dhlp/port/full")
    requests_mock.get(f"http://{gateway_ip}/dhlp/portal/full", json=connection)
    requests_mock.get(connection["link"])
    requests_mock.post(
        f"http://{gateway_ip}/remote/json-rpc",
        [
            {"json": load_fixture("homecontrol_zones")},
            {"json": load_fixture("homecontrol_device_page")},
            {"json": load_fixture("homecontrol_devices")},
            {"json": load_fixture("homecontrol_device_details")},
        ],
    )
    homecontrol = HomeControl(gateway_id, mydevolo)
    yield homecontrol
    homecontrol.websocket_disconnect("Test finished.")


@pytest.fixture
def maintenance_mode(requests_mock: Mocker) -> None:
    """Simulate mydevolo maitenance mode."""
    requests_mock.get(MAINTENANCE_URL, json={"state": "off"})


@pytest.fixture
def remote_gateway(mydevolo: Mydevolo, gateway_id: str, requests_mock: Mocker) -> Generator[HomeControl, None, None]:
    """Emulate a remote gateway connection."""
    requests_mock.get(
        f"{HOMECONTROL_URL}/dhp/portal/fullLogin/?token=1410000000001_1:24b1516b93adebf7&X-MPRM-LB=1410000000001_1"
    )
    requests_mock.post(
        f"{HOMECONTROL_URL}/remote/json-rpc",
        [
            {"json": load_fixture("homecontrol_zones")},
            {"json": load_fixture("homecontrol_device_page")},
            {"json": load_fixture("homecontrol_devices")},
            {"json": load_fixture("homecontrol_device_details")},
        ],
    )
    with patch("devolo_home_control_api.homecontrol.Mprm.detect_gateway_in_lan"):
        homecontrol = HomeControl(gateway_id, mydevolo)
        yield homecontrol
        homecontrol.websocket_disconnect("Test finished.")


@pytest.fixture
def mydevolo(requests_mock: Mocker) -> Mydevolo:
    """Create a mydevolo object with static test data."""
    requests_mock.get(UUID_URL, json=load_fixture("mydevolo_uuid"))
    requests_mock.get(GATEWAY_STATUS_URL, json=load_fixture("mydevolo_gateway_status"))
    requests_mock.get(GATEWAY_DETAILS_URL, json=load_fixture("mydevolo_gateway_details"))
    requests_mock.get(GATEWAY_LOCATION_URL, json=load_fixture("mydevolo_gateway_location"))
    requests_mock.get(GATEWAY_FULLURL, json=load_fixture("mydevolo_gateway_fullurl"))
    requests_mock.get(ZWAVE_PRODUCTS_URL, json=load_fixture("mydevolo_zwave_products"))
    requests_mock.get(MAINTENANCE_URL, json=load_fixture("mydevolo_maintenance"))
    requests_mock.get(STANDARD_TIMEZONE_URL, json=load_fixture("mydevolo_standard_timezone"))
    return Mydevolo()


@pytest.fixture
def snapshot(snapshot: SnapshotAssertion) -> SnapshotAssertion:
    """Return snapshot assertion fixture with nicer path."""
    return snapshot.use_extension(DifferentDirectoryExtension)
