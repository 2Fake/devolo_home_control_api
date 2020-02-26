import pytest
from requests import ConnectTimeout

from devolo_home_control_api.backend.mprm_rest import MprmDeviceCommunicationError, MprmRest
from devolo_home_control_api.mydevolo import Mydevolo

from .mocks.mock_dnsrecord import MockDNSRecord


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

    def test_singleton(self):
        MprmRest.del_instance()

        with pytest.raises(SyntaxError):
            MprmRest.get_instance()

        first = MprmRest(gateway_id=self.gateway.get("id"), url="https://homecontrol.mydevolo.com")
        with pytest.raises(SyntaxError):
            MprmRest(gateway_id=self.gateway.get("id"), url="https://homecontrol.mydevolo.com")

        second = MprmRest.get_instance()
        assert first is second

    def test_create_connection_local(self, mock_mprmrest_get_local_session):
        self.mprm._local_ip = self.gateway.get("local_ip")
        self.mprm.create_connection()

    def test_create_connection_remote(self, mock_mprmrest_get_remote_session, mydevolo):
        self.mprm._gateway.external_access = True
        self._mydevolo = Mydevolo.get_instance()
        self.mprm.create_connection()

    def test_create_connection_invalid(self):
        with pytest.raises(ConnectionError):
            self.mprm._gateway.external_access = False
            self.mprm.create_connection()

    def test_detect_gateway_in_lan(self, mock_mprmrest_zeroconf_cache_entries, mock_mprmrest__try_local_connection):
        assert self.mprm.detect_gateway_in_lan() == self.gateway.get("local_ip")

    def test_extract_data_from_element_uid(self, mock_mprmrest__post):
        properties = self.mprm.extract_data_from_element_uid(uid="test")
        assert properties.get("properties").get("itemName") == "test_name"

    def test_get_all_devices(self, mock_mprmrest__post):
        devices = self.mprm.get_all_devices()
        assert devices == "deviceUIDs"

    @pytest.mark.usefixtures("mock_session_get")
    @pytest.mark.usefixtures("mock_response_json")
    def test_get_local_session_valid(self):
        self.mprm._local_ip = self.gateway.get("local_ip")
        self.mprm.get_local_session()

    @pytest.mark.usefixtures("mock_response_requests_ConnectTimeout")
    def test_get_local_session_ConnectTimeout(self):
        self.mprm._local_ip = self.gateway.get("local_ip")
        with pytest.raises(ConnectTimeout):
            self.mprm.get_local_session()

    @pytest.mark.usefixtures("mock_response_json_JSONDecodeError")
    def test_get_local_session_JSONDecodeError(self):
        self.mprm._local_ip = self.gateway.get("local_ip")
        with pytest.raises(MprmDeviceCommunicationError):
            self.mprm.get_local_session()

    @pytest.mark.usefixtures("mock_response_json_JSONDecodeError")
    def test_get_remote_session_JSONDecodeError(self):
        with pytest.raises(MprmDeviceCommunicationError):
            self.mprm.get_remote_session()

    @pytest.mark.usefixtures("mock_response_requests_ReadTimeout")
    def test_post_ReadTimeOut(self):
        with pytest.raises(MprmDeviceCommunicationError):
            self.mprm.post({"data": "test"})

    def test_post_gateway_offline(self):
        self.mprm._gateway.online = False
        self.mprm._gateway.sync = False
        self.mprm._gateway.local_connection = False
        with pytest.raises(MprmDeviceCommunicationError):
            self.mprm.post({"data": "test"})

    @pytest.mark.usefixtures("mock_response_requests_invalid_id")
    def test_post_invalid_id(self):
        self.mprm._data_id = 0
        with pytest.raises(ValueError):
            self.mprm.post({"data": "test"})

    def test_post_valid(self, mock_response_requests_valid):
        self.mprm._data_id = 1
        assert self.mprm.post({"data": "test"}).get("id") == 2

    def test__try_local_connection_success(self, mock_socket_inet_ntoa, mock_response_valid):
        mdns_name = MockDNSRecord()
        mdns_name.address = self.gateway.get("local_ip")
        self.mprm._try_local_connection(mdns_name)
        assert self.mprm._local_ip == self.gateway.get("local_ip")
