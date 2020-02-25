import pytest

from ..mocks.mock_gateway import MockGateway


@pytest.fixture()
def mock_gateway(mocker):
    """ Mock the Gateway object with static test data. """
    mocker.patch("devolo_home_control_api.devices.gateway.Gateway.__init__", MockGateway.__init__)
