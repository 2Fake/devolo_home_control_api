import pytest


@pytest.fixture()
def mock_updater_binary_switch(mocker):
    """Mock processing an update for binary switch devices."""
    mocker.patch("devolo_home_control_api.publisher.updater.Updater._binary_switch", return_value=None)


@pytest.fixture()
def mock_updater_pending_operations(mocker):
    """Mock processing an update for a pending operation attribute."""
    mocker.patch("devolo_home_control_api.publisher.updater.Updater._pending_operations", return_value=None)
