import pytest

from devolo_home_control_api.devices.gateway import Gateway


@pytest.mark.usefixtures("mock_mydevolo__call")
class TestGateway:
    def test_update_state_known(self):
        gateway = Gateway(self.gateway.get("id"))
        gateway.update_state(False)

        assert not gateway.online
        assert not gateway.sync

    def test_update_state_unknow(self):
        gateway = Gateway(self.gateway.get("id"))
        gateway.online = False
        gateway.sync = False
        gateway.update_state()

        assert gateway.online
        assert gateway.sync
