import pytest

from devolo_home_control_api.properties.binary_switch_property import BinarySwitchProperty
from devolo_home_control_api.properties.consumption_property import ConsumptionProperty
from devolo_home_control_api.properties.property import WrongElementError
from devolo_home_control_api.properties.settings_property import SettingsProperty
from devolo_home_control_api.properties.voltage_property import VoltageProperty


class TestProperties:
    def test_settings_property_valid(self):
        setting_property = SettingsProperty(f"lis.{self.devices.get('mains').get('uid')}",
                                            led_setting=True,
                                            events_enabled=False,
                                            param_changed=True,
                                            local_switching=False,
                                            remote_switching=True,)
        assert setting_property.led_setting
        assert not setting_property.events_enabled
        assert setting_property.param_changed
        assert not setting_property.local_switching
        assert setting_property.remote_switching

    def test_settings_property_invalid(self):
        with pytest.raises(WrongElementError):
            SettingsProperty(self.devices.get('mains').get('uid'))


    def test_binary_switch_property_invalid(self):
        with pytest.raises(WrongElementError):
            BinarySwitchProperty("invalid")

    def test_consumption_property_invalid(self):
        with pytest.raises(WrongElementError):
            ConsumptionProperty("invalid")

    def test_voltage_property_invalid(self):
        with pytest.raises(WrongElementError):
            VoltageProperty("invalid")
