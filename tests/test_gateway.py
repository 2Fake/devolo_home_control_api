import pytest

from devolo_home_control_api.devices.gateway import Gateway


@pytest.mark.usefixtures("mydevolo")
@pytest.mark.usefixtures("mock_mydevolo__call")
class TestGateway:
    def test_update_state_known(self):
        gateway = Gateway(self.gateway.get("id"))
        gateway.update_state(False)

        assert not gateway.online
        assert not gateway.sync

    def test_update_state_offline(self):
        gateway = Gateway(self.gateway.get("id"))
        gateway._update_state(status="devolo.hc_gateway.status.offline", state="devolo.hc_gateway.state.update")

        assert not gateway.online
        assert not gateway.sync

    def test_update_state_unknown(self):
        gateway = Gateway(self.gateway.get("id"))
        gateway.online = False
        gateway.sync = False
        gateway.update_state()

        assert gateway.online
        assert gateway.sync

    @pytest.mark.usefixtures("mock_mydevolo_full_url")
    def test_full_url(self):
        gateway = Gateway(self.gateway.get("id"))
        assert gateway.full_url == self.gateway.get("id")
