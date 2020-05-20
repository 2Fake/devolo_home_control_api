import pytest

from devolo_home_control_api.exceptions.device import WrongElementError
from devolo_home_control_api.properties.multi_level_switch_property import MultiLevelSwitchProperty


@pytest.mark.usefixtures("home_control_instance")
class TestMultiLevelSwitchProperty:
    def test_multi_level_switch_property_invalid(self, gateway_instance, mprm_session):
        with pytest.raises(WrongElementError):
            MultiLevelSwitchProperty(gateway=gateway_instance, session=mprm_session, element_uid="invalid", value=0)

    def test_unit(self, gateway_instance, mprm_session):
        element_uid = self.devices.get("siren").get("elementUIDs")[0]
        switch_type = self.devices.get("siren").get("switch_type")
        mlsp = MultiLevelSwitchProperty(gateway=gateway_instance, session=mprm_session,
                                        element_uid=element_uid, switch_type=switch_type)
        assert mlsp.unit is None

    @pytest.mark.usefixtures("mock_mprmrest__post_set")
    def test_set_invalid(self):
        value = self.devices.get("multi_level_switch").get("max") + 1
        with pytest.raises(ValueError):
            self.homecontrol.devices.get(self.devices.get("multi_level_switch").get("uid"))\
                .multi_level_switch_property.get(self.devices.get("multi_level_switch").get("elementUIDs")[0]).set(value=value)

    @pytest.mark.usefixtures("mock_mprmrest__post_set")
    def test_set_valid(self):
        value = self.devices.get("multi_level_switch").get("value")
        self.homecontrol.devices.get(self.devices.get("multi_level_switch").get("uid"))\
            .multi_level_switch_property.get(self.devices.get("multi_level_switch").get("elementUIDs")[0]).set(value=value)
        assert self.homecontrol.devices.get(self.devices.get("multi_level_switch").get("uid"))\
            .multi_level_switch_property.get(self.devices.get("multi_level_switch").get("elementUIDs")[0]).value == value
