import pytest
from devolo_home_control_api.exceptions.gateway import GatewayOfflineError


@pytest.mark.usefixtures("mprm_instance")
class TestMprmRest:
    @pytest.mark.usefixtures("mock_mprmrest__post")
    def test_get_name_and_element_uids(self):
        properties = self.mprm.get_name_and_element_uids("test")
        assert properties == {
            "itemName": "test_name",
            "zone": "test_zone",
            "batteryLevel": "test_battery",
            "icon": "test_icon",
            "elementUIDs": "test_element_uids",
            "settingUIDs": "test_setting_uids",
            "deviceModelUID": "test_device_model_uid",
            "status": "test_status",
        }

    @pytest.mark.usefixtures("mock_mprmrest__post")
    def test_get_all_devices(self):
        devices = self.mprm.get_all_devices()
        assert devices == "deviceUIDs"

    @pytest.mark.usefixtures("mock_mprmrest__post")
    def test_get_all_zones(self):
        zones = self.mprm.get_all_zones()
        assert zones == {
            "hz_3": "Office",
        }

    @pytest.mark.usefixtures("mock_response_requests_ReadTimeout")
    def test_post_ReadTimeOut(self, mprm_session, gateway_instance):
        self.mprm._session = mprm_session
        self.mprm.gateway = gateway_instance
        with pytest.raises(GatewayOfflineError):
            self.mprm._post({"data": "test"})

    @pytest.mark.usefixtures("mock_response_requests_invalid_id")
    def test_post_invalid_id(self, mprm_session):
        self.mprm._session = mprm_session
        self.mprm._data_id = 0
        with pytest.raises(ValueError):
            self.mprm._post({"data": "test"})

    @pytest.mark.usefixtures("mock_response_requests_valid")
    def test_post_valid(self, mprm_session):
        self.mprm._session = mprm_session
        self.mprm._data_id = 1
        assert self.mprm._post({"data": "test"}).get("id") == 2

    @pytest.mark.usefixtures("mock_mprmrest__post")
    @pytest.mark.parametrize(
        "setter",
        [
            ("set_binary_switch"),
            ("set_multi_level_switch"),
            ("set_remote_control"),
            ("set_setting"),
        ],
    )
    def test_set_success(self, setter):
        test_data = {
            "set_binary_switch": bool(self.devices["mains"]["properties"]["state"]),
            "set_multi_level_switch": self.devices["multi_level_switch"]["value"],
            "set_remote_control": 1,
            "set_setting": self.devices["mains"]["properties"]["local_switch"],
        }
        assert getattr(self.mprm, setter)(self.devices["mains"]["properties"]["elementUIDs"][1], test_data[setter])

    @pytest.mark.usefixtures("mock_mprmrest__post")
    @pytest.mark.parametrize("setter", [("set_binary_switch"), ("set_multi_level_switch")])
    def test_set_doubled(self, setter):
        assert not getattr(self.mprm, setter)(
            self.devices["mains"]["properties"]["elementUIDs"][1], bool(self.devices["mains"]["properties"]["state"])
        )

    @pytest.mark.usefixtures("mock_mprmrest__post")
    @pytest.mark.parametrize(
        "setter",
        [
            ("set_binary_switch"),
            ("set_multi_level_switch"),
            ("set_remote_control"),
            ("set_setting"),
        ],
    )
    def test_set_failed(self, setter):
        assert not getattr(self.mprm, setter)(
            self.devices["mains"]["properties"]["elementUIDs"][1], bool(self.devices["mains"]["properties"]["state"])
        )

    @pytest.mark.usefixtures("mock_mprmrest__post")
    def test_get_data_from_uid_list(self):
        properties = self.mprm.get_data_from_uid_list(["test"])
        assert properties[0].get("properties").get("itemName") == "test_name"
