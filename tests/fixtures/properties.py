import pytest


@pytest.fixture()
def mock_properties(mocker):
    mocker.patch("devolo_home_control_api.properties.consumption_property.ConsumptionProperty.fetch_consumption",
                 return_value=None)
    mocker.patch("devolo_home_control_api.properties.binary_switch_property.BinarySwitchProperty.fetch_binary_switch_state",
                 return_value=None)
    mocker.patch("devolo_home_control_api.properties.voltage_property.VoltageProperty.fetch_voltage",
                 return_value=None)
    mocker.patch("devolo_home_control_api.properties.settings_property.SettingsProperty.fetch_general_device_settings",
                 return_value=None)
    mocker.patch("devolo_home_control_api.properties.settings_property.SettingsProperty.fetch_param_changed_setting",
                 return_value=None)
    mocker.patch("devolo_home_control_api.properties.settings_property.SettingsProperty.fetch_protection_setting",
                 return_value=None)
    mocker.patch("devolo_home_control_api.properties.settings_property.SettingsProperty.fetch_led_setting",
                 return_value=None)
