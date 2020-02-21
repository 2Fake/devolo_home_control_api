import pytest


@pytest.mark.usefixtures("home_control_instance")
class TestConsumption:
    def test_fetch_consumption_invalid(self):
        with pytest.raises(ValueError):
            self.homecontrol.devices.get(self.devices.get("mains").get("uid"))\
                .consumption_property.get(self.devices.get("mains").get("elementUIDs")[0]).fetch_consumption("invalid")

    def test_fetch_consumption_valid(self, mock_mprmrest__extract_data_from_element_uid):
        current = self.homecontrol.devices.get(self.devices.get("mains").get("uid"))\
            .consumption_property.get(self.devices.get("mains").get("elementUIDs")[0])\
            .fetch_consumption(consumption_type="current")
        total = self.homecontrol.devices.get(self.devices.get("mains").get("uid"))\
            .consumption_property.get(self.devices.get("mains").get("elementUIDs")[0])\
            .fetch_consumption(consumption_type="total")
        assert current == 0.58
        assert total == 125.68
