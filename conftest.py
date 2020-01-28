import pytest
import logging
from devolo_home_control_api.mprm_rest import MprmRest
from tests.mock_gateway import Gateway

_logger = logging.getLogger()


@pytest.fixture()
def mock_gateway(mocker):
    mocker.patch('devolo_home_control_api.devices.gateway.Gateway.__init__', Gateway.__init__)
