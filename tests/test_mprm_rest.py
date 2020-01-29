import pytest

from devolo_home_control_api.mprm_rest import MprmRest


class TestMprmRest:
    def test_binary_switch_devices(self, mock_gateway, mock_inspect_devices_metering_plug, mock_mprmrest__detect_gateway_in_lan):
        mprm = MprmRest(self.gateway_id)
        assert hasattr(mprm.binary_switch_devices[0], "binary_switch_property")

    def test_get_binary_switch_state_invalid(self, mock_gateway, mock_inspect_devices_metering_plug, mock_mprmrest__detect_gateway_in_lan):
        mprm = MprmRest(self.gateway_id)

        with pytest.raises(ValueError):
            mprm.get_binary_switch_state("invalid")

    def test_get_consumption_invalid(self, mock_gateway, mock_inspect_devices_metering_plug, mock_mprmrest__detect_gateway_in_lan):
        mprm = MprmRest(self.gateway_id)

        with pytest.raises(ValueError):
            mprm.get_consumption("invalid", "invalid")
        with pytest.raises(ValueError):
            mprm.get_consumption("devolo.Meter:", "invalid")

    def test_get_voltage_invalid(self, mock_gateway, mock_inspect_devices_metering_plug, mock_mprmrest__detect_gateway_in_lan):
        mprm = MprmRest(self.gateway_id)

        with pytest.raises(ValueError):
            mprm.get_voltage("invalid")
