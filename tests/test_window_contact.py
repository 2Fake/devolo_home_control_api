"""Test interacting with a window contact."""
import json
import sys

import pytest
from syrupy.assertion import SnapshotAssertion

from devolo_home_control_api.homecontrol import HomeControl

from . import Subscriber, load_fixture
from .mocks import WEBSOCKET

ELEMENT_ID = "hdm:ZWave:CBC56091/3"
FIXTURE = load_fixture("homecontrol_binary_sensor")


@pytest.mark.skipif(sys.version_info < (3, 8), reason="Tests with snapshots need at least Python 3.8")
@pytest.mark.freeze_time("2023-04-28T08:00:00")
def test_getting_devices(local_gateway: HomeControl, snapshot: SnapshotAssertion) -> None:
    """Test getting binary sensor devices."""
    assert local_gateway.binary_sensor_devices == snapshot


def test_state_change(local_gateway: HomeControl) -> None:
    """Test state change of a binary sensor."""
    subscriber = Subscriber(ELEMENT_ID)
    local_gateway.publisher.register(ELEMENT_ID, subscriber)
    window_contact = local_gateway.devices[ELEMENT_ID]
    binary_sensor = window_contact.binary_sensor_property[f"devolo.BinarySensor:{ELEMENT_ID}"]
    state = binary_sensor.state
    last_activity = binary_sensor.last_activity
    WEBSOCKET.recv_packet(json.dumps(FIXTURE["sensor_event"]))
    assert state != binary_sensor.state
    assert last_activity != binary_sensor.last_activity
    assert subscriber.update.call_count == 1


def test_temperature_report(local_gateway: HomeControl) -> None:
    """Test processing a temperature report."""
    subscriber = Subscriber(ELEMENT_ID)
    local_gateway.publisher.register(ELEMENT_ID, subscriber)
    window_contact = local_gateway.devices[ELEMENT_ID]
    temperature_sensor = window_contact.multi_level_sensor_property[
        f"devolo.MultiLevelSensor:{ELEMENT_ID}#MultilevelSensor(1)"
    ]
    value = temperature_sensor.value
    last_activity = temperature_sensor.last_activity
    WEBSOCKET.recv_packet(json.dumps(FIXTURE["temperature_event"]))
    assert value != temperature_sensor.value
    assert last_activity != temperature_sensor.last_activity
    assert subscriber.update.call_count == 1


def test_battery_report(local_gateway: HomeControl) -> None:
    """Test processing a battery report."""
    subscriber = Subscriber(ELEMENT_ID)
    local_gateway.publisher.register(ELEMENT_ID, subscriber)
    window_contact = local_gateway.devices[ELEMENT_ID]
    battery_level = window_contact.battery_level
    battery_low = window_contact.battery_low
    WEBSOCKET.recv_packet(json.dumps(FIXTURE["battery_low"]))
    WEBSOCKET.recv_packet(json.dumps(FIXTURE["battery_level"]))
    assert battery_level != window_contact.battery_level
    assert battery_low != window_contact.battery_low
    assert subscriber.update.call_count == 2


def test_changing_general_device_settings(local_gateway: HomeControl) -> None:
    """Test changing general device settings."""
    window_contact = local_gateway.devices[ELEMENT_ID]
    events_enabled = window_contact.settings_property["general_device_settings"].events_enabled
    icon = window_contact.settings_property["general_device_settings"].icon
    name = window_contact.settings_property["general_device_settings"].name
    zone_id = window_contact.settings_property["general_device_settings"].zone_id
    WEBSOCKET.recv_packet(json.dumps(FIXTURE["general_device_settings"]))
    assert events_enabled != window_contact.settings_property["general_device_settings"].events_enabled
    assert icon != window_contact.settings_property["general_device_settings"].icon
    assert name != window_contact.settings_property["general_device_settings"].name
    assert zone_id != window_contact.settings_property["general_device_settings"].zone_id


def test_changing_led_settings(local_gateway: HomeControl) -> None:
    """Test changing led settings."""
    window_contact = local_gateway.devices[ELEMENT_ID]
    WEBSOCKET.recv_packet(json.dumps(FIXTURE["led"]))
    assert not window_contact.settings_property["led"].led_setting


def test_temperature_report_setting(local_gateway: HomeControl) -> None:
    """Test processing the temperature report setting."""
    window_contact = local_gateway.devices[ELEMENT_ID]
    WEBSOCKET.recv_packet(json.dumps(FIXTURE["temperature_report"]))
    assert not window_contact.settings_property["temperature_report"].temp_report


def test_changing_expert_settings(local_gateway: HomeControl) -> None:
    """Test changing expert settings."""
    window_contact = local_gateway.devices[ELEMENT_ID]
    param_changed = window_contact.settings_property["param_changed"].param_changed
    WEBSOCKET.recv_packet(json.dumps(FIXTURE["param_changed"]))
    assert param_changed != window_contact.settings_property["param_changed"].param_changed


def test_getting_properties(local_gateway: HomeControl) -> None:
    """Test getting a property of the device."""
    window_contact = local_gateway.devices[ELEMENT_ID]
    assert window_contact.get_property("binary_sensor") == list(window_contact.binary_sensor_property.values())
    assert window_contact.get_property("multi_level_sensor") == list(window_contact.multi_level_sensor_property.values())


def test_getting_state(local_gateway: HomeControl) -> None:
    """Test getting the online state of the device."""
    window_contact = local_gateway.devices[ELEMENT_ID]
    assert window_contact.is_online()
