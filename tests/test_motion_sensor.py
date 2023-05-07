"""Test interacting with a window contact."""
import json

from requests_mock import Mocker

from devolo_home_control_api.homecontrol import HomeControl

from . import HOMECONTROL_URL, Subscriber, load_fixture
from .mocks import WEBSOCKET

ELEMENT_ID = "hdm:ZWave:CBC56091/8"
FIXTURE = load_fixture("homecontrol_motion_sensor")


def test_state_change(local_gateway: HomeControl) -> None:
    """Test state change of a binary sensor."""
    subscriber = Subscriber(ELEMENT_ID)
    local_gateway.publisher.register(ELEMENT_ID, subscriber)
    motion_sensor = local_gateway.devices[ELEMENT_ID]
    binary_sensor = motion_sensor.binary_sensor_property[f"devolo.BinarySensor:{ELEMENT_ID}"]
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
    motion_sensor = local_gateway.devices[ELEMENT_ID]
    temperature_sensor = motion_sensor.multi_level_sensor_property[f"devolo.MultiLevelSensor:{ELEMENT_ID}#MultilevelSensor(1)"]
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
    motion_sensor = local_gateway.devices[ELEMENT_ID]
    battery_level = motion_sensor.battery_level
    battery_low = motion_sensor.battery_low
    WEBSOCKET.recv_packet(json.dumps(FIXTURE["battery_low"]))
    WEBSOCKET.recv_packet(json.dumps(FIXTURE["battery_level"]))
    assert battery_level != motion_sensor.battery_level
    assert battery_low != motion_sensor.battery_low
    assert subscriber.update.call_count == 2


def test_changing_general_device_settings(local_gateway: HomeControl) -> None:
    """Test changing general device settings."""
    motion_sensor = local_gateway.devices[ELEMENT_ID]
    events_enabled = motion_sensor.settings_property["general_device_settings"].events_enabled
    icon = motion_sensor.settings_property["general_device_settings"].icon
    name = motion_sensor.settings_property["general_device_settings"].name
    zone_id = motion_sensor.settings_property["general_device_settings"].zone_id
    WEBSOCKET.recv_packet(json.dumps(FIXTURE["general_device_settings"]))
    assert events_enabled != motion_sensor.settings_property["general_device_settings"].events_enabled
    assert icon != motion_sensor.settings_property["general_device_settings"].icon
    assert name != motion_sensor.settings_property["general_device_settings"].name
    assert zone_id != motion_sensor.settings_property["general_device_settings"].zone_id


def test_setting_general_device_settings(remote_gateway: HomeControl, requests_mock: Mocker) -> None:
    """Test setting general device settings."""
    response = FIXTURE["success"]
    requests_mock.post(f"{HOMECONTROL_URL}/remote/json-rpc", json=response)
    motion_sensor = remote_gateway.devices[ELEMENT_ID]
    events_enabled = motion_sensor.settings_property["general_device_settings"].events_enabled
    icon = motion_sensor.settings_property["general_device_settings"].icon
    name = motion_sensor.settings_property["general_device_settings"].name
    zone_id = motion_sensor.settings_property["general_device_settings"].zone_id
    motion_sensor.settings_property["general_device_settings"].set(zone_id="hz_2")
    assert motion_sensor.settings_property["general_device_settings"].events_enabled == events_enabled
    assert icon == motion_sensor.settings_property["general_device_settings"].icon
    assert name == motion_sensor.settings_property["general_device_settings"].name
    assert zone_id != motion_sensor.settings_property["general_device_settings"].zone_id


def test_changing_led_settings(local_gateway: HomeControl) -> None:
    """Test changing led settings."""
    motion_sensor = local_gateway.devices[ELEMENT_ID]
    WEBSOCKET.recv_packet(json.dumps(FIXTURE["led"]))
    assert not motion_sensor.settings_property["led"].led_setting


def test_setting_led(remote_gateway: HomeControl, requests_mock: Mocker) -> None:
    """Test setting led settings."""
    response = FIXTURE["success"]
    requests_mock.post(f"{HOMECONTROL_URL}/remote/json-rpc", json=response)
    motion_sensor = remote_gateway.devices[ELEMENT_ID]
    led_setting = motion_sensor.settings_property["led"].led_setting
    motion_sensor.settings_property["led"].set(led_setting=False)
    assert motion_sensor.settings_property["led"].led_setting != led_setting


