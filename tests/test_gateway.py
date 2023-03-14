"""Test handling the gateway device."""
from unittest.mock import patch

import pytest

from devolo_home_control_api.devices.gateway import Gateway
from devolo_home_control_api.exceptions.gateway import GatewayOfflineError
from devolo_home_control_api.mydevolo import Mydevolo


@pytest.mark.usefixtures("mock_mydevolo__call")
class TestGateway:
    def test_offline_init(self, mydevolo: Mydevolo) -> None:
        """Test, that a gateway can be setup while being offline."""
        with patch("devolo_home_control_api.mydevolo.Mydevolo.get_full_url", side_effect=GatewayOfflineError):
            gateway = Gateway(self.gateway.get("id"), mydevolo_instance=mydevolo)
            assert not gateway.full_url

    def test_update_state_known(self, mydevolo: Mydevolo) -> None:
        """Test state change to knowingly being offline."""
        gateway = Gateway(self.gateway.get("id"), mydevolo_instance=mydevolo)
        gateway.update_state(False)
        assert not gateway.online
        assert not gateway.sync

    def test_update_state_offline(self, mydevolo: Mydevolo) -> None:
        """Test state change to offline because of an update."""
        gateway = Gateway(self.gateway.get("id"), mydevolo_instance=mydevolo)
        gateway._update_state(status="devolo.hc_gateway.status.offline", state="devolo.hc_gateway.state.update")
        assert not gateway.online
        assert not gateway.sync

    def test_update_state_unknown(self, mydevolo: Mydevolo) -> None:
        """Test setting the state to the state mydevolo knows."""
        gateway = Gateway(self.gateway.get("id"), mydevolo_instance=mydevolo)
        gateway.online = False
        gateway.sync = False
        gateway.update_state()
        assert gateway.online
        assert gateway.sync
