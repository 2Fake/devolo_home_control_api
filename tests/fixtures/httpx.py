import pytest

from ..mocks.mock_response import (MockResponseConnectTimeout,
                                   MockResponseGet,
                                   MockResponseJsonError,
                                   MockResponsePost,
                                   MockResponseReadTimeout,
                                   MockResponseServiceUnavailable)


@pytest.fixture()
def mock_response_gateway_offline(mocker):
    """ Mock httpx get method with service_unavailable status_code. """
    mocker.patch("httpx.get",
                 return_value=MockResponseServiceUnavailable({"link": "test_link"},
                                                             status_code=503))


@pytest.fixture()
def mock_response_json(mocker):
    """ Mock httpx.Client get method with success status_code. """
    mocker.patch("httpx.Client",
                 return_value=MockResponseGet({"link": "test_link"},
                                              status_code=200))


@pytest.fixture()
def mock_response_ConnectTimeout(mocker):
    """ Mock httpx.Client with ConnectTimeout exception. """
    mocker.patch("httpx.Client",
                 return_value=MockResponseConnectTimeout({"link": "test_link"},
                                                         status_code=200))


@pytest.fixture()
def mock_response_json_JSONDecodeError(mocker):
    """ Mock httpx.Client with JSONDecodeError exception. """
    mocker.patch("httpx.Client",
                 return_value=MockResponseJsonError({"link": "test_link"},
                                                    status_code=200))


@pytest.fixture()
def mock_response_invalid_id(mocker):
    """ Mock httpx.Client with JSONDecodeError exception. """
    mocker.patch("httpx.Client",
                 return_value=MockResponsePost({"link": "test_link"},
                                               status_code=200))


@pytest.fixture()
def mock_response_post_valid(mocker):
    """ Mock httpx.Client post method with success status_code. """
    mocker.patch("httpx.Client",
                 return_value=MockResponsePost({"link": "test_link"},
                                               status_code=200))


@pytest.fixture()
def mock_response_get_valid(mocker):
    """ Mock httpx get method with success status_code. """
    mocker.patch("httpx.get",
                 return_value=MockResponseGet({"response": "response"},
                                              status_code=200))


@pytest.fixture()
def mock_response_wrong_credentials_error(mocker):
    """ Mock httpx get method with forbidden status_code. """
    mocker.patch("httpx.get",
                 return_value=MockResponseGet({"link": "test_link"},
                                              status_code=403))


@pytest.fixture()
def mock_response_wrong_url_error(mocker):
    """ Mock httpx get method with notfound status_code. """
    mocker.patch("httpx.get",
                 return_value=MockResponseGet({"link": "test_link"},
                                              status_code=404))


@pytest.fixture()
def mock_response_ReadTimeout(mocker):
    """ Mock httpx.Client with ReadTimeout exception. """
    mocker.patch("httpx.Client",
                 return_value=MockResponseReadTimeout({"link": "test_link"},
                                                      status_code=200))


@pytest.fixture()
def mock_session_get(mocker, request):
    """ Mock httpx.Client get method with test data. """
    properties = {
        'test_get_local_session_valid': {
            'link': 'test_link'
        },
        'test__on_pong': {
            'link': 'test_link'
        },
    }
    mocker.patch("httpx.Client.get", return_value=properties.get(request.node.name))
