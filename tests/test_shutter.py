"""Test interacting with a shutter."""
import json
import sys

import pytest
from requests_mock import Mocker
from syrupy.assertion import SnapshotAssertion

from devolo_home_control_api.homecontrol import HomeControl

from . import HOMECONTROL_URL, Subscriber, load_fixture
from .mocks import WEBSOCKET

ELEMENT_ID = "hdm:ZWave:CBC56091/9"
FIXTURE = load_fixture("homecontrol_blinds")


@pytest.mark.skipif(sys.version_info < (3, 8), reason="Tests with snapshots need at least Python 3.8")
def test_getting_devices(local_gateway: HomeControl, snapshot: SnapshotAssertion) -> None:
    """Test getting shutter devices."""
    assert local_gateway.blinds_devices == snapshot


def test_state_change(local_gateway: HomeControl) -> None:
    """Test state change of a shutter."""
    subscriber = Subscriber(ELEMENT_ID)
    local_gateway.publisher.register(ELEMENT_ID, subscriber)
    shutter = local_gateway.devices[ELEMENT_ID]
    state = shutter.multi_level_switch_property[f"devolo.Blinds:{ELEMENT_ID}"]
    value = state.value
    last_activity = state.last_activity
    WEBSOCKET.recv_packet(json.dumps(FIXTURE["movement_event"]))
    assert value != state.value
    assert last_activity != state.last_activity
    assert subscriber.update.call_count == 1


def test_changing_general_device_settings(local_gateway: HomeControl) -> None:
    """Test changing general device settings."""
    shutter = local_gateway.devices[ELEMENT_ID]
    events_enabled = shutter.settings_property["general_device_settings"].events_enabled
    icon = shutter.settings_property["general_device_settings"].icon
    name = shutter.settings_property["general_device_settings"].name
    zone_id = shutter.settings_property["general_device_settings"].zone_id
    WEBSOCKET.recv_packet(json.dumps(FIXTURE["general_device_settings"]))
    assert events_enabled != shutter.settings_property["general_device_settings"].events_enabled
    assert icon != shutter.settings_property["general_device_settings"].icon
    assert name != shutter.settings_property["general_device_settings"].name
    assert zone_id != shutter.settings_property["general_device_settings"].zone_id


def test_setting_general_device_settings(remote_gateway: HomeControl, requests_mock: Mocker) -> None:
    """Test setting general device settings."""
    response = FIXTURE["success"]
    requests_mock.post(f"{HOMECONTROL_URL}/remote/json-rpc", json=response)
    shutter = remote_gateway.devices[ELEMENT_ID]
    events_enabled = shutter.settings_property["general_device_settings"].events_enabled
    icon = shutter.settings_property["general_device_settings"].icon
    name = shutter.settings_property["general_device_settings"].name
    zone_id = shutter.settings_property["general_device_settings"].zone_id
    shutter.settings_property["general_device_settings"].set(zone_id="hz_2", icon="icon_17")
    assert shutter.settings_property["general_device_settings"].events_enabled == events_enabled
    assert icon != shutter.settings_property["general_device_settings"].icon
    assert name == shutter.settings_property["general_device_settings"].name
    assert zone_id != shutter.settings_property["general_device_settings"].zone_id


def test_setting_automatic_calibration(remote_gateway: HomeControl) -> None:
    """Test setting automatic calibration settings."""
    shutter = remote_gateway.devices[ELEMENT_ID]
    automatic_calibration = shutter.settings_property["automatic_calibration"].calibration_status
    WEBSOCKET.recv_packet(json.dumps(FIXTURE["automatic_calibration"]))
    assert automatic_calibration != shutter.settings_property["automatic_calibration"].calibration_status
    WEBSOCKET.recv_packet(json.dumps(FIXTURE["automatic_calibration_old"]))
    assert automatic_calibration == shutter.settings_property["automatic_calibration"].calibration_status


def test_setting_movement_direction(remote_gateway: HomeControl) -> None:
    """Test setting the movement direction."""
    shutter = remote_gateway.devices[ELEMENT_ID]
    inverted = shutter.settings_property["movement_direction"].inverted
    WEBSOCKET.recv_packet(json.dumps(FIXTURE["movement_direction"]))
    assert inverted != shutter.settings_property["movement_direction"].inverted


def test_getting_properties(local_gateway: HomeControl) -> None:
    """Test getting a property of the device."""
    shutter = local_gateway.devices[ELEMENT_ID]
    assert shutter.get_property("multi_level_switch") == list(shutter.multi_level_switch_property.values())


def test_getting_state(local_gateway: HomeControl) -> None:
    """Test getting the online state of the device."""
    shutter = local_gateway.devices[ELEMENT_ID]
    assert shutter.is_online()
