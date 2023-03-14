"""Fixtures used for mydevolo testing."""
from typing import Generator
from unittest.mock import patch

import pytest
from pytest_mock import MockerFixture

from devolo_home_control_api.mydevolo import Mydevolo, WrongCredentialsError, WrongUrlError

from ..mocks.mock_mydevolo import MockMydevolo


@pytest.fixture()
def mydevolo(request: pytest.FixtureRequest) -> Generator[Mydevolo, None, None]:
    """Create real mydevolo object with static test data."""
    with patch("devolo_home_control_api.mydevolo.Mydevolo.uuid", return_value=request.cls.user.get("uuid")):
        yield Mydevolo()


@pytest.fixture()
def mock_mydevolo__call(mocker: MockerFixture, request: pytest.FixtureRequest) -> None:
    """Mock calls to the mydevolo API."""
    mock_mydevolo = MockMydevolo(request)
    mocker.patch("devolo_home_control_api.mydevolo.Mydevolo._call", side_effect=mock_mydevolo._call)


@pytest.fixture()
def mock_mydevolo__call_raise_WrongUrlError(mocker: MockerFixture) -> None:
    """Respond with WrongUrlError on calls to the mydevolo API."""
    mocker.patch("devolo_home_control_api.mydevolo.Mydevolo._call", side_effect=WrongUrlError)


@pytest.fixture()
def mock_mydevolo_uuid_raise_WrongCredentialsError(mydevolo: Mydevolo) -> Generator[Mydevolo, None, None]:
    """Respond with WrongCredentialsError on calls to the mydevolo API."""
    with patch("devolo_home_control_api.mydevolo.Mydevolo.uuid", side_effect=WrongCredentialsError):
        yield mydevolo


@pytest.fixture()
def mock_get_zwave_products(mocker: MockerFixture) -> None:
    """Mock Z-Wave product information call to speed up tests."""
    mocker.patch("devolo_home_control_api.mydevolo.Mydevolo.get_zwave_products", return_value={})
