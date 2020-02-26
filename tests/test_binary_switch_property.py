import pytest

from devolo_home_control_api.backend.mprm_rest import MprmDeviceCommunicationError


@pytest.mark.usefixtures("home_control_instance")
class TestBinarySwitchProperty:
    def test_fetch_binary_switch_state_valid_on(self, mock_mprmrest__extract_data_from_element_uid):
        assert self.homecontrol.devices.get(self.devices.get("mains").get("uid"))\
            .binary_switch_property.get(self.devices.get("mains").get("elementUIDs")[1]).fetch_binary_switch_state()

    def test_fetch_binary_switch_state_valid_off(self, mock_mprmrest__extract_data_from_element_uid):
        assert not self.homecontrol.devices.get(self.devices.get("mains").get("uid"))\
            .binary_switch_property.get(self.devices.get("mains").get("elementUIDs")[1]).fetch_binary_switch_state()

    def test_set_binary_switch_valid(self, mock_mprmrest__post_set):
        self.homecontrol.devices.get(self.devices.get("mains").get("uid"))\
            .binary_switch_property.get(self.devices.get("mains").get("elementUIDs")[1]).set_binary_switch(True)
        assert self.homecontrol.devices.get(self.devices.get("mains").get("uid"))\
            .binary_switch_property.get(self.devices.get("mains").get("elementUIDs")[1]).state

    def test_set_binary_switch_error(self, mock_mprmrest__post_set, mock_homecontrol_is_online):
        with pytest.raises(MprmDeviceCommunicationError):
            self.homecontrol.devices[self.devices.get("ambiguous_2").get("uid")]\
                .binary_switch_property[self.devices.get("ambiguous_2").get("elementUIDs")[1]].set_binary_switch(True)

    @pytest.mark.usefixtures("mock_mprmrest__post_set")
    def test_set_binary_switch_same(self, mocker):
        spy = mocker.spy(self.homecontrol.devices[self.devices.get("ambiguous_2").get("uid")]
                         .binary_switch_property.get(self.devices.get("ambiguous_2").get("elementUIDs")[1])._logger, "info")
        self.homecontrol.devices[self.devices.get("ambiguous_2").get("uid")].status = 2
        self.homecontrol.devices[self.devices.get("ambiguous_2").get("uid")] \
            .binary_switch_property[self.devices.get("ambiguous_2").get("elementUIDs")[1]].set_binary_switch(True)
        assert spy.call_count == 2
