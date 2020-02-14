import pytest


@pytest.mark.usefixtures("home_control_instance")
@pytest.mark.usefixtures("mock_mprmrest__extract_data_from_element_uid")
@pytest.mark.usefixtures("mock_mydevolo__call")
class TestVoltageProperty:
    def test_get_voltage_valid(self):
        voltage = self.homecontrol.devices.get(self.devices.get("mains").get("uid")).\
            voltage_property.get(f"devolo.VoltageMultiLevelSensor:{self.devices.get('mains').get('uid')}").fetch_voltage()
        assert voltage == 237
