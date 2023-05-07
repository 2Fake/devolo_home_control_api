"""Test interacting with a metering plug."""
import json
import sys
from datetime import datetime, timezone

import pytest
from dateutil import tz
from requests_mock import Mocker
from syrupy.assertion import SnapshotAssertion

from devolo_home_control_api.exceptions import SwitchingProtected
from devolo_home_control_api.homecontrol import HomeControl

from . import HOMECONTROL_URL, Subscriber, load_fixture
from .mocks import WEBSOCKET

ELEMENT_ID = "hdm:ZWave:CBC56091/2"
FIXTURE = load_fixture("homecontrol_binary_switch")
TIMEZONE = tz.gettz()


@pytest.mark.skipif(sys.version_info < (3, 8), reason="Tests with snapshots need at least Python 3.8")
def test_getting_devices(local_gateway: HomeControl, snapshot: SnapshotAssertion) -> None:
    """Test getting binary switch devices."""
    assert local_gateway.binary_switch_devices == snapshot


def test_switching(local_gateway: HomeControl, gateway_ip: str, requests_mock: Mocker) -> None:
    """Test switching a binary switch."""
    response = FIXTURE["success"]
    requests_mock.post(f"http://{gateway_ip}/remote/json-rpc", json=response)
    subscriber = Subscriber(ELEMENT_ID)
    local_gateway.publisher.register(ELEMENT_ID, subscriber)
    metering_plug = local_gateway.devices[ELEMENT_ID]

    binary_switch = metering_plug.binary_switch_property[f"devolo.BinarySwitch:{ELEMENT_ID}"]
    state = binary_switch.state
    last_activity = binary_switch.last_activity
    assert binary_switch.set(state=not state)
    assert state != binary_switch.state
    assert last_activity != binary_switch.last_activity

    state = binary_switch.state
    last_activity = binary_switch.last_activity
    WEBSOCKET.recv_packet(json.dumps(FIXTURE["switch_event"]))
    assert state != binary_switch.state
    assert last_activity != binary_switch.last_activity
    assert subscriber.update.call_count == 1


def test_switching_same_state(local_gateway: HomeControl, gateway_ip: str, requests_mock: Mocker) -> None:
    """Test switching a binary switch to the same state."""
    response = FIXTURE["fail"]
    requests_mock.post(f"http://{gateway_ip}/remote/json-rpc", json=response)
    subscriber = Subscriber(ELEMENT_ID)
    local_gateway.publisher.register(ELEMENT_ID, subscriber)

    metering_plug = local_gateway.devices[ELEMENT_ID]
    binary_switch = metering_plug.binary_switch_property[f"devolo.BinarySwitch:{ELEMENT_ID}"]
    state = binary_switch.state
    assert not binary_switch.set(state=not state)
    assert state == binary_switch.state


def test_switching_protected(local_gateway: HomeControl) -> None:
    """Test switching a binary switch that is protected."""
    metering_plug = local_gateway.devices[ELEMENT_ID]
    binary_switch = metering_plug.binary_switch_property[f"devolo.BinarySwitch:{ELEMENT_ID}"]
    binary_switch.enabled = False
    with pytest.raises(SwitchingProtected):
        binary_switch.set(state=True)


def test_consumption(local_gateway: HomeControl) -> None:
    """Test consumption a mitering plug."""
    element = next(
        item
        for item in load_fixture("homecontrol_device_details")["result"]["items"]
        if item["UID"] == f"devolo.Meter:{ELEMENT_ID}"
    )
    subscriber = Subscriber(ELEMENT_ID)
    local_gateway.publisher.register(ELEMENT_ID, subscriber)

    metering_plug = local_gateway.devices[ELEMENT_ID]
    consumption = metering_plug.consumption_property[f"devolo.Meter:{ELEMENT_ID}"]
    assert consumption.current == element["properties"]["currentValue"]
    assert consumption.total == element["properties"]["totalValue"]
    assert consumption.total_since == datetime.fromtimestamp(
        element["properties"]["sinceTime"] / 1000, tz=timezone.utc
    ).replace(tzinfo=tz.gettz("Europe/Berlin"))

    last_activity = consumption.last_activity
    WEBSOCKET.recv_packet(json.dumps(FIXTURE["current_event"]))
    assert consumption.current == FIXTURE["current_event"]["properties"]["property.value.new"]
    assert last_activity != consumption.last_activity
    assert subscriber.update.call_count == 1

    last_activity = consumption.last_activity
    WEBSOCKET.recv_packet(json.dumps(FIXTURE["total_event"]))
    assert consumption.total == FIXTURE["total_event"]["properties"]["property.value.new"]
    assert last_activity != consumption.last_activity
    assert subscriber.update.call_count == 2

    WEBSOCKET.recv_packet(json.dumps(FIXTURE["total_since"]))
    assert consumption.total_since == datetime.fromtimestamp(
        FIXTURE["total_since"]["properties"]["property.value.new"] / 1000, tz=timezone.utc
    ).replace(tzinfo=tz.gettz("Europe/Berlin"))
    assert subscriber.update.call_count == 3


