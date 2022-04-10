import pytest
from devolo_home_control_api.exceptions.device import WrongElementError
from devolo_home_control_api.properties.multi_level_switch_property import MultiLevelSwitchProperty


@pytest.mark.usefixtures("home_control_instance")
class TestMultiLevelSwitchProperty:
    def test_multi_level_switch_property_invalid(self):
        with pytest.raises(WrongElementError):
            MultiLevelSwitchProperty(element_uid="invalid", setter=lambda uid, state: None)

    def test_unit(self):
        element_uid = self.devices["siren"]["elementUIDs"][0]
        switch_type = self.devices["siren"]["switch_type"]
        mlsp = MultiLevelSwitchProperty(element_uid=element_uid, setter=lambda uid, state: None, switch_type=switch_type)
        assert mlsp.unit is None

    def test_set_invalid(self):
        value = self.devices["multi_level_switch"]["max"] + 1
        element_uid = self.devices["multi_level_switch"]["elementUIDs"][0]
        device = self.homecontrol.devices.get(self.devices["multi_level_switch"]["uid"])
        device.multi_level_switch_property[element_uid]._setter = lambda uid, state: True
        with pytest.raises(ValueError):
            device.multi_level_switch_property[element_uid].set(value=value)

    def test_set(self):
        value = self.devices["multi_level_switch"]["value"]
        element_uid = self.devices["multi_level_switch"]["elementUIDs"][0]
        device = self.homecontrol.devices.get(self.devices["multi_level_switch"]["uid"])
        device.multi_level_switch_property[element_uid]._setter = lambda uid, state: True
        device.multi_level_switch_property[element_uid].set(value=value)
        assert device.multi_level_switch_property[element_uid].value == value
