import pytest
from devolo_home_control_api.exceptions.device import SwitchingProtected, WrongElementError
from devolo_home_control_api.properties.binary_switch_property import BinarySwitchProperty


@pytest.mark.usefixtures("home_control_instance")
class TestBinarySwitchProperty:
    def test_binary_switch_property_invalid(self):
        with pytest.raises(WrongElementError):
            BinarySwitchProperty(element_uid="invalid", setter=lambda uid, state: None, state=True, enabled=True)

    def test_set(self):
        uid = self.devices["mains"]["uid"]
        element_uid = self.devices["mains"]["elementUIDs"][1]
        self.homecontrol.devices[uid].binary_switch_property[element_uid]._setter = lambda uid, state: True
        self.homecontrol.devices[uid].binary_switch_property[element_uid].set(True)
        assert self.homecontrol.devices[uid].binary_switch_property[element_uid].state

    def test_set_protected(self):
        uid = self.devices["mains"]["uid"]
        element_uid = self.devices["mains"]["elementUIDs"][1]
        self.homecontrol.devices[uid].binary_switch_property[element_uid]._setter = lambda uid, state: True
        self.homecontrol.devices[uid].binary_switch_property[element_uid].enabled = False
        with pytest.raises(SwitchingProtected):
            self.homecontrol.devices[uid].binary_switch_property[element_uid].set(True)