def test_voltage(local_gateway: HomeControl) -> None:
    """Test voltage sensor of a metering plug."""
    element = next(
        item
        for item in load_fixture("homecontrol_device_details")["result"]["items"]
        if item["UID"] == f"devolo.VoltageMultiLevelSensor:{ELEMENT_ID}"
    )
    subscriber = Subscriber(ELEMENT_ID)
    local_gateway.publisher.register(ELEMENT_ID, subscriber)

    metering_plug = local_gateway.devices[ELEMENT_ID]
    voltage = metering_plug.multi_level_sensor_property[f"devolo.VoltageMultiLevelSensor:{ELEMENT_ID}"]
    assert voltage.value == element["properties"]["value"]

    last_activity = voltage.last_activity
    WEBSOCKET.recv_packet(json.dumps(FIXTURE["voltage_event"]))
    assert voltage.value == FIXTURE["voltage_event"]["properties"]["property.value.new"]
    assert last_activity != voltage.last_activity


def test_changing_general_device_settings(local_gateway: HomeControl) -> None:
    """Test changing general device settings."""
    metering_plug = local_gateway.devices[ELEMENT_ID]
    events_enabled = metering_plug.settings_property["general_device_settings"].events_enabled
    icon = metering_plug.settings_property["general_device_settings"].icon
    name = metering_plug.settings_property["general_device_settings"].name
    zone_id = metering_plug.settings_property["general_device_settings"].zone_id
    WEBSOCKET.recv_packet(json.dumps(FIXTURE["general_device_settings"]))
    assert events_enabled != metering_plug.settings_property["general_device_settings"].events_enabled
    assert icon != metering_plug.settings_property["general_device_settings"].icon
    assert name != metering_plug.settings_property["general_device_settings"].name
    assert zone_id != metering_plug.settings_property["general_device_settings"].zone_id


def test_setting_general_device_settings(remote_gateway: HomeControl, requests_mock: Mocker) -> None:
    """Test setting general device settings."""
    response = FIXTURE["success"]
    requests_mock.post(f"{HOMECONTROL_URL}/remote/json-rpc", json=response)
    metering_plug = remote_gateway.devices[ELEMENT_ID]
    events_enabled = metering_plug.settings_property["general_device_settings"].events_enabled
    icon = metering_plug.settings_property["general_device_settings"].icon
    name = metering_plug.settings_property["general_device_settings"].name
    zone_id = metering_plug.settings_property["general_device_settings"].zone_id
    assert metering_plug.settings_property["general_device_settings"].set(icon="icon_15")
    assert metering_plug.settings_property["general_device_settings"].events_enabled == events_enabled
    assert icon != metering_plug.settings_property["general_device_settings"].icon
    assert name == metering_plug.settings_property["general_device_settings"].name
    assert zone_id == metering_plug.settings_property["general_device_settings"].zone_id


def test_setting_general_device_settings_same_state(remote_gateway: HomeControl, requests_mock: Mocker) -> None:
    """Test setting general device settings to the same state."""
    response = FIXTURE["fail"]
    requests_mock.post(f"{HOMECONTROL_URL}/remote/json-rpc", json=response)
    metering_plug = remote_gateway.devices[ELEMENT_ID]
    icon = metering_plug.settings_property["general_device_settings"].icon
    assert not metering_plug.settings_property["general_device_settings"].set(icon="icon_15")
    assert icon == metering_plug.settings_property["general_device_settings"].icon


def test_changing_led_settings(local_gateway: HomeControl) -> None:
    """Test changing led settings."""
    metering_plug = local_gateway.devices[ELEMENT_ID]
    WEBSOCKET.recv_packet(json.dumps(FIXTURE["led"]))
    assert not metering_plug.settings_property["led"].led_setting


