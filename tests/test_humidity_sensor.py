"""Test interacting with a humidity sensor."""
import json

from requests_mock import Mocker

from devolo_home_control_api.homecontrol import HomeControl

from . import HOMECONTROL_URL, Subscriber, load_fixture
from .mocks import WEBSOCKET

ELEMENT_ID = "hdm:ZWave:CBC56091/4"
FIXTURE = load_fixture("homecontrol_humidity_sensor")


def test_state_change(local_gateway: HomeControl) -> None:
    """Test state change of a humidity sensor."""
    subscriber = Subscriber(ELEMENT_ID)
    local_gateway.publisher.register(ELEMENT_ID, subscriber)
    humidity_sensor = local_gateway.devices[ELEMENT_ID]
    humidity_bar = humidity_sensor.humidity_bar_property[f"devolo.HumidityBar:{ELEMENT_ID}"]
    value = humidity_bar.value
    zone = humidity_bar.zone
    last_activity = humidity_bar.last_activity
    WEBSOCKET.recv_packet(json.dumps(FIXTURE["value_event"]))
    assert value != humidity_bar.value
    WEBSOCKET.recv_packet(json.dumps(FIXTURE["zone_event"]))
    assert zone != humidity_bar.zone
    assert last_activity != humidity_bar.last_activity
    assert subscriber.update.call_count == 2


def test_temperature_report(local_gateway: HomeControl) -> None:
    """Test processing a temperature report."""
    subscriber = Subscriber(ELEMENT_ID)
    local_gateway.publisher.register(ELEMENT_ID, subscriber)
    humidity_sensor = local_gateway.devices[ELEMENT_ID]
    temperature_sensor = humidity_sensor.multi_level_sensor_property[
        f"devolo.MultiLevelSensor:{ELEMENT_ID}#MultilevelSensor(1)"
    ]
    value = temperature_sensor.value
    last_activity = temperature_sensor.last_activity
    WEBSOCKET.recv_packet(json.dumps(FIXTURE["temperature_event"]))
    assert value != temperature_sensor.value
    assert last_activity != temperature_sensor.last_activity
    assert subscriber.update.call_count == 1


def test_mildew_report(local_gateway: HomeControl) -> None:
    """Test processing a mildew report."""
    subscriber = Subscriber(ELEMENT_ID)
    local_gateway.publisher.register(ELEMENT_ID, subscriber)
    humidity_sensor = local_gateway.devices[ELEMENT_ID]
    mildew_sensor = humidity_sensor.binary_sensor_property[f"devolo.MildewSensor:{ELEMENT_ID}"]
    state = mildew_sensor.state
    last_activity = mildew_sensor.last_activity
    WEBSOCKET.recv_packet(json.dumps(FIXTURE["mildew_event"]))
    assert state != mildew_sensor.state
    assert last_activity != mildew_sensor.last_activity
    assert subscriber.update.call_count == 1


def test_battery_report(local_gateway: HomeControl) -> None:
    """Test processing a battery report."""
    subscriber = Subscriber(ELEMENT_ID)
    local_gateway.publisher.register(ELEMENT_ID, subscriber)
    humidity_sensor = local_gateway.devices[ELEMENT_ID]
    battery_level = humidity_sensor.battery_level
    battery_low = humidity_sensor.battery_low
    WEBSOCKET.recv_packet(json.dumps(FIXTURE["battery_low"]))
    WEBSOCKET.recv_packet(json.dumps(FIXTURE["battery_level"]))
    assert battery_level != humidity_sensor.battery_level
    assert battery_low != humidity_sensor.battery_low
    assert subscriber.update.call_count == 2


def test_changing_general_device_settings(local_gateway: HomeControl) -> None:
    """Test changing general device settings."""
    humidity_sensor = local_gateway.devices[ELEMENT_ID]
    events_enabled = humidity_sensor.settings_property["general_device_settings"].events_enabled
    icon = humidity_sensor.settings_property["general_device_settings"].icon
    name = humidity_sensor.settings_property["general_device_settings"].name
    zone_id = humidity_sensor.settings_property["general_device_settings"].zone_id
    WEBSOCKET.recv_packet(json.dumps(FIXTURE["general_device_settings"]))
    assert events_enabled != humidity_sensor.settings_property["general_device_settings"].events_enabled
    assert icon != humidity_sensor.settings_property["general_device_settings"].icon
    assert name != humidity_sensor.settings_property["general_device_settings"].name
    assert zone_id != humidity_sensor.settings_property["general_device_settings"].zone_id


