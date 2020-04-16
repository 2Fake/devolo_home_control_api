import pytest

from devolo_home_control_api.backend.mprm_rest import MprmDeviceCommunicationError


@pytest.mark.usefixtures("mprm_instance")
class TestMprmRest:

    def test_get_name_and_element_uids(self, mock_mprmrest__extract_data_from_element_uid, mock_mprmrest__post):
        properties = self.mprm.get_name_and_element_uids("test")
        assert properties == {"itemName": "test_name",
                              "zone": "test_zone",
                              "batteryLevel": "test_battery",
                              "icon": "test_icon",
                              "elementUIDs": "test_element_uids",
                              "settingUIDs": "test_setting_uids",
                              "deviceModelUID": "test_device_model_uid",
                              "status": "test_status"}

    @pytest.mark.usefixtures("mock_mprmrest__post")
    def test_get_all_devices(self):
        devices = self.mprm.get_all_devices()
        assert devices == "deviceUIDs"

    @pytest.mark.usefixtures("mock_response_requests_ReadTimeout")
    def test_post_ReadTimeOut(self, mprm_session, gateway_instance):
        self.mprm._session = mprm_session
        self.mprm._gateway = gateway_instance
        with pytest.raises(MprmDeviceCommunicationError):
            self.mprm.post({"data": "test"})

    @pytest.mark.usefixtures("mock_response_requests_ReadTimeout")
    def test_post_gateway_offline(self, mprm_session, gateway_instance):
        self.mprm._session = mprm_session
        self.mprm._gateway = gateway_instance
        self.mprm._gateway.online = False
        self.mprm._gateway.sync = False
        self.mprm._gateway.local_connection = False
        with pytest.raises(MprmDeviceCommunicationError):
            self.mprm.post({"data": "test"})

    @pytest.mark.usefixtures("mock_response_requests_invalid_id")
    def test_post_invalid_id(self, mprm_session):
        self.mprm._session = mprm_session
        self.mprm._data_id = 0
        with pytest.raises(ValueError):
            self.mprm.post({"data": "test"})

    @pytest.mark.usefixtures("mock_response_requests_valid")
    def test_post_valid(self, mprm_session):
        self.mprm._session = mprm_session
        self.mprm._data_id = 1
        assert self.mprm.post({"data": "test"}).get("id") == 2

    def test_get_data_from_uid_list(self, mock_mprmrest__post):
        properties = self.mprm.get_data_from_uid_list(["test"])
        assert properties[0].get("properties").get("itemName") == "test_name"
