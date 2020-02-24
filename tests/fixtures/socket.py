import pytest


@pytest.fixture()
def mock_socket_inet_ntoa(mocker, request):
    mocker.patch("socket.inet_ntoa", return_value=request.cls.gateway.get("local_ip"))
