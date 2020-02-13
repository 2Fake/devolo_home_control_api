import pytest

from devolo_home_control_api.backend.mprm_rest import MprmRest, \
    MprmDeviceCommunicationError, \
    MprmDeviceNotFoundError, \
    get_sub_device_uid_from_element_uid, \
    get_device_type_from_element_uid


@pytest.mark.usefixtures("mprm_instance")
@pytest.mark.usefixtures("mock_mprmrest__extract_data_from_element_uid")
@pytest.mark.usefixtures("mock_mydevolo__call")
class TestMprmRest:

    def test_singleton(self):
        MprmRest.del_instance()

        with pytest.raises(SyntaxError):
            MprmRest.get_instance()

        first = MprmRest(gateway_id=self.gateway.get("id"), url="https://homecontrol.mydevolo.com")
        with pytest.raises(SyntaxError):
            MprmRest(gateway_id=self.gateway.get("id"), url="https://homecontrol.mydevolo.com")

        second = MprmRest.get_instance()
        assert first is second


    @pytest.mark.usefixtures("mock_mprmrest__post")
    def test_get_name_and_element_uids(self):
        name, zone, battery_level, icon, element_uids, setting_uids, deviceModelUID, online_state = \
            self.mprm.get_name_and_element_uids("test")
        assert name == "test_name"
        assert zone == "test_zone"
        assert battery_level == "test_battery"
        assert icon == "test_icon"
        assert element_uids == "test_element_uids"
        assert setting_uids == "test_setting_uids"
        assert deviceModelUID == "test_device_model_uid"
        assert online_state == "test_status"

    def test_get_sub_device_uid_from_element_uid(self):
        assert get_sub_device_uid_from_element_uid("devolo.Meter:hdm:ZWave:F6BF9812/2#2") == 2
        assert get_sub_device_uid_from_element_uid("devolo.Meter:hdm:ZWave:F6BF9812/2") is None

    def test_get_device_type_from_element_uid(self):
        assert get_device_type_from_element_uid("devolo.Meter:hdm:ZWave:F6BF9812/2#2") == "devolo.Meter"
