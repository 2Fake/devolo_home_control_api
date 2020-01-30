import pytest

from devolo_home_control_api.mprm_rest import MprmRest


@pytest.mark.usefixtures("mprm_instance")
@pytest.mark.usefixtures("mock_mprmrest__extract_data_from_element_uid")
class TestMprmRest:
    def test_binary_switch_devices(self):
        assert hasattr(self.mprm.binary_switch_devices[0], "binary_switch_property")

    def test_get_binary_switch_state_invalid(self):
        with pytest.raises(ValueError):
            self.mprm.get_binary_switch_state("invalid")

    def test_get_binary_switch_state_valid_on(self):
        assert self.mprm.get_binary_switch_state(element_uid=f"devolo.BinarySwitch:{self.device_uid}")

    def test_get_binary_switch_state_valid_off(self):
        assert not self.mprm.get_binary_switch_state(element_uid=f"devolo.BinarySwitch:{self.device_uid}")

    def test_get_consumption_invalid(self):
        with pytest.raises(ValueError):
            self.mprm.get_consumption("invalid", "invalid")
        with pytest.raises(ValueError):
            self.mprm.get_consumption("devolo.Meter:", "invalid")

    def test_get_consumption_valid(self):
        pass

    def test_get_voltage_invalid(self):
        with pytest.raises(ValueError):
            self.mprm.get_voltage("invalid")
