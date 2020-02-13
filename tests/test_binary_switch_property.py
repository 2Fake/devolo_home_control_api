import pytest

from devolo_home_control_api.backend.mprm_rest import MprmDeviceCommunicationError


@pytest.mark.usefixtures("home_control_instance")
@pytest.mark.usefixtures("mock_mprmrest__extract_data_from_element_uid")
@pytest.mark.usefixtures("mock_mydevolo__call")
class TestBinarySwitchProperty:
    def test_get_binary_switch_state_valid_on(self):
        assert self.homecontrol.devices.get(self.devices.get("mains").get("uid")).binary_switch_property.get(self.devices.get("mains").get("element_uids")[1]).get_binary_switch_state()

    def test_get_binary_switch_state_valid_off(self):
        assert not self.homecontrol.devices.get(self.devices.get("mains").get("uid")).binary_switch_property.get(self.devices.get("mains").get("element_uids")[1]).get_binary_switch_state()

    @pytest.mark.usefixtures("mock_mprmrest__post_set")
    def test_set_binary_switch_valid(self):
        self.homecontrol.devices.get(self.devices.get("mains").get("uid")).binary_switch_property.get(self.devices.get("mains").get("element_uids")[1]).set_binary_switch(True)
        assert self.homecontrol.devices.get(self.devices.get("mains").get("uid")).binary_switch_property.get(self.devices.get("mains").get("element_uids")[1]).state

    # TODO: Depends on _device_usable in mprm_rest
    # @pytest.mark.usefixtures("mock_mprmrest__post_set")
    # def test_set_binary_switch_error(self):
    #     with pytest.raises(MprmDeviceCommunicationError):
    #         self.homecontrol.devices.get(self.devices.get("ambiguous_2").get("uid")).binary_switch_property.get(self.devices.get("ambiguous_2").get("element_uids")[0]).set_binary_switch(True)