def test_setting_general_device_settings(remote_gateway: HomeControl, requests_mock: Mocker) -> None:
    """Test setting general device settings."""
    response = FIXTURE["success"]
    requests_mock.post(f"{HOMECONTROL_URL}/remote/json-rpc", json=response)
    humidity_sensor = remote_gateway.devices[ELEMENT_ID]
    events_enabled = humidity_sensor.settings_property["general_device_settings"].events_enabled
    icon = humidity_sensor.settings_property["general_device_settings"].icon
    name = humidity_sensor.settings_property["general_device_settings"].name
    zone_id = humidity_sensor.settings_property["general_device_settings"].zone_id
    humidity_sensor.settings_property["general_device_settings"].set(events_enabled=False)
    assert humidity_sensor.settings_property["general_device_settings"].events_enabled != events_enabled
    assert icon == humidity_sensor.settings_property["general_device_settings"].icon
    assert name == humidity_sensor.settings_property["general_device_settings"].name
    assert zone_id == humidity_sensor.settings_property["general_device_settings"].zone_id


def test_changing_led_settings(local_gateway: HomeControl) -> None:
    """Test changing led settings."""
    fixture = load_fixture("homecontrol_humidity_sensor")
    humidity_sensor = local_gateway.devices[ELEMENT_ID]
    WEBSOCKET.recv_packet(json.dumps(fixture["led"]))
    assert not humidity_sensor.settings_property["led"].led_setting


def test_setting_led(remote_gateway: HomeControl, requests_mock: Mocker) -> None:
    """Test setting led settings."""
    response = FIXTURE["success"]
    requests_mock.post(f"{HOMECONTROL_URL}/remote/json-rpc", json=response)
    humidity_sensor = remote_gateway.devices[ELEMENT_ID]
    led_setting = humidity_sensor.settings_property["led"].led_setting
    humidity_sensor.settings_property["led"].set(led_setting=False)
    assert humidity_sensor.settings_property["led"].led_setting != led_setting


def test_temperature_report_setting(local_gateway: HomeControl) -> None:
    """Test processing the temperature report setting."""
    fixture = load_fixture("homecontrol_humidity_sensor")
    humidity_sensor = local_gateway.devices[ELEMENT_ID]
    WEBSOCKET.recv_packet(json.dumps(fixture["temperature_report"]))
    assert not humidity_sensor.settings_property["temperature_report"].temp_report


def test_setting_temperature_report(remote_gateway: HomeControl, requests_mock: Mocker) -> None:
    """Test chaning the temperature report setting."""
    response = FIXTURE["success"]
    requests_mock.post(f"{HOMECONTROL_URL}/remote/json-rpc", json=response)
    humidity_sensor = remote_gateway.devices[ELEMENT_ID]
    humidity_sensor.settings_property["temperature_report"].set(temp_report=False)
    assert not humidity_sensor.settings_property["temperature_report"].temp_report


def test_changing_expert_settings(local_gateway: HomeControl) -> None:
    """Test processing expert settings."""
    humidity_sensor = local_gateway.devices[ELEMENT_ID]
    param_changed = humidity_sensor.settings_property["param_changed"].param_changed
    WEBSOCKET.recv_packet(json.dumps(FIXTURE["param_changed"]))
    assert param_changed != humidity_sensor.settings_property["param_changed"].param_changed


def test_getting_properties(local_gateway: HomeControl) -> None:
    """Test getting a property of the device."""
    humidity_sensor = local_gateway.devices[ELEMENT_ID]
    assert humidity_sensor.get_property("humidity_bar") == list(humidity_sensor.humidity_bar_property.values())
    assert humidity_sensor.get_property("multi_level_sensor") == list(humidity_sensor.multi_level_sensor_property.values())


def test_getting_state(local_gateway: HomeControl) -> None:
    """Test getting the online state of the device."""
    humidity_sensor = local_gateway.devices[ELEMENT_ID]
    assert humidity_sensor.is_online()
