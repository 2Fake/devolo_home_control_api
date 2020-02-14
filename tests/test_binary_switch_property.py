import pytest

from devolo_home_control_api.backend.mprm_rest import MprmDeviceCommunicationError


@pytest.mark.usefixtures("home_control_instance")
@pytest.mark.usefixtures("mock_mprmrest__extract_data_from_element_uid")
@pytest.mark.usefixtures("mock_mydevolo__call")
class TestBinarySwitchProperty:
    def test_fetch_binary_switch_state_valid_on(self):
        assert self.homecontrol.devices.get(self.devices.get("mains").get("uid"))\
            .binary_switch_property.get(self.devices.get("mains").get("elementUIDs")[1]).fetch_binary_switch_state()

    def test_fetch_binary_switch_state_valid_off(self):
        assert not self.homecontrol.devices.get(self.devices.get("mains").get("uid"))\
            .binary_switch_property.get(self.devices.get("mains").get("elementUIDs")[1]).fetch_binary_switch_state()

    @pytest.mark.usefixtures("mock_mprmrest__post_set")
    def test_set_binary_switch_valid(self):
        self.homecontrol.devices.get(self.devices.get("mains").get("uid"))\
            .binary_switch_property.get(self.devices.get("mains").get("elementUIDs")[1]).set_binary_switch(True)
        assert self.homecontrol.devices.get(self.devices.get("mains").get("uid"))\
            .binary_switch_property.get(self.devices.get("mains").get("elementUIDs")[1]).state

    @pytest.mark.usefixtures("mock_mprmrest__post_set")
    @pytest.mark.usefixtures("mock_homecontrol_is_online")
    def test_set_binary_switch_error(self):
        with pytest.raises(MprmDeviceCommunicationError):
            # TODO: Make this dynamic again
            self.homecontrol.devices['hdm:ZWave:F6BF9812/4'].binary_switch_property['devolo.BinarySwitch:hdm:ZWave:F6BF9812/4'].set_binary_switch(True)
