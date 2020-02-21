import pytest

from ..mocks.mock_response import (MockResponseConnectTimeout, MockResponseGet,
                                   MockResponseJsonError, MockResponsePost,
                                   MockResponseReadTimeout)


@pytest.fixture()
def mock_response_json(mocker):
    mocker.patch("requests.Session", return_value=MockResponseGet({"link": "test_link"}, status_code=200))


@pytest.fixture()
def mock_response_requests_ConnectTimeout(mocker):
    mocker.patch("requests.Session", return_value=MockResponseConnectTimeout({"link": "test_link"}, status_code=200))


@pytest.fixture()
def mock_response_json_JSONDecodeError(mocker):
    mocker.patch("requests.Session", return_value=MockResponseJsonError({"link": "test_link"}, status_code=200))


@pytest.fixture()
def mock_response_requests_invalid_id(mocker):
    mocker.patch("requests.Session", return_value=MockResponsePost({"link": "test_link"}, status_code=200))


@pytest.fixture()
def mock_response_requests_valid(mocker):
    mocker.patch("requests.Session", return_value=MockResponsePost({"link": "test_link"}, status_code=200))


@pytest.fixture()
def mock_response_valid(mocker):
    mocker.patch("requests.get", return_value=MockResponseGet({"response": "response"}, status_code=200))


@pytest.fixture()
def mock_response_wrong_credentials_error(mocker):
    mocker.patch("requests.get", return_value=MockResponseGet({"link": "test_link"}, status_code=403))


@pytest.fixture()
def mock_response_wrong_url_error(mocker):
    mocker.patch("requests.get", return_value=MockResponseGet({"link": "test_link"}, status_code=404))


@pytest.fixture()
def mock_response_requests_ReadTimeout(mocker):
    mocker.patch("requests.Session", return_value=MockResponseReadTimeout({"link": "test_link"}, status_code=200))


@pytest.fixture()
def mock_session_post(mocker, request):
    properties = {}
    properties["test_get_local_session_valid"] = {"link": "test_link"}
    mocker.patch("requests.Session.get", return_value=properties.get(request.node.name))
