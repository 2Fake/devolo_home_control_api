"""Test interacting with a siren."""
import json

from requests_mock import Mocker

from devolo_home_control_api.homecontrol import HomeControl

from . import HOMECONTROL_URL, Subscriber, load_fixture
from .mocks import WEBSOCKET

ELEMENT_ID = "hdm:ZWave:CBC56091/6"
FIXTURE = load_fixture("homecontrol_siren")


def test_state_change(local_gateway: HomeControl, gateway_ip: str, requests_mock: Mocker) -> None:
    """Test state change of a siren."""
    response = FIXTURE["success"]
    requests_mock.post(f"http://{gateway_ip}/remote/json-rpc", json=response)
    subscriber = Subscriber(ELEMENT_ID)
    subscriber = Subscriber(ELEMENT_ID)
    local_gateway.publisher.register(ELEMENT_ID, subscriber)
    siren = local_gateway.devices[ELEMENT_ID]

    multi_level_switch = siren.multi_level_switch_property[f"devolo.SirenMultiLevelSwitch:{ELEMENT_ID}"]
    value = multi_level_switch.value
    last_activity = multi_level_switch.last_activity
    WEBSOCKET.recv_packet(json.dumps(FIXTURE["switch_event"]))
    assert value != multi_level_switch.value
    assert last_activity != multi_level_switch.last_activity
    assert subscriber.update.call_count == 1

    multi_level_switch.set(value + 1)
    assert value + 1 == multi_level_switch.value


def test_changing_general_device_settings(local_gateway: HomeControl) -> None:
    """Test changing general device settings."""
    siren = local_gateway.devices[ELEMENT_ID]
    events_enabled = siren.settings_property["general_device_settings"].events_enabled
    icon = siren.settings_property["general_device_settings"].icon
    name = siren.settings_property["general_device_settings"].name
    zone_id = siren.settings_property["general_device_settings"].zone_id
    WEBSOCKET.recv_packet(json.dumps(FIXTURE["general_device_settings"]))
    assert events_enabled != siren.settings_property["general_device_settings"].events_enabled
    assert icon != siren.settings_property["general_device_settings"].icon
    assert name != siren.settings_property["general_device_settings"].name
    assert zone_id != siren.settings_property["general_device_settings"].zone_id


def test_setting_general_device_settings(remote_gateway: HomeControl, requests_mock: Mocker) -> None:
    """Test setting general device settings."""
    response = FIXTURE["success"]
    requests_mock.post(f"{HOMECONTROL_URL}/remote/json-rpc", json=response)
    siren = remote_gateway.devices[ELEMENT_ID]
    events_enabled = siren.settings_property["general_device_settings"].events_enabled
    icon = siren.settings_property["general_device_settings"].icon
    name = siren.settings_property["general_device_settings"].name
    zone_id = siren.settings_property["general_device_settings"].zone_id
    siren.settings_property["general_device_settings"].set(events_enabled=False, icon="icon_20")
    assert siren.settings_property["general_device_settings"].events_enabled != events_enabled
    assert icon != siren.settings_property["general_device_settings"].icon
    assert name == siren.settings_property["general_device_settings"].name
    assert zone_id == siren.settings_property["general_device_settings"].zone_id


def test_changing_mute_state(local_gateway: HomeControl) -> None:
    """Test muting the siren."""
    siren = local_gateway.devices[ELEMENT_ID]
    mute = siren.settings_property["muted"].value
    WEBSOCKET.recv_packet(json.dumps(FIXTURE["muted"]))
    assert mute != siren.settings_property["muted"].value


def test_setting_mute_state(remote_gateway: HomeControl, requests_mock: Mocker) -> None:
    """Test muting the siren."""
    response = FIXTURE["success"]
    requests_mock.post(f"{HOMECONTROL_URL}/remote/json-rpc", json=response)
    siren = remote_gateway.devices[ELEMENT_ID]
    mute = siren.settings_property["muted"].value
    assert siren.settings_property["muted"].set(value=False)
    assert mute != siren.settings_property["muted"].value


def test_setting_mute_state_same_value(remote_gateway: HomeControl, requests_mock: Mocker) -> None:
    """Test muting the siren using the same value."""
    response = FIXTURE["fail"]
    requests_mock.post(f"{HOMECONTROL_URL}/remote/json-rpc", json=response)
    siren = remote_gateway.devices[ELEMENT_ID]
    mute = siren.settings_property["muted"].value
    assert not siren.settings_property["muted"].set(value=False)
    assert mute == siren.settings_property["muted"].value


def test_changing_default_tone(local_gateway: HomeControl) -> None:
    """Test changing the default tone."""
    siren = local_gateway.devices[ELEMENT_ID]
    tone = siren.settings_property["tone"].tone
    WEBSOCKET.recv_packet(json.dumps(FIXTURE["tone"]))
    assert tone != siren.settings_property["tone"].tone


def test_changing_expert_settings(local_gateway: HomeControl) -> None:
    """Test changing expert settings."""
    siren = local_gateway.devices[ELEMENT_ID]
    param_changed = siren.settings_property["param_changed"].param_changed
    WEBSOCKET.recv_packet(json.dumps(FIXTURE["param_changed"]))
    assert param_changed != siren.settings_property["param_changed"].param_changed


def test_getting_properties(local_gateway: HomeControl) -> None:
    """Test getting a property of the device."""
    siren = local_gateway.devices[ELEMENT_ID]
    assert siren.get_property("multi_level_switch") == list(siren.multi_level_switch_property.values())


def test_getting_state(local_gateway: HomeControl) -> None:
    """Test getting the online state of the device."""
    siren = local_gateway.devices[ELEMENT_ID]
    assert siren.is_online()