def test_setting_led(remote_gateway: HomeControl, requests_mock: Mocker) -> None:
    """Test setting led settings."""
    response = FIXTURE["success"]
    requests_mock.post(f"{HOMECONTROL_URL}/remote/json-rpc", json=response)
    metering_plug = remote_gateway.devices[ELEMENT_ID]
    led_setting = metering_plug.settings_property["led"].led_setting
    assert metering_plug.settings_property["led"].set(led_setting=False)
    assert metering_plug.settings_property["led"].led_setting != led_setting


def test_setting_led_same_state(remote_gateway: HomeControl, requests_mock: Mocker) -> None:
    """Test setting led settings to the same state."""
    response = FIXTURE["fail"]
    requests_mock.post(f"{HOMECONTROL_URL}/remote/json-rpc", json=response)
    metering_plug = remote_gateway.devices[ELEMENT_ID]
    led_setting = metering_plug.settings_property["led"].led_setting
    assert not metering_plug.settings_property["led"].set(led_setting=True)
    assert metering_plug.settings_property["led"].led_setting == led_setting


def test_changing_protection_mode(local_gateway: HomeControl) -> None:
    """Test changing the protection mode."""
    metering_plug = local_gateway.devices[ELEMENT_ID]
    binary_switch = metering_plug.binary_switch_property[f"devolo.BinarySwitch:{ELEMENT_ID}"]
    WEBSOCKET.recv_packet(json.dumps(FIXTURE["protection"]))
    WEBSOCKET.recv_packet(json.dumps(FIXTURE["gui_enabled"]))
    assert not metering_plug.settings_property["protection"].remote_switching
    assert not binary_switch.enabled

    FIXTURE["protection"]["properties"]["property.name"] = "localSwitch"
    FIXTURE["protection"]["properties"]["com.prosyst.mbs.services.remote.event.sequence.number"] = 2
    metering_plug = local_gateway.devices[ELEMENT_ID]
    WEBSOCKET.recv_packet(json.dumps(FIXTURE["protection"]))
    assert not metering_plug.settings_property["protection"].local_switching


def test_protection_mode(remote_gateway: HomeControl, requests_mock: Mocker) -> None:
    """Test setting the protection mode."""
    response = FIXTURE["success"]
    requests_mock.post(f"{HOMECONTROL_URL}/remote/json-rpc", json=response)
    metering_plug = remote_gateway.devices[ELEMENT_ID]
    local_switching = metering_plug.settings_property["protection"].local_switching
    remote_switching = metering_plug.settings_property["protection"].remote_switching
    assert metering_plug.settings_property["protection"].set(local_switching=False)
    assert metering_plug.settings_property["protection"].local_switching != local_switching
    assert metering_plug.settings_property["protection"].remote_switching == remote_switching


def test_protection_mode_same_state(remote_gateway: HomeControl, requests_mock: Mocker) -> None:
    """Test setting the protection mode to the same state."""
    response = FIXTURE["fail"]
    requests_mock.post(f"{HOMECONTROL_URL}/remote/json-rpc", json=response)
    metering_plug = remote_gateway.devices[ELEMENT_ID]
    local_switching = metering_plug.settings_property["protection"].local_switching
    assert not metering_plug.settings_property["protection"].set(local_switching=False)
    assert metering_plug.settings_property["protection"].local_switching == local_switching


def test_changing_expert_settings(local_gateway: HomeControl) -> None:
    """Test changing expert settings."""
    metering_plug = local_gateway.devices[ELEMENT_ID]
    param_changed = metering_plug.settings_property["param_changed"].param_changed
    WEBSOCKET.recv_packet(json.dumps(FIXTURE["param_changed"]))
    assert param_changed != metering_plug.settings_property["param_changed"].param_changed


def test_changing_flash_mode_settings(local_gateway: HomeControl) -> None:
    """Test changing flash mode settings."""
    metering_plug = local_gateway.devices[ELEMENT_ID]
    WEBSOCKET.recv_packet(json.dumps(FIXTURE["flash_mode"]))
    assert metering_plug.settings_property["flash_mode"].value == 2


def test_getting_properties(local_gateway: HomeControl) -> None:
    """Test getting a property of the device."""
    metering_plug = local_gateway.devices[ELEMENT_ID]
    assert metering_plug.get_property("binary_switch") == list(metering_plug.binary_switch_property.values())
    assert metering_plug.get_property("consumption") == list(metering_plug.consumption_property.values())


def test_getting_state(local_gateway: HomeControl) -> None:
    """Test getting the online state of the device."""
    metering_plug = local_gateway.devices[ELEMENT_ID]
    assert metering_plug.is_online()
