"""Test mydevolo."""
import sys
from http import HTTPStatus

import pytest
from requests_mock import Mocker
from syrupy.assertion import SnapshotAssertion

from devolo_home_control_api.exceptions import GatewayOfflineError, WrongUrlError
from devolo_home_control_api.mydevolo import Mydevolo

from . import GATEWAY_DETAILS_URL, GATEWAY_FULLURL, GATEWAY_STATUS_URL, MAINTENANCE_URL, UUID_URL, ZWAVE_PRODUCTS_URL


def test_cache_clear(mydevolo: Mydevolo) -> None:
    """Test clearing the UUID cache on new username or password."""
    mydevolo.user = "test@test.com"
    mydevolo.password = "secret"
    assert mydevolo.user == "test@test.com"
    assert mydevolo.password == "secret"
    assert mydevolo.uuid.cache_info().currsize == 0


def test_credential_verification(mydevolo: Mydevolo, requests_mock: Mocker) -> None:
    """Test credentil verification."""
    mydevolo.user = "test@test.com"
    mydevolo.password = "secret"
    assert mydevolo.credentials_valid()

    requests_mock.get(UUID_URL, status_code=HTTPStatus.FORBIDDEN)
    mydevolo.uuid.cache_clear()
    assert not mydevolo.credentials_valid()


@pytest.mark.skipif(sys.version_info < (3, 8), reason="Tests with snapshots need at least Python 3.8")
def test_get_gateway_ids(mydevolo: Mydevolo, requests_mock: Mocker, snapshot: SnapshotAssertion) -> None:
    """Test getting gateway serial numbers."""
    gateway_ids = mydevolo.get_gateway_ids()
    assert gateway_ids == snapshot

    requests_mock.get(GATEWAY_STATUS_URL, json={"items": []})
    with pytest.raises(IndexError):
        mydevolo.get_gateway_ids()


@pytest.mark.skipif(sys.version_info < (3, 8), reason="Tests with snapshots need at least Python 3.8")
def test_get_gateway(mydevolo: Mydevolo, gateway_id: str, requests_mock: Mocker, snapshot: SnapshotAssertion) -> None:
    """Test getting gateway details."""
    gateway = mydevolo.get_gateway(gateway_id)
    assert gateway == snapshot

    requests_mock.get(GATEWAY_DETAILS_URL, status_code=HTTPStatus.NOT_FOUND)
    with pytest.raises(WrongUrlError):
        mydevolo.get_gateway(gateway_id)

    requests_mock.get(GATEWAY_FULLURL, status_code=HTTPStatus.SERVICE_UNAVAILABLE)
    with pytest.raises(GatewayOfflineError):
        mydevolo.get_full_url(gateway_id)


@pytest.mark.skipif(sys.version_info < (3, 8), reason="Tests with snapshots need at least Python 3.8")
def test_get_zwave_products(mydevolo: Mydevolo, requests_mock: Mocker, snapshot: SnapshotAssertion) -> None:
    """Test getting zwave product information."""
    details = mydevolo.get_zwave_products("0x0060", "0x0001", "0x0002")
    assert details == snapshot

    requests_mock.get(ZWAVE_PRODUCTS_URL, status_code=HTTPStatus.NOT_FOUND)
    details = mydevolo.get_zwave_products("0x1060", "0x0001", "0x0002")
    assert details == snapshot


def test_maintenance(mydevolo: Mydevolo, requests_mock: Mocker) -> None:
    """Test maintenance mode state."""
    assert not mydevolo.maintenance()

    requests_mock.get(MAINTENANCE_URL, json={"state": "off"})
    assert mydevolo.maintenance()


@pytest.mark.skipif(sys.version_info < (3, 8), reason="Tests with snapshots need at least Python 3.8")
def test_get_uuid(mydevolo: Mydevolo, snapshot: SnapshotAssertion) -> None:
    """Test getting user's UUID."""
    uuid = mydevolo.uuid()
    assert uuid == snapshot
