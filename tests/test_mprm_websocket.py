import pytest


@pytest.mark.usefixtures("mprm_instance")
@pytest.mark.usefixtures("mock_mprmrest__extract_data_from_element_uid")
class TestMprmWebsocket:
    def test_get_consumption_invalid(self):
        with pytest.raises(ValueError):
            self.mprm.get_consumption("invalid", "invalid")
        with pytest.raises(ValueError):
            self.mprm.get_consumption("devolo.Meter:", "invalid")

    def test_get_consumption_valid(self, fill_device_data):
        current = self.mprm.get_consumption(f"devolo.Meter:{self.device.get('mains').get('uid')}", "current")
        total = self.mprm.get_consumption(f"devolo.Meter:{self.device.get('mains').get('uid')}", "total")
        assert current == 0.58
        assert total == 125.68

    def test_get_binary_switch_state_invalid(self):
        with pytest.raises(ValueError):
            self.mprm.get_binary_switch_state("invalid")

    def test_update_binary_switch_state_invalid(self):
        with pytest.raises(ValueError):
            self.mprm.update_binary_switch_state("invalid")

    def test_update_binary_switch_state_valid(self, fill_device_data):
        binary_switch_property = self.mprm.devices.get(self.device.get("mains").get("uid")).binary_switch_property
        state = binary_switch_property.get(f"devolo.BinarySwitch:{self.device.get('mains').get('uid')}").state
        self.mprm.update_binary_switch_state(f"devolo.BinarySwitch:{self.device.get('mains').get('uid')}", value=True)
        assert state != binary_switch_property.get(f"devolo.BinarySwitch:{self.device.get('mains').get('uid')}").state

    def test_update_consumption_invalid(self):
        with pytest.raises(ValueError):
            self.mprm.update_consumption("invalid", "current")
        with pytest.raises(ValueError):
            self.mprm.update_consumption("devolo.Meter", "invalid")

    def test_update_consumption_valid(self, fill_device_data):
        consumption_property = self.mprm.devices.get(self.device.get("mains").get("uid")).consumption_property
        current_before = consumption_property.get(f"devolo.Meter:{self.device.get('mains').get('uid')}").current
        total_before = consumption_property.get(f"devolo.Meter:{self.device.get('mains').get('uid')}").total
        self.mprm.update_consumption(element_uid=f"devolo.Meter:{self.device.get('mains').get('uid')}",
                                     consumption="current", value=1.58)
        self.mprm.update_consumption(element_uid=f"devolo.Meter:{self.device.get('mains').get('uid')}",
                                     consumption="total", value=254)
        assert current_before != consumption_property.get(f"devolo.Meter:{self.device.get('mains').get('uid')}").current
        assert total_before != consumption_property.get(f"devolo.Meter:{self.device.get('mains').get('uid')}").total
        assert consumption_property.get(f"devolo.Meter:{self.device.get('mains').get('uid')}").current == 1.58
        assert consumption_property.get(f"devolo.Meter:{self.device.get('mains').get('uid')}").total == 254

    def test_update_voltage_valid(self, fill_device_data):
        voltage_property = self.mprm.devices.get(self.device.get("mains").get("uid")).voltage_property
        current_voltage = voltage_property.get(f"devolo.VoltageMultiLevelSensor:{self.device.get('mains').get('uid')}").current
        self.mprm.update_voltage(element_uid=f"devolo.VoltageMultiLevelSensor:{self.device.get('mains').get('uid')}", value=257)
        assert current_voltage != voltage_property.get(f"devolo.VoltageMultiLevelSensor:{self.device.get('mains').get('uid')}").current
        assert voltage_property.get(f"devolo.VoltageMultiLevelSensor:{self.device.get('mains').get('uid')}").current == 257

    def test_update_voltage_invalid(self):
        with pytest.raises(ValueError):
            self.mprm.update_voltage(element_uid="invalid", value=123)
