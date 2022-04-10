import pytest


@pytest.fixture()
def mock_socket_inet_ntoa(mocker, request):
    """Mock socket's hostname to IP method to be independent from a real existing device."""
    mocker.patch("socket.inet_ntoa", return_value=request.cls.gateway.get("local_ip"))
