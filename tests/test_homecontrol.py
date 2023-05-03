"""Test the Home Control setup."""
import json
import sys
from unittest.mock import patch

import pytest
import requests
from requests_mock import Mocker
from syrupy.assertion import SnapshotAssertion

from devolo_home_control_api.exceptions.gateway import GatewayOfflineError
from devolo_home_control_api.homecontrol import HomeControl
from devolo_home_control_api.mydevolo import Mydevolo

from . import GATEWAY_FULLURL, MAINTENANCE_URL, Subscriber, load_fixture
from .mocks import WEBSOCKET


@pytest.mark.skipif(sys.version_info < (3, 8))
@pytest.mark.freeze_time("2023-04-28T08:00:00")
def test_setup_local(local_gateway: HomeControl, snapshot: SnapshotAssertion) -> None:
    """Test setting up locally."""
    assert local_gateway.gateway.local_connection
    assert local_gateway.devices == snapshot


@pytest.mark.usefixtures("maintenance_mode")
def test_setup_local_while_in_maintenance(local_gateway: HomeControl) -> None:
    """Test setting up locally while mydevolo is in maintenance mode."""
    assert local_gateway.gateway.local_connection


@pytest.mark.usefixtures("disable_external_access")
def test_setup_local_without_external_access(local_gateway: HomeControl) -> None:
    """Test setting up locally while external access is prohibited."""
    assert local_gateway.gateway.local_connection


@pytest.mark.usefixtures("local_gateway")
def test_setup_local_gateway_offline(mydevolo: Mydevolo, gateway_id: str, gateway_ip: str, requests_mock: Mocker) -> None:
    """Test setup failure when gateway is offline."""
    requests_mock.get(f"http://{gateway_ip}/dhlp/portal/full", exc=requests.exceptions.ConnectionError)
    with pytest.raises(GatewayOfflineError):
        HomeControl(gateway_id, mydevolo)

    requests_mock.get(f"http://{gateway_ip}/dhlp/portal/full", status_code=requests.codes.unavailable)
    with pytest.raises(GatewayOfflineError):
        HomeControl(gateway_id, mydevolo)


@pytest.mark.skipif(sys.version_info < (3, 8))
@pytest.mark.freeze_time("2023-04-28T08:00:00")
def test_setup_remote(remote_gateway: HomeControl, snapshot: SnapshotAssertion) -> None:
    """Test setting up remotely."""
    assert not remote_gateway.gateway.local_connection
    assert remote_gateway.devices == snapshot


@pytest.mark.usefixtures("remote_gateway")
def test_setup_remote_gateway_offline(mydevolo: Mydevolo, gateway_id: str, requests_mock: Mocker) -> None:
    """Test setup failure when gateway is offline."""
    requests_mock.get(GATEWAY_FULLURL, status_code=requests.codes.unavailable)
    with pytest.raises(GatewayOfflineError):
        HomeControl(gateway_id, mydevolo)


@pytest.mark.usefixtures("remote_gateway")
def test_setup_remote_maintenance(mydevolo: Mydevolo, gateway_id: str, requests_mock: Mocker) -> None:
    """Test failing setup remotely while mydevolo is in maintenance mode."""
    requests_mock.get(MAINTENANCE_URL, json={"state": "off"})
    with pytest.raises(ConnectionError):
        HomeControl(gateway_id, mydevolo)


@pytest.mark.usefixtures("remote_gateway", "disable_external_access")
def test_setup_remote_external_access(mydevolo: Mydevolo, gateway_id: str) -> None:
    """Test failing setup remotely while external access is prohibited."""
    with pytest.raises(ConnectionError):
        HomeControl(gateway_id, mydevolo)


def test_context_manager(mydevolo: Mydevolo, gateway_id: str, gateway_ip: str, requests_mock: Mocker) -> None:
    """Test setting up using a conext manager."""
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
    with HomeControl(gateway_id, mydevolo) as homecontrol:
        assert homecontrol


def test_update_online_state(local_gateway: HomeControl, gateway_ip: str, requests_mock: Mocker) -> None:
    """Test updating the online state."""
    local_gateway.gateway.online = False
    local_gateway.gateway.sync = False
    local_gateway.gateway.update_state()
    assert local_gateway.gateway.online
    assert local_gateway.gateway.sync

    requests_mock.post(f"http://{gateway_ip}/remote/json-rpc", exc=requests.exceptions.ConnectionError)
    with pytest.raises(GatewayOfflineError):
        local_gateway.refresh_session()
    assert not local_gateway.gateway.online
    assert not local_gateway.gateway.sync

    WEBSOCKET.recv_packet(json.dumps(load_fixture("homecontrol_gateway_status")))
    assert local_gateway.gateway.online
    assert local_gateway.gateway.sync


def test_update_zones(local_gateway: HomeControl) -> None:
    """Update zones."""
    fixture = load_fixture("homecontrol_grouping")
    WEBSOCKET.recv_packet(json.dumps(fixture))
    assert len(local_gateway.gateway.zones) == len(fixture["properties"]["property.value.new"])


@pytest.mark.usefixtures("local_gateway")
def test_device_added() -> None:
    """Test handling an added device."""
    fixture = load_fixture("homecontrol_device_new")
    with patch("devolo_home_control_api.homecontrol.HomeControl._inspect_devices") as inspect_devices:
        WEBSOCKET.recv_packet(json.dumps(fixture))
        inspect_devices.assert_called_once_with([fixture["properties"]["property.value.new"][-1]])


def test_device_deleted(local_gateway: HomeControl) -> None:
    """Test handling an deleted device."""
    fixture = load_fixture("homecontrol_device_del")
    WEBSOCKET.recv_packet(json.dumps(fixture))
    assert len(local_gateway.devices) == len(fixture["properties"]["property.value.new"])


@pytest.mark.parametrize(
    "useless", ["devolo.HttpRequest", "devolo.PairDevice", "devolo.RemoveDevice", "devolo.mprm.gw.GatewayManager"]
)
def test_ignore_pending_operations(local_gateway: HomeControl, useless: str) -> None:
    """Test ignoring certail pending operations."""
    subscriber = Subscriber(useless)
    local_gateway.publisher.register(useless, subscriber)
    fixture = load_fixture("homecontrol_pending_operation")
    fixture["properties"]["uid"] = useless
    WEBSOCKET.recv_packet(json.dumps(fixture))
    subscriber.update.assert_not_called()
