import pytest

from ..mocks.mock_gateway import MockGateway


@pytest.fixture()
def gateway_instance(request):
    """ Create a completly mocked gateway instance. """
    return MockGateway(request.cls.gateway.get("id"))


@pytest.fixture()
def mock_gateway(mocker):
    """ Mock ony the constructor of a gateway instance. """
    mocker.patch("devolo_home_control_api.devices.gateway.Gateway.__init__", MockGateway.__init__)
