import pytest
import zeroconf
from requests.exceptions import ConnectTimeout

from devolo_home_control_api.exceptions.gateway import GatewayOfflineError


@pytest.mark.usefixtures("mprm_instance")
class TestMprm:
    @pytest.mark.usefixtures("mock_mprm_get_local_session")
    def test_create_connection_local(self, mprm_session):
        self.mprm._session = mprm_session
        self.mprm._local_ip = self.gateway.get("local_ip")
        self.mprm.create_connection()

    @pytest.mark.usefixtures("mock_mprmwebsocket_get_remote_session")
    @pytest.mark.usefixtures("mock_session_get")
    def test_create_connection_remote(self, mprm_session, mydevolo):
        self.mprm._session = mprm_session
        self.mprm.gateway.external_access = True
        self._mydevolo = mydevolo
        self.mprm.create_connection()

    def test_create_connection_invalid(self):
        with pytest.raises(ConnectionError):
            self.mprm.gateway.external_access = False
            self.mprm.create_connection()

    @pytest.mark.usefixtures("mock_mprm_service_browser")
    def test_detect_gateway_in_lan(self):
        self.mprm._local_ip = self.gateway.get("local_ip")
        assert self.mprm.detect_gateway_in_lan("zeroconf") == self.gateway.get("local_ip")

    @pytest.mark.usefixtures("mock_session_get")
    @pytest.mark.usefixtures("mock_response_json")
    def test_get_local_session_valid(self, mprm_session):
        self.mprm._session = mprm_session
        self.mprm._local_ip = self.gateway.get("local_ip")
        self.mprm.get_local_session()

    @pytest.mark.usefixtures("mock_response_requests_ConnectTimeout")
    def test_get_local_session_ConnectTimeout(self, mprm_session):
        self.mprm._session = mprm_session
        self.mprm._local_ip = self.gateway.get("local_ip")
        with pytest.raises(ConnectTimeout):
            self.mprm.get_local_session()

    @pytest.mark.usefixtures("mock_response_json_JSONDecodeError")
    def test_get_local_session_JSONDecodeError(self, mprm_session):
        self.mprm._session = mprm_session
        self.mprm._local_ip = self.gateway.get("local_ip")
        with pytest.raises(GatewayOfflineError):
            self.mprm.get_local_session()

    @pytest.mark.usefixtures("mock_response_json_JSONDecodeError")
    def test_get_remote_session_JSONDecodeError(self, mprm_session):
        self.mprm._session = mprm_session
        with pytest.raises(GatewayOfflineError):
            self.mprm.get_remote_session()

    @pytest.mark.usefixtures("mock_mprm_service_browser")
    @pytest.mark.usefixtures("mock_mprm__try_local_connection")
    def test__on_service_state_change(self):
        zc = zeroconf.Zeroconf()
        service_type = "_http._tcp.local."
        self.mprm._on_service_state_change(zc, service_type, service_type, zeroconf.ServiceStateChange.Added)
        assert self.mprm._local_ip == self.gateway.get("local_ip")

    @pytest.mark.usefixtures("mock_socket_inet_ntoa")
    @pytest.mark.usefixtures("mock_response_valid")
    def test__try_local_connection_success(self, mprm_session):
        self.mprm._session = mprm_session
        self.mprm._try_local_connection([self.gateway.get("local_ip")])
        assert self.mprm._local_ip == self.gateway.get("local_ip")
