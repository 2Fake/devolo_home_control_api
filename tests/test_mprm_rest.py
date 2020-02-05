import pytest

from devolo_home_control_api.mprm_rest import MprmDeviceCommunicationError, MprmDeviceNotFoundError


@pytest.mark.usefixtures("mprm_instance")
@pytest.mark.usefixtures("mock_mprmrest__extract_data_from_element_uid")
@pytest.mark.usefixtures("mock_mydevolo__call")
class TestMprmRest:
    def test_binary_switch_devices(self):
        assert hasattr(self.mprm.binary_switch_devices[0], "binary_switch_property")

    def test_get_binary_switch_state_invalid(self):
        with pytest.raises(ValueError):
            self.mprm.get_binary_switch_state("invalid")

    def test_get_binary_switch_state_valid_on(self):
        assert self.mprm.get_binary_switch_state(element_uid=f"devolo.BinarySwitch:{self.devices.get('mains').get('uid')}")

    def test_get_binary_switch_state_valid_off(self):
        assert not self.mprm.get_binary_switch_state(element_uid=f"devolo.BinarySwitch:{self.devices.get('mains').get('uid')}")

    def test_get_device_uid_from_name_unique(self):
        uid = self.mprm.get_device_uid_from_name(name=self.devices.get("mains").get("name"))
        assert uid == self.devices.get("mains").get("uid")

    def test_get_device_uid_from_name_unknow(self):
        with pytest.raises(MprmDeviceNotFoundError):
            self.mprm.get_device_uid_from_name(name="unknown")

    def test_get_device_uid_from_name_ambiguous(self):
        with pytest.raises(MprmDeviceNotFoundError):
            self.mprm.get_device_uid_from_name(name=self.devices.get("ambiguous_1").get("name"))

    def test_get_device_uid_from_name_ambiguous_with_zone(self):
        uid = self.mprm.get_device_uid_from_name(name=self.devices.get("ambiguous_1").get("name"),
                                                 zone=self.devices.get("ambiguous_1").get("zone_name"))
        assert uid == self.devices.get("ambiguous_1").get("uid")

    def test_get_device_uid_from_name_ambiguous_with_zone_invalid(self):
        with pytest.raises(MprmDeviceNotFoundError):
            self.mprm.get_device_uid_from_name(name=self.devices.get("ambiguous_1").get("name"), zone="invalid")

    def test_get_consumption_invalid(self):
        with pytest.raises(ValueError):
            self.mprm.get_consumption(element_uid="invalid", consumption_type="invalid")
        with pytest.raises(ValueError):
            self.mprm.get_consumption(element_uid="devolo.Meter:", consumption_type="invalid")

    def test_get_consumption_valid(self):
        current = self.mprm.get_consumption(element_uid=f"devolo.Meter:{self.devices.get('mains').get('uid')}",
                                            consumption_type="current")
        total = self.mprm.get_consumption(element_uid=f"devolo.Meter:{self.devices.get('mains').get('uid')}",
                                          consumption_type="total")
        assert current == 0.58
        assert total == 125.68

    def test_get_general_device_settings_invalid(self):
        with pytest.raises(ValueError):
            self.mprm.get_general_device_settings(setting_uid="invalid")

    def test_get_general_device_settings_valid(self):
        name, icon, zone_id, events_enabled = \
            self.mprm.get_general_device_settings(setting_uid=f"gds.{self.devices.get('mains').get('uid')}")
        assert name == self.devices.get('mains').get('name')
        assert icon == self.devices.get('mains').get('icon')
        assert zone_id == self.devices.get('mains').get('zone_id')
        assert events_enabled

    def test_get_led_setting_invalid(self):
        with pytest.raises(ValueError):
            self.mprm.get_led_setting("invalid")

    def test_get_led_setting_valid(self):
        assert self.mprm.get_led_setting(setting_uid=f"lis.{self.devices.get('mains').get('uid')}")

    def test_get_param_changed_invalid(self):
        with pytest.raises(ValueError):
            self.mprm.get_param_changed_setting(setting_uid="invalid")

    def test_get_param_changed_valid(self):
        assert not self.mprm.get_param_changed_setting(setting_uid=f"cps.{self.devices.get('mains').get('uid')}")

    def test_get_protection_setting_invalid(self):
        with pytest.raises(ValueError):
            self.mprm.get_protection_setting(setting_uid="invalid", protection_setting="local")

        with pytest.raises(ValueError):
            self.mprm.get_protection_setting(setting_uid=f"ps.{self.devices.get('mains').get('uid')}",
                                             protection_setting="invalid")

    def test_get_protection_setting_valid(self):
        local_switch = self.mprm.get_protection_setting(setting_uid=f"ps.{self.devices.get('mains').get('uid')}",
                                                        protection_setting="local")
        remote_switch = self.mprm.get_protection_setting(setting_uid=f"ps.{self.devices.get('mains').get('uid')}",
                                                         protection_setting="remote")
        assert local_switch
        assert not remote_switch

    def test_get_voltage_invalid(self):
        with pytest.raises(ValueError):
            self.mprm.get_voltage(element_uid="invalid")

    def test_get_voltage_valid(self):
        voltage = self.mprm.get_voltage(element_uid=f"devolo.VoltageMultiLevelSensor:{self.devices.get('mains').get('uid')}")
        assert voltage == 237

    def test_set_binary_switch_invalid(self):
        with pytest.raises(ValueError):
            self.mprm.set_binary_switch(element_uid="invalid", state=True)
        with pytest.raises(ValueError):
            self.mprm.set_binary_switch(element_uid=f"devolo.BinarySwitch:{self.devices.get('mains').get('uid')}",
                                        state="invalid")

    @pytest.mark.usefixtures("mock_mprmrest__post_set")
    def test_set_binary_switch_valid(self):
        element_uid = f"devolo.BinarySwitch:{self.devices.get('mains').get('uid')}"
        self.mprm.set_binary_switch(element_uid=element_uid, state=True)
        assert self.mprm.devices.get(self.devices.get('mains').get('uid')).binary_switch_property.get(element_uid).state

    @pytest.mark.usefixtures("mock_mprmrest__post_set")
    def test_set_binary_switch_error(self):
        with pytest.raises(MprmDeviceCommunicationError):
            element_uid = f"devolo.BinarySwitch:{self.devices.get('ambiguous_2').get('uid')}"
            self.mprm.set_binary_switch(element_uid=element_uid, state=True)
