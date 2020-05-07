import pytest

from devolo_home_control_api.exceptions.device import WrongElementError
from devolo_home_control_api.properties.binary_switch_property import BinarySwitchProperty


@pytest.mark.usefixtures("home_control_instance")
class TestBinarySwitchProperty:
    def test_binary_switch_property_invalid(self, gateway_instance, mprm_session):
        with pytest.raises(WrongElementError):
            BinarySwitchProperty(gateway=gateway_instance, session=mprm_session, element_uid="invalid", state=True)

    @pytest.mark.usefixtures("mock_mprmrest__post_set")
    def test_set_valid(self):
        self.homecontrol.devices.get(self.devices.get("mains").get("uid"))\
            .binary_switch_property.get(self.devices.get("mains").get("elementUIDs")[1]).set(True)
        assert self.homecontrol.devices.get(self.devices.get("mains").get("uid"))\
            .binary_switch_property.get(self.devices.get("mains").get("elementUIDs")[1]).state
