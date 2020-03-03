import pytest

from devolo_home_control_api.properties.property import WrongElementError
from devolo_home_control_api.properties.voltage_property import VoltageProperty


@pytest.mark.usefixtures("home_control_instance")
@pytest.mark.usefixtures("mock_mprmrest__extract_data_from_element_uid")
class TestVoltageProperty:
    def test_voltage_property_invalid(self):
        with pytest.raises(WrongElementError):
            VoltageProperty("invalid", 0.0)

    def test_fetch_voltage_valid(self):
        voltage = self.homecontrol.devices.get(self.devices.get("mains").get("uid")).\
            voltage_property.get(f"devolo.VoltageMultiLevelSensor:{self.devices.get('mains').get('uid')}").fetch_voltage()
        assert voltage == 237
