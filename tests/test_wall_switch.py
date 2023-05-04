"""Test interacting with a wall switch."""
import json
import sys

import pytest
from requests_mock import Mocker
from syrupy.assertion import SnapshotAssertion

from devolo_home_control_api.homecontrol import HomeControl

from . import Subscriber, load_fixture
from .mocks import WEBSOCKET

ELEMENT_ID = "hdm:ZWave:CBC56091/7"
FIXTURE = load_fixture("homecontrol_remote_control")


@pytest.mark.skipif(sys.version_info < (3, 8), reason="Tests with snapshots need at least Python 3.8")
@pytest.mark.freeze_time("2023-04-28T08:00:00")
def test_getting_devices(local_gateway: HomeControl, snapshot: SnapshotAssertion) -> None:
    """Test getting remote control devices."""
    assert local_gateway.remote_control_devices == snapshot


def test_state_change(local_gateway: HomeControl, gateway_ip: str, requests_mock: Mocker) -> None:
    """Test state change of a wall switch."""
    response = FIXTURE["success"]
    requests_mock.post(f"http://{gateway_ip}/remote/json-rpc", json=response)
    subscriber = Subscriber(ELEMENT_ID)
    local_gateway.publisher.register(ELEMENT_ID, subscriber)
    wall_swtich = local_gateway.devices[ELEMENT_ID]

    button = wall_swtich.remote_control_property[f"devolo.RemoteControl:{ELEMENT_ID}"]
    key_pressed = button.key_pressed
    last_activity = button.last_activity
    WEBSOCKET.recv_packet(json.dumps(FIXTURE["button_event"]))
    assert key_pressed != button.key_pressed
    assert last_activity != button.last_activity
    assert subscriber.update.call_count == 1

    button = wall_swtich.remote_control_property[f"devolo.RemoteControl:{ELEMENT_ID}"]
    assert button.set(2)
    assert button.key_pressed == 2


def test_state_change_same_value(local_gateway: HomeControl, gateway_ip: str, requests_mock: Mocker) -> None:
    """Test state change of a wall switch using the same value."""
    response = FIXTURE["fail"]
    requests_mock.post(f"http://{gateway_ip}/remote/json-rpc", json=response)
    wall_swtich = local_gateway.devices[ELEMENT_ID]
    button = wall_swtich.remote_control_property[f"devolo.RemoteControl:{ELEMENT_ID}"]
    assert not button.set(2)


def test_type_change(local_gateway: HomeControl) -> None:
    """Test processing a type change."""
    subscriber = Subscriber(ELEMENT_ID)
    local_gateway.publisher.register(ELEMENT_ID, subscriber)
    wall_switch = local_gateway.devices[ELEMENT_ID]
    button = wall_switch.remote_control_property[f"devolo.RemoteControl:{ELEMENT_ID}"]
    switch_type = button.key_count
    WEBSOCKET.recv_packet(json.dumps(FIXTURE["count_change"]))
    assert switch_type != button.key_count
    assert subscriber.update.call_count == 1


def test_battery_report(local_gateway: HomeControl) -> None:
    """Test processing a battery report."""
    subscriber = Subscriber(ELEMENT_ID)
    local_gateway.publisher.register(ELEMENT_ID, subscriber)
    wall_switch = local_gateway.devices[ELEMENT_ID]
    battery_level = wall_switch.battery_level
    battery_low = wall_switch.battery_low
    WEBSOCKET.recv_packet(json.dumps(FIXTURE["battery_low"]))
    WEBSOCKET.recv_packet(json.dumps(FIXTURE["battery_level"]))
    assert battery_level != wall_switch.battery_level
    assert battery_low != wall_switch.battery_low
    assert subscriber.update.call_count == 2


def test_changing_general_device_settings(local_gateway: HomeControl) -> None:
    """Test changing general device settings."""
    wall_switch = local_gateway.devices[ELEMENT_ID]
    events_enabled = wall_switch.settings_property["general_device_settings"].events_enabled
    icon = wall_switch.settings_property["general_device_settings"].icon
    name = wall_switch.settings_property["general_device_settings"].name
    zone_id = wall_switch.settings_property["general_device_settings"].zone_id
    WEBSOCKET.recv_packet(json.dumps(FIXTURE["general_device_settings"]))
    assert events_enabled != wall_switch.settings_property["general_device_settings"].events_enabled
    assert icon != wall_switch.settings_property["general_device_settings"].icon
    assert name != wall_switch.settings_property["general_device_settings"].name
    assert zone_id != wall_switch.settings_property["general_device_settings"].zone_id


def test_changing_expert_settings(local_gateway: HomeControl) -> None:
    """Test changing expert settings."""
    wall_switch = local_gateway.devices[ELEMENT_ID]
    param_changed = wall_switch.settings_property["param_changed"].param_changed
    WEBSOCKET.recv_packet(json.dumps(FIXTURE["param_changed"]))
    assert param_changed != wall_switch.settings_property["param_changed"].param_changed


def test_getting_properties(local_gateway: HomeControl) -> None:
    """Test getting a property of the device."""
    wall_switch = local_gateway.devices[ELEMENT_ID]
    assert wall_switch.get_property("remote_control") == list(wall_switch.remote_control_property.values())


def test_getting_state(local_gateway: HomeControl) -> None:
    """Test getting the online state of the device."""
    wall_switch = local_gateway.devices[ELEMENT_ID]
    assert not wall_switch.is_online()
