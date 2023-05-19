"""Tests for devolo_home_control_api."""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any
from unittest.mock import Mock

from syrupy.extensions.amber import AmberSnapshotExtension
from syrupy.location import PyTestLocation

MYDEVOLO_URL = "https://www.mydevolo.com"
HOMECONTROL_URL = "https://homecontrol.mydevolo.com"
GATEWAY_DETAILS_URL = re.compile(
    MYDEVOLO_URL + r"/v1/users/[0-9A-F]{8}\b-[0-9A-F]{4}\b-[0-9A-F]{4}\b-[0-9A-F]{4}\b-[0-9A-F]{12}/hc/gateways/\d{16}"
)
GATEWAY_FULLURL = re.compile(
    MYDEVOLO_URL + r"/v1/users/[0-9A-F]{8}\b-[0-9A-F]{4}\b-[0-9A-F]{4}\b-[0-9A-F]{4}\b-[0-9A-F]{12}/hc/gateways/\d{16}/fullURL"
)
GATEWAY_LOCATION_URL = re.compile(
    MYDEVOLO_URL
    + r"/v1/users/[0-9A-F]{8}\b-[0-9A-F]{4}\b-[0-9A-F]{4}\b-[0-9A-F]{4}\b-[0-9A-F]{12}/hc/gateways/\d{16}/location"
)
GATEWAY_STATUS_URL = re.compile(
    MYDEVOLO_URL + r"/v1/users/[0-9A-F]{8}\b-[0-9A-F]{4}\b-[0-9A-F]{4}\b-[0-9A-F]{4}\b-[0-9A-F]{12}/hc/gateways/status"
)
MAINTENANCE_URL = f"{MYDEVOLO_URL}/v1/hc/maintenance"
STANDARD_TIMEZONE_URL = re.compile(
    MYDEVOLO_URL + r"/v1/users/[0-9A-F]{8}\b-[0-9A-F]{4}\b-[0-9A-F]{4}\b-[0-9A-F]{4}\b-[0-9A-F]{12}/standardTimezone"
)
UUID_URL = f"{MYDEVOLO_URL}/v1/users/uuid"
ZWAVE_PRODUCTS_URL = re.compile(MYDEVOLO_URL + r"/v1/zwave/products/0x[0-9a-f]{4}/0x[0-9a-f]{4}/0x[0-9a-f]{4}")


def get_fixtures_path() -> Path:
    """Get path of the fixtures."""
    return Path(__file__).parent.joinpath("fixtures")


@lru_cache()
def load_fixture(name: str) -> dict[str, Any]:
    """Load a fixture."""
    fixture_path = get_fixtures_path().joinpath(f"{name}.json")
    with Path.open(fixture_path, encoding="UTF-8") as fixture:
        return json.loads(fixture.read())


class Subscriber:
    """Subscriber used during testing."""

    def __init__(self, name: str) -> None:
        """Initialize the subscriber."""
        self.name = name
        self.update = Mock()


class DifferentDirectoryExtension(AmberSnapshotExtension):
    """Extention for Syrupy to change the directory in which snapshots are stored."""

    @classmethod
    def dirname(cls, *, test_location: PyTestLocation) -> str:
        """Store snapshots in `snapshots`rather than `__snapshots__`."""
        return str(Path(test_location.filepath).parent.joinpath("snapshots"))
