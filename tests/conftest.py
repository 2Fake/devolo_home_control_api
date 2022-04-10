import json
import pathlib

import pytest

file = pathlib.Path(__file__).parent / "test_data.json"
with file.open("r") as fh:
    test_data = json.load(fh)

pytest_plugins = [
    "tests.fixtures.gateway",
    "tests.fixtures.homecontrol",
    "tests.fixtures.mprm",
    "tests.fixtures.mydevolo",
    "tests.fixtures.publisher",
    "tests.fixtures.requests",
    "tests.fixtures.socket",
    "tests.fixtures.updater",
]


@pytest.fixture(autouse=True)
def test_data_fixture(request):
    """Load test data."""
    request.cls.user = test_data["user"]
    request.cls.gateway = test_data["gateway"]
    request.cls.devices = test_data["devices"]
