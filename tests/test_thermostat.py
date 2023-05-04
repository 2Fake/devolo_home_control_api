"""Test interacting with a room thermostat."""
import json
import sys

import pytest
from requests_mock import Mocker
from syrupy.assertion import SnapshotAssertion

from devolo_home_control_api.homecontrol import HomeControl

from . import Subscriber, load_fixture
from .mocks import WEBSOCKET

ELEMENT_ID = "hdm:ZWave:CBC56091/5"
FIXTURE = load_fixture("homecontrol_thermostat")


@pytest.mark.skipif(sys.version_info < (3, 8), reason="Tests with snapshots need at least Python 3.8")
@pytest.mark.freeze_time("2023-04-28T08:00:00")
def test_getting_devices(local_gateway: HomeControl, snapshot: SnapshotAssertion) -> None:
    """Test getting multi level sensor and switch devices."""
    assert local_gateway.multi_level_sensor_devices == snapshot
    assert local_gateway.multi_level_switch_devices == snapshot
    assert local_gateway.remote_control_devices == snapshot


def test_state_change(local_gateway: HomeControl, gateway_ip: str, requests_mock: Mocker) -> None:
    """Test state change of a room thermostat."""
    response = FIXTURE["success"]
    requests_mock.post(f"http://{gateway_ip}/remote/json-rpc", json=response)
    subscriber = Subscriber(ELEMENT_ID)
    local_gateway.publisher.register(ELEMENT_ID, subscriber)
    thermostat = local_gateway.devices[ELEMENT_ID]

    sensor = thermostat.multi_level_sensor_property[f"devolo.MultiLevelSensor:{ELEMENT_ID}"]
    value = sensor.value
    last_activity = sensor.last_activity
    WEBSOCKET.recv_packet(json.dumps(FIXTURE["sensor_event"]))
    assert value != sensor.value
    assert last_activity != sensor.last_activity
    assert subscriber.update.call_count == 1

    switch = thermostat.multi_level_switch_property[f"devolo.MultiLevelSwitch:{ELEMENT_ID}#ThermostatSetpoint(1)"]
    value = switch.value
    assert switch.set(value - 1)
    assert value - 1 == switch.value

    value = switch.value
    last_activity = switch.last_activity
    WEBSOCKET.recv_packet(json.dumps(FIXTURE["switch_event"]))
    assert value != switch.value
    assert last_activity != switch.last_activity
    assert subscriber.update.call_count == 2

    FIXTURE["success"]["id"] += 1
    button = thermostat.remote_control_property[f"devolo.RemoteControl:{ELEMENT_ID}"]
    assert button.set(1)
    assert button.key_pressed == 1

    WEBSOCKET.recv_packet(json.dumps(FIXTURE["button_event"]))
    assert button.key_pressed == 0
    assert last_activity != switch.last_activity
    assert subscriber.update.call_count == 3


def test_switching_same_state(local_gateway: HomeControl, gateway_ip: str, requests_mock: Mocker) -> None:
    """Test switching a room thermostat to the same state."""
    response = FIXTURE["fail"]
    requests_mock.post(f"http://{gateway_ip}/remote/json-rpc", json=response)
    subscriber = Subscriber(ELEMENT_ID)
    local_gateway.publisher.register(ELEMENT_ID, subscriber)

    thermostat = local_gateway.devices[ELEMENT_ID]
    switch = thermostat.multi_level_switch_property[f"devolo.MultiLevelSwitch:{ELEMENT_ID}#ThermostatSetpoint(1)"]
    value = switch.value
    assert not switch.set(value=value)
    assert value == switch.value


def test_invalid_set(local_gateway: HomeControl) -> None:
    """Test setting an invalid value."""
    thermostat = local_gateway.devices[ELEMENT_ID]
    switch = thermostat.multi_level_switch_property[f"devolo.MultiLevelSwitch:{ELEMENT_ID}#ThermostatSetpoint(1)"]
    with pytest.raises(ValueError):
        switch.set(switch.max + 1)

    button = thermostat.remote_control_property[f"devolo.RemoteControl:{ELEMENT_ID}"]
    with pytest.raises(ValueError):
        button.set(button.key_count + 1)


def test_pending_operation(local_gateway: HomeControl) -> None:
    """Test processing of a pending operation."""
    thermostat = local_gateway.devices[ELEMENT_ID]
    sensor = thermostat.multi_level_sensor_property[f"devolo.MultiLevelSensor:{ELEMENT_ID}"]
    value = sensor.value
    last_activity = sensor.last_activity
    WEBSOCKET.recv_packet(json.dumps(FIXTURE["pending_operation"]))
    assert value == sensor.value
    assert last_activity == sensor.last_activity
    assert thermostat.pending_operations


def test_battery_report(local_gateway: HomeControl) -> None:
    """Test processing a battery report."""
    subscriber = Subscriber(ELEMENT_ID)
    local_gateway.publisher.register(ELEMENT_ID, subscriber)
    thermostat = local_gateway.devices[ELEMENT_ID]
    battery_level = thermostat.battery_level
    battery_low = thermostat.battery_low
    WEBSOCKET.recv_packet(json.dumps(FIXTURE["battery_low"]))
    WEBSOCKET.recv_packet(json.dumps(FIXTURE["battery_level"]))
    assert battery_level != thermostat.battery_level
    assert battery_low != thermostat.battery_low
    assert subscriber.update.call_count == 2


def test_changing_general_device_settings(local_gateway: HomeControl) -> None:
    """Test changing general device settings."""
    thermostat = local_gateway.devices[ELEMENT_ID]
    events_enabled = thermostat.settings_property["general_device_settings"].events_enabled
    icon = thermostat.settings_property["general_device_settings"].icon
    name = thermostat.settings_property["general_device_settings"].name
    zone_id = thermostat.settings_property["general_device_settings"].zone_id
    WEBSOCKET.recv_packet(json.dumps(FIXTURE["general_device_settings"]))
    assert events_enabled != thermostat.settings_property["general_device_settings"].events_enabled
    assert icon != thermostat.settings_property["general_device_settings"].icon
    assert name != thermostat.settings_property["general_device_settings"].name
    assert zone_id != thermostat.settings_property["general_device_settings"].zone_id


def test_changing_expert_settings(local_gateway: HomeControl) -> None:
    """Test changing expert settings."""
    thermostat = local_gateway.devices[ELEMENT_ID]
    param_changed = thermostat.settings_property["param_changed"].param_changed
    WEBSOCKET.recv_packet(json.dumps(FIXTURE["param_changed"]))
    assert param_changed != thermostat.settings_property["param_changed"].param_changed


def test_getting_properties(local_gateway: HomeControl) -> None:
    """Test getting a property of the device."""
    thermostat = local_gateway.devices[ELEMENT_ID]
    assert thermostat.get_property("multi_level_sensor") == list(thermostat.multi_level_sensor_property.values())
    assert thermostat.get_property("multi_level_switch") == list(thermostat.multi_level_switch_property.values())
    assert thermostat.get_property("remote_control") == list(thermostat.remote_control_property.values())


def test_getting_state(local_gateway: HomeControl) -> None:
    """Test getting the online state of the device."""
    thermostat = local_gateway.devices[ELEMENT_ID]
    assert thermostat.is_online()
