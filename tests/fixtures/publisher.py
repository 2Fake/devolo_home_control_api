import pytest


@pytest.fixture()
def mock_publisher_add_event(mocker):
    """Mock add event function to keep tests independent from a real event."""
    mocker.patch("devolo_home_control_api.publisher.publisher.Publisher.add_event", return_value=None)


@pytest.fixture()
def mock_publisher_delete_event(mocker):
    """Mock delete event function to keep tests independent from a real event."""
    mocker.patch("devolo_home_control_api.publisher.publisher.Publisher.delete_event", return_value=None)


@pytest.fixture()
def mock_publisher_dispatch(mocker):
    """Mock dispatch function to keep tests independent from a real subscriber."""
    mocker.patch("devolo_home_control_api.publisher.publisher.Publisher.dispatch", return_value=None)
