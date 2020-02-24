import pytest

from devolo_home_control_api.mydevolo import Mydevolo, WrongUrlError

from ..mocks.mock_mydevolo import MockMydevolo


@pytest.fixture()
def mydevolo(request):
    mydevolo = Mydevolo()
    mydevolo._uuid = request.cls.user.get("uuid")
    yield mydevolo
    Mydevolo.del_instance()


@pytest.fixture()
def mock_mydevolo_full_url(mocker):
    mocker.patch("devolo_home_control_api.mydevolo.Mydevolo.get_full_url", side_effect=MockMydevolo.get_full_url)


@pytest.fixture()
def mock_mydevolo__call(mocker, request):
    mock_mydevolo = MockMydevolo(request)
    mocker.patch("devolo_home_control_api.mydevolo.Mydevolo._call", side_effect=mock_mydevolo._call)
    del mock_mydevolo


@pytest.fixture()
def mock_mydevolo__call_raise_WrongUrlError(mocker):
    mocker.patch("devolo_home_control_api.mydevolo.Mydevolo._call", side_effect=WrongUrlError)


@pytest.fixture()
def mock_get_zwave_products(mocker):
    mocker.patch("devolo_home_control_api.mydevolo.Mydevolo.get_zwave_products", return_value={})
