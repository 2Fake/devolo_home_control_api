import pytest


@pytest.mark.usefixtures("home_control_instance")
@pytest.mark.usefixtures("mock_mprmrest__extract_data_from_element_uid")
@pytest.mark.usefixtures("mock_mydevolo__call")
@pytest.mark.usefixtures("mock_publisher_dispatch")
class TestUpdater:
    def test_update_binary_switch_state_valid(self, fill_device_data):
        binary_switch_property = self.homecontrol.devices.get(self.devices.get("mains").get("uid")).binary_switch_property
        state = binary_switch_property.get(f"devolo.BinarySwitch:{self.devices.get('mains').get('uid')}").state
        self.homecontrol.updater.update_binary_switch_state(element_uid=f"devolo.BinarySwitch:{self.devices.get('mains').get('uid')}",
                                                            value=True)
        assert state != binary_switch_property.get(f"devolo.BinarySwitch:{self.devices.get('mains').get('uid')}").state

    def test_update_consumption_valid(self, fill_device_data):
        consumption_property = self.homecontrol.devices.get(self.devices.get("mains").get("uid")).consumption_property
        current_before = consumption_property.get(f"devolo.Meter:{self.devices.get('mains').get('uid')}").current
        total_before = consumption_property.get(f"devolo.Meter:{self.devices.get('mains').get('uid')}").total
        self.homecontrol.updater.update_consumption(element_uid=f"devolo.Meter:{self.devices.get('mains').get('uid')}",
                                                    consumption="current", value=1.58)
        self.homecontrol.updater.update_consumption(element_uid=f"devolo.Meter:{self.devices.get('mains').get('uid')}",
                                                    consumption="total", value=254)
        assert current_before != consumption_property.get(f"devolo.Meter:{self.devices.get('mains').get('uid')}").current
        assert total_before != consumption_property.get(f"devolo.Meter:{self.devices.get('mains').get('uid')}").total
        assert consumption_property.get(f"devolo.Meter:{self.devices.get('mains').get('uid')}").current == 1.58
        assert consumption_property.get(f"devolo.Meter:{self.devices.get('mains').get('uid')}").total == 254

    def test_update_gateway_state(self):
        self.homecontrol.updater.update_gateway_state(accessible=True, online_sync=False)
        assert self.homecontrol._gateway.online
        assert not self.homecontrol._gateway.sync

    def test_update_voltage_valid(self, fill_device_data):
        voltage_property = self.homecontrol.devices.get(self.devices.get("mains").get("uid")).voltage_property
        current_voltage = \
            voltage_property.get(f"devolo.VoltageMultiLevelSensor:{self.devices.get('mains').get('uid')}").current
        self.homecontrol.updater.update_voltage(element_uid=f"devolo.VoltageMultiLevelSensor:{self.devices.get('mains').get('uid')}",
                                                value=257)
        assert current_voltage != \
            voltage_property.get(f"devolo.VoltageMultiLevelSensor:{self.devices.get('mains').get('uid')}").current
        assert voltage_property.get(f"devolo.VoltageMultiLevelSensor:{self.devices.get('mains').get('uid')}").current == 257

    def test_update(self):
        self.homecontrol.updater.update(message={"properties":
                                        {"uid": f"devolo.BinarySwitch:{self.devices.get('mains').get('uid')}"}})