def test_pending_operation(local_gateway: HomeControl) -> None:
    """Test processing of a pending operation."""
    motion_sensor = local_gateway.devices[ELEMENT_ID]
    WEBSOCKET.recv_packet(json.dumps(FIXTURE["pending_operation"]))
    assert motion_sensor.pending_operations


def test_changing_motion_sensitivity(local_gateway: HomeControl) -> None:
    """Test changing motion sensitivity settings."""
    motion_sensor = local_gateway.devices[ELEMENT_ID]
    motion_sensitivity = motion_sensor.settings_property["motion_sensitivity"].motion_sensitivity
    WEBSOCKET.recv_packet(json.dumps(FIXTURE["motion_sensitivity"]))
    assert motion_sensor.settings_property["motion_sensitivity"].motion_sensitivity != motion_sensitivity


def test_setting_motion_sensitivity(remote_gateway: HomeControl, requests_mock: Mocker) -> None:
    """Test setting motion sensitivity settings."""
    response = FIXTURE["success"]
    requests_mock.post(f"{HOMECONTROL_URL}/remote/json-rpc", json=response)
    motion_sensor = remote_gateway.devices[ELEMENT_ID]
    motion_sensitivity = motion_sensor.settings_property["motion_sensitivity"].motion_sensitivity
    assert motion_sensor.settings_property["motion_sensitivity"].set(9)
    assert motion_sensor.settings_property["motion_sensitivity"].motion_sensitivity != motion_sensitivity


def test_setting_motion_sensitivity_same_value(remote_gateway: HomeControl, requests_mock: Mocker) -> None:
    """Test setting motion sensitivity settings using the same value."""
    response = FIXTURE["fail"]
    requests_mock.post(f"{HOMECONTROL_URL}/remote/json-rpc", json=response)
    motion_sensor = remote_gateway.devices[ELEMENT_ID]
    motion_sensitivity = motion_sensor.settings_property["motion_sensitivity"].motion_sensitivity
    assert not motion_sensor.settings_property["motion_sensitivity"].set(9)
    assert motion_sensor.settings_property["motion_sensitivity"].motion_sensitivity == motion_sensitivity


def test_temperature_report_setting(local_gateway: HomeControl) -> None:
    """Test processing the temperature report setting."""
    motion_sensor = local_gateway.devices[ELEMENT_ID]
    WEBSOCKET.recv_packet(json.dumps(FIXTURE["temperature_report"]))
    assert not motion_sensor.settings_property["temperature_report"].temp_report


def test_setting_temperature_report(remote_gateway: HomeControl, requests_mock: Mocker) -> None:
    """Test chaning the temperature report setting."""
    response = FIXTURE["success"]
    requests_mock.post(f"{HOMECONTROL_URL}/remote/json-rpc", json=response)
    motion_sensor = remote_gateway.devices[ELEMENT_ID]
    assert motion_sensor.settings_property["temperature_report"].set(temp_report=False)
    assert not motion_sensor.settings_property["temperature_report"].temp_report


def test_setting_temperature_report_same_value(remote_gateway: HomeControl, requests_mock: Mocker) -> None:
    """Test chaning the temperature report setting using the same value."""
    response = FIXTURE["fail"]
    requests_mock.post(f"{HOMECONTROL_URL}/remote/json-rpc", json=response)
    motion_sensor = remote_gateway.devices[ELEMENT_ID]
    assert not motion_sensor.settings_property["temperature_report"].set(temp_report=False)
    assert motion_sensor.settings_property["temperature_report"].temp_report


def test_changing_expert_settings(local_gateway: HomeControl) -> None:
    """Test changing expert settings."""
    motion_sensor = local_gateway.devices[ELEMENT_ID]
    param_changed = motion_sensor.settings_property["param_changed"].param_changed
    WEBSOCKET.recv_packet(json.dumps(FIXTURE["param_changed"]))
    assert param_changed != motion_sensor.settings_property["param_changed"].param_changed


def test_getting_properties(local_gateway: HomeControl) -> None:
    """Test getting a property of the device."""
    motion_sensor = local_gateway.devices[ELEMENT_ID]
    assert motion_sensor.get_property("binary_sensor") == list(motion_sensor.binary_sensor_property.values())
    assert motion_sensor.get_property("multi_level_sensor") == list(motion_sensor.multi_level_sensor_property.values())


def test_getting_state(local_gateway: HomeControl) -> None:
    """Test getting the online state of the device."""
    motion_sensor = local_gateway.devices[ELEMENT_ID]
    assert motion_sensor.is_online()
