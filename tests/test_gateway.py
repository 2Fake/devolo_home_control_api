import pytest
from devolo_home_control_api.devices.gateway import Gateway


@pytest.mark.usefixtures("mydevolo")
@pytest.mark.usefixtures("mock_mydevolo__call")
class TestGateway:
    def test_update_state_known(self, mydevolo):
        gateway = Gateway(self.gateway.get("id"), mydevolo_instance=mydevolo)
        gateway.update_state(False)

        assert not gateway.online
        assert not gateway.sync

    def test_update_state_offline(self, mydevolo):
        gateway = Gateway(self.gateway.get("id"), mydevolo_instance=mydevolo)
        gateway._update_state(status="devolo.hc_gateway.status.offline", state="devolo.hc_gateway.state.update")

        assert not gateway.online
        assert not gateway.sync

    def test_update_state_unknown(self, mydevolo):
        gateway = Gateway(self.gateway.get("id"), mydevolo_instance=mydevolo)
        gateway.online = False
        gateway.sync = False
        gateway.update_state()

        assert gateway.online
        assert gateway.sync
