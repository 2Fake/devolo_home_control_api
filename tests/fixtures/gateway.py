import pytest

from ..mocks.mock_gateway import MockGateway


@pytest.fixture()
def mock_gateway(mocker):
    mocker.patch("devolo_home_control_api.devices.gateway.Gateway.__init__", MockGateway.__init__)
