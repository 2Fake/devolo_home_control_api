import pytest


@pytest.mark.usefixtures("home_control_instance")
class TestSettingsProperty:
    def test_fetch_general_device_settings_valid(self, mock_mprmrest__extract_data_from_element_uid):
        name, icon, zone_id, events_enabled = \
            self.homecontrol.devices.get(self.devices.get("mains").get("uid"))\
                .settings_property.get("general_device_settings").fetch_general_device_settings()
        assert name == self.devices.get('mains').get('name')
        assert icon == self.devices.get('mains').get('icon')
        assert zone_id == self.devices.get('mains').get('zone_id')
        assert events_enabled

    def test_fetch_led_setting_valid(self, mock_mprmrest__extract_data_from_element_uid):
        assert self.homecontrol.devices.get(self.devices.get("mains").get("uid"))\
            .settings_property.get("led").fetch_led_setting()

    def test_fetch_param_changed_valid(self, mock_mprmrest__extract_data_from_element_uid):
        assert not self.homecontrol.devices.get(self.devices.get("mains").get("uid"))\
            .settings_property.get("param_changed").fetch_param_changed_setting()

    def test_fetch_protection_setting_invalid(self):
        with pytest.raises(ValueError):
            self.homecontrol.devices.get(self.devices.get("mains").get("uid"))\
                .settings_property.get("protection_setting").fetch_protection_setting(protection_setting="invalid")

    def test_fetch_protection_setting_valid(self, mock_mprmrest__extract_data_from_element_uid):
        local_switch = self.homecontrol.devices.get(self.devices.get("mains").get("uid"))\
            .settings_property.get("protection_setting").fetch_protection_setting(protection_setting="local")
        remote_switch = self.homecontrol.devices.get(self.devices.get("mains").get("uid"))\
            .settings_property.get("protection_setting").fetch_protection_setting(protection_setting="remote")
        assert local_switch
        assert not remote_switch
