import pytest

from devolo_home_control_api.properties.consumption_property import ConsumptionProperty
from devolo_home_control_api.properties.property import WrongElementError


@pytest.mark.usefixtures("home_control_instance")
class TestConsumption:
    def test_consumption_property_invalid(self):
        with pytest.raises(WrongElementError):
            ConsumptionProperty("invalid", 0.0, 0.0, 1231412412)

    def test_fetch_consumption_invalid(self):
        with pytest.raises(ValueError):
            self.homecontrol.devices.get(self.devices.get("mains").get("uid"))\
                .consumption_property.get(self.devices.get("mains").get("elementUIDs")[0]).fetch_consumption("invalid")

    def test_fetch_consumption_valid(self, mock_mprmrest__extract_data_from_element_uid):
        current = self.homecontrol.devices.get(self.devices.get("mains").get("uid"))\
            .consumption_property.get(self.devices.get("mains").get("properties").get("elementUIDs")[0])\
            .fetch_consumption(consumption_type="current")
        total = self.homecontrol.devices.get(self.devices.get("mains").get("uid"))\
            .consumption_property.get(self.devices.get("mains").get("properties").get("elementUIDs")[0])\
            .fetch_consumption(consumption_type="total")
        assert current == 0.58
        assert total == 125.68
