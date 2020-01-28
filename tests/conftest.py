import pytest
import logging
from devolo_home_control_api.mprm_rest import MprmRest
from devolo_home_control_api.mydevolo import Mydevolo
from tests.mock_gateway import Gateway

_logger = logging.getLogger()

_uuid = "535512AB-165D-11E7-A4E2-000C29D76CCA"
_gateway = "1409301750000598"


@pytest.fixture()
def mock_gateway(mocker):
    mocker.patch('devolo_home_control_api.devices.gateway.Gateway.__init__', Gateway.__init__)


@pytest.fixture()
def mock_inspect_devices(mocker):
    def mock_inspect_devices(self):
        pass
    mocker.patch('devolo_home_control_api.mprm_rest.MprmRest._inspect_devices', mock_inspect_devices)


@pytest.fixture()
def mock_mydevolo__call_uuid(mocker):
    def _call_mock(url):
        return {"uuid": _uuid}

    mocker.patch("devolo_home_control_api.mydevolo.Mydevolo._call", side_effect=_call_mock)
    Mydevolo.del_instance()


@pytest.fixture()
def mock_mydevolo__call_gateway_ids(mocker):
    def _call_mock(url):
        return {"items": [{"gatewayId": _gateway}]}

    mocker.patch("devolo_home_control_api.mydevolo.Mydevolo._call", side_effect=_call_mock)
    Mydevolo.del_instance()


@pytest.fixture()
def mock_mydevolo__call_gateway_ids_empty(mocker):
    def _call_mock(url):
        return {"items": []}

    mocker.patch("devolo_home_control_api.mydevolo.Mydevolo._call", side_effect=_call_mock)
    Mydevolo.del_instance()


@pytest.fixture()
def mock_mydevolo__call_get_gateways(mocker):
    def _call_mock(url):
        return {"gatewayId": _gateway}

    mocker.patch("devolo_home_control_api.mydevolo.Mydevolo._call", side_effect=_call_mock)
    Mydevolo.del_instance()


@pytest.fixture()
def mock_mydevolo__call_get_full_url(mocker):
    def _call_mock(url):
        return {"url": "https://homecontrol.mydevolo.com/dhp/portal/fullLogin/?token=1410000000002_1:ec73a059f398fa8b&X-MPRM-LB=1410000000002_1"}

    mocker.patch("devolo_home_control_api.mydevolo.Mydevolo._call", side_effect=_call_mock)
    Mydevolo.del_instance()