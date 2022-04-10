import pytest

from ..mocks.mock_response import (
    MockResponseConnectTimeout,
    MockResponseGet,
    MockResponseJsonError,
    MockResponsePost,
    MockResponseReadTimeout,
    MockResponseServiceUnavailable,
)


@pytest.fixture()
def mock_response_gateway_offline(mocker):
    """Mock requests get method with service_unavailable status_code."""
    mocker.patch("requests.get", return_value=MockResponseServiceUnavailable({"link": "test_link"}, status_code=503))


@pytest.fixture()
def mock_response_json(mocker):
    """Mock requests.Session get method with success status_code."""
    mocker.patch("requests.Session", return_value=MockResponseGet({"link": "test_link"}, status_code=200))


@pytest.fixture()
def mock_response_requests_ConnectTimeout(mocker):
    """Mock requests.Session with ConnectTimeout exception."""
    mocker.patch("requests.Session", return_value=MockResponseConnectTimeout({"link": "test_link"}, status_code=200))


@pytest.fixture()
def mock_response_json_JSONDecodeError(mocker):
    """Mock requests.Session with JSONDecodeError exception."""
    mocker.patch("requests.Session", return_value=MockResponseJsonError({"link": "test_link"}, status_code=200))


@pytest.fixture()
def mock_response_requests_invalid_id(mocker):
    """Mock requests.Session with JSONDecodeError exception."""
    mocker.patch("requests.Session", return_value=MockResponsePost({"link": "test_link"}, status_code=200))


@pytest.fixture()
def mock_response_requests_valid(mocker):
    """Mock requests.Session post method with success status_code."""
    mocker.patch("requests.Session", return_value=MockResponsePost({"link": "test_link"}, status_code=200))


@pytest.fixture()
def mock_response_valid(mocker):
    """Mock requests get method with success status_code."""
    mocker.patch("requests.get", return_value=MockResponseGet({"response": "response"}, status_code=200))


@pytest.fixture()
def mock_response_wrong_credentials_error(mocker):
    """Mock requests get method with forbidden status_code."""
    mocker.patch("requests.get", return_value=MockResponseGet({"link": "test_link"}, status_code=403))


@pytest.fixture()
def mock_response_wrong_url_error(mocker):
    """Mock requests get method with notfound status_code."""
    mocker.patch("requests.get", return_value=MockResponseGet({"link": "test_link"}, status_code=404))


@pytest.fixture()
def mock_response_requests_ReadTimeout(mocker):
    """Mock requests.Session with ReadTimeout exception."""
    mocker.patch("requests.Session", return_value=MockResponseReadTimeout({"link": "test_link"}, status_code=200))


@pytest.fixture()
def mock_session_get(mocker, request):
    """Mock requests.Session get method with test data."""
    properties = {
        "test_get_local_session_valid": {"link": "test_link"},
        "test__on_pong": {"link": "test_link"},
    }
    mocker.patch("requests.Session", return_value=MockResponseGet(properties.get(request.node.name), status_code=200))


@pytest.fixture()
def mock_session_get_nok(mocker):
    mocker.patch("requests.Session", return_value=MockResponseServiceUnavailable({}, status_code=500))
