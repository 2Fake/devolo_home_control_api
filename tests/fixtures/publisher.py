import pytest


@pytest.fixture()
def mock_publisher_dispatch(mocker):
    mocker.patch("devolo_home_control_api.publisher.publisher.Publisher.dispatch", return_value=None)
