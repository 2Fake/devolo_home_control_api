import pytest


@pytest.fixture()
def mock_publisher_dispatch(mocker):
    """ Mock dispatch function to keep tests independent from a real subscriber. """
    mocker.patch("devolo_home_control_api.publisher.publisher.Publisher.dispatch", return_value=None)
