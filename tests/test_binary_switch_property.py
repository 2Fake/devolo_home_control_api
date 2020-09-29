import pytest

from devolo_home_control_api.exceptions.device import SwitchingProtected, WrongElementError
from devolo_home_control_api.properties.binary_switch_property import BinarySwitchProperty


@pytest.mark.usefixtures("home_control_instance")
class TestBinarySwitchProperty:
    def test_binary_switch_property_invalid(self, gateway_instance, mprm_session):
        with pytest.raises(WrongElementError):
            BinarySwitchProperty(gateway=gateway_instance,
                                 session=mprm_session,
                                 element_uid="invalid",
                                 state=True,
                                 enabled=True)

    @pytest.mark.usefixtures("mock_mprmrest__post_set")
    def test_set_valid(self):
        uid = self.devices['mains']['uid']
        element_uid = self.devices['mains']['elementUIDs'][1]
        self.homecontrol.devices[uid].binary_switch_property[element_uid].set(True)
        assert self.homecontrol.devices[uid].binary_switch_property[element_uid].state

    def test_set_protected(self):
        uid = self.devices['mains']['uid']
        element_uid = self.devices['mains']['elementUIDs'][1]
        self.homecontrol.devices[uid].binary_switch_property[element_uid].enabled = False
        with pytest.raises(SwitchingProtected):
            self.homecontrol.devices[uid].binary_switch_property[element_uid].set(True)
