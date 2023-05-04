"""Test interacting with the websocket."""
import logging
from unittest.mock import patch

import pytest
import requests
from requests_mock import Mocker

from devolo_home_control_api.exceptions import GatewayOfflineError
from devolo_home_control_api.homecontrol import HomeControl
from devolo_home_control_api.mydevolo import Mydevolo

from . import load_fixture
from .mocks import WEBSOCKET


def test_setup_websocket_broken(mydevolo: Mydevolo, gateway_id: str, gateway_ip: str, requests_mock: Mocker) -> None:
    """Test setup failure when websocket cannot be established."""
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
    with patch(
        "devolo_home_control_api.backend.mprm_websocket.time", side_effect=[1682620298.7491188, 1682620898.7491188]
    ), patch("devolo_home_control_api.backend.mprm_websocket.MprmWebsocket.websocket_connect"), pytest.raises(
        GatewayOfflineError
    ):
        HomeControl(gateway_id, mydevolo)


def test_websocket_breakdown(local_gateway: HomeControl) -> None:
    """Test reconnect behavior on websocket breakdown."""
    with patch(
        "devolo_home_control_api.backend.mprm_websocket.MprmWebsocket.websocket_connect",
        wraps=local_gateway.websocket_connect,
    ) as websocket_connect, patch(
        "devolo_home_control_api.backend.mprm.Mprm.get_local_session",
        side_effect=[GatewayOfflineError, requests.exceptions.ConnectTimeout, True],
    ) as get_local_session, patch(
        "devolo_home_control_api.backend.mprm.Mprm.detect_gateway_in_lan",
    ) as detect_gateway_in_lan, patch(
        "devolo_home_control_api.backend.mprm_websocket.sleep",
    ):
        WEBSOCKET.error()
        assert get_local_session.call_count == 3
        websocket_connect.assert_called_once()
        detect_gateway_in_lan.assert_called_once()


@pytest.mark.usefixtures("local_gateway")
def test_websocket_closed(caplog: pytest.LogCaptureFixture) -> None:
    """Test reveiving a close message."""
    caplog.set_level(logging.INFO)
    WEBSOCKET.close()
    assert "Closed websocket connection." in caplog.messages


@pytest.mark.usefixtures("local_gateway")
def test_websocket_session_refresh() -> None:
    """Test refreshing the session from time to time."""
    with patch("devolo_home_control_api.backend.mprm_rest.MprmRest._post") as post:
        WEBSOCKET.recv_pong()
        post.assert_called_once_with(
            {
                "method": "FIM/invokeOperation",
                "params": ["devolo.UserPrefs.535512AB-165D-11E7-A4E2-000C29D76CCA", "resetSessionTimeout", []],
            }
        )
