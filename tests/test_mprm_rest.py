import pytest

from devolo_home_control_api.mprm_rest import MprmDeviceError


@pytest.mark.usefixtures("mprm_instance")
@pytest.mark.usefixtures("mock_mprmrest__extract_data_from_element_uid")
class TestMprmRest:
    def test_binary_switch_devices(self):
        assert hasattr(self.mprm.binary_switch_devices[0], "binary_switch_property")

    def test_get_binary_switch_state_invalid(self):
        with pytest.raises(ValueError):
            self.mprm.get_binary_switch_state("invalid")

    def test_get_binary_switch_state_valid_on(self):
        assert self.mprm.get_binary_switch_state(element_uid=f"devolo.BinarySwitch:{self.device.get('mains').get('uid')}")

    def test_get_binary_switch_state_valid_off(self):
        assert not self.mprm.get_binary_switch_state(element_uid=f"devolo.BinarySwitch:{self.device.get('mains').get('uid')}")

    def test_get_consumption_invalid(self):
        with pytest.raises(ValueError):
            self.mprm.get_consumption("invalid", "invalid")
        with pytest.raises(ValueError):
            self.mprm.get_consumption("devolo.Meter:", "invalid")

    def test_get_consumption_valid(self):
        current = self.mprm.get_consumption(element_uid=f"devolo.Meter:{self.device.get('mains').get('uid')}", consumption_type="current")
        total = self.mprm.get_consumption(element_uid=f"devolo.Meter:{self.device.get('mains').get('uid')}", consumption_type="total")
        assert current == 0.58
        assert total == 125.68

    def test_get_general_device_settings_invalid(self):
        with pytest.raises(ValueError):
            self.mprm.get_general_device_settings("invalid")

    def test_get_general_device_settings_valid(self):
        name, icon, zone_id, events_enabled = self.mprm.get_general_device_settings(setting_uid=f"gds.{self.device.get('mains').get('uid')}")
        assert name == "Light"
        assert icon == "light-bulb"
        assert zone_id == "hz_2"
        assert events_enabled

    def test_get_led_setting_invalid(self):
        with pytest.raises(ValueError):
            self.mprm.get_led_setting("invalid")

    def test_get_led_setting_valid(self):
        assert self.mprm.get_led_setting(setting_uid=f"lis.{self.device.get('mains').get('uid')}")

    def test_get_param_changed_invalid(self):
        with pytest.raises(ValueError):
            self.mprm.get_param_changed_setting("invalid")

    def test_get_param_changed_valid(self):
        assert not self.mprm.get_param_changed_setting(setting_uid=f"cps.{self.device.get('mains').get('uid')}")

    def test_get_protection_setting_invalid(self):
        with pytest.raises(ValueError):
            self.mprm.get_protection_setting(setting_uid="invalid", protection_setting="local")

        with pytest.raises(ValueError):
            self.mprm.get_protection_setting(setting_uid=f"ps.{self.device.get('mains').get('uid')}", protection_setting="invalid")

    def test_get_protection_setting_valid(self):
        local_switch = self.mprm.get_protection_setting(setting_uid=f"ps.{self.device.get('mains').get('uid')}", protection_setting="local")
        remote_switch = self.mprm.get_protection_setting(setting_uid=f"ps.{self.device.get('mains').get('uid')}", protection_setting="remote")
        assert local_switch
        assert not remote_switch

    def test_get_voltage_invalid(self):
        with pytest.raises(ValueError):
            self.mprm.get_voltage("invalid")

    def test_get_voltage_valid(self):
        voltage = self.mprm.get_voltage(f"devolo.VoltageMultiLevelSensor:{self.device.get('mains').get('uid')}")
        assert voltage == 237

    def test_set_binary_switch_invalid(self):
        with pytest.raises(ValueError):
            self.mprm.set_binary_switch(element_uid="invalid", state=True)
        with pytest.raises(ValueError):
            self.mprm.set_binary_switch(element_uid=f"devolo.BinarySwitch:{self.device.get('mains').get('uid')}", state="invalid")

    @pytest.mark.usefixtures("mock_mprmrest__post_set_success")
    def test_set_binary_switch_valid(self):
        element_uid = f"devolo.BinarySwitch:{self.device.get('mains').get('uid')}"
        self.mprm.set_binary_switch(element_uid=element_uid, state=True)
        assert self.mprm.devices.get(self.device.get('mains').get('uid')).binary_switch_property.get(element_uid).state

    @pytest.mark.usefixtures("mock_mprmrest__post_set_error")
    def test_set_binary_switch_error(self):
        with pytest.raises(MprmDeviceError):
            element_uid = f"devolo.BinarySwitch:{self.device.get('mains').get('uid')}"
            self.mprm.set_binary_switch(element_uid=element_uid, state=True)
