import pytest


@pytest.mark.usefixtures("home_control_instance")
@pytest.mark.usefixtures("mock_mprmrest__extract_data_from_element_uid")
@pytest.mark.usefixtures("mock_mydevolo__call")
class TestConsumption:
    def test_get_consumption_invalid(self):
        with pytest.raises(ValueError):
            self.homecontrol.devices.get(self.devices.get("mains").get("uid"))\
                .consumption_property.get(self.devices.get("mains").get("element_uids")[0]).get_consumption("invalid")

    def test_get_consumption_valid(self):
        current = self.homecontrol.devices.get(self.devices.get("mains").get("uid"))\
            .consumption_property.get(self.devices.get("mains").get("element_uids")[0])\
            .get_consumption(consumption_type="current")
        total = self.homecontrol.devices.get(self.devices.get("mains").get("uid"))\
            .consumption_property.get(self.devices.get("mains").get("element_uids")[0])\
            .get_consumption(consumption_type="total")
        assert current == 0.58
        assert total == 125.68
