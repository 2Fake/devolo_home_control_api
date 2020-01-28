import pytest
import logging

_logger = logging.getLogger()

@pytest.fixture()
def mock_gateway(mocker):
    return mocker.patch('devolo_home_control_api.devices.gateway.Gateway', autospec=True)