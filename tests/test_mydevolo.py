"""Test mydevolo."""
import pytest

from devolo_home_control_api.mydevolo import GatewayOfflineError, Mydevolo, WrongCredentialsError, WrongUrlError


class TestMydevolo:
    def test_credentials_valid(self, mydevolo: Mydevolo) -> None:
        """Test credential validation."""
        assert mydevolo.credentials_valid()

    @pytest.mark.usefixtures("mock_mydevolo_uuid_raise_WrongCredentialsError")
    def test_credentials_invalid(self, mydevolo: Mydevolo) -> None:
        """Test credential validation."""
        assert not mydevolo.credentials_valid()

    @pytest.mark.usefixtures("mock_mydevolo__call")
    def test_gateway_ids(self, mydevolo: Mydevolo) -> None:
        """Test getting gateway serial numbers."""
        assert mydevolo.get_gateway_ids() == [self.gateway["id"]]

    @pytest.mark.usefixtures("mock_mydevolo__call")
    def test_gateway_ids_empty(self, mydevolo: Mydevolo) -> None:
        """Test raising on empty gateway list."""
        with pytest.raises(IndexError):
            mydevolo.get_gateway_ids()

    @pytest.mark.usefixtures("mock_mydevolo__call")
    def test_get_full_url(self, mydevolo: Mydevolo) -> None:
        """Test getting the remote mPRM URL."""
        full_url = mydevolo.get_full_url(self.gateway["id"])
        assert full_url == self.gateway["full_url"]

    @pytest.mark.usefixtures("mock_mydevolo__call")
    def test_get_gateway(self, mydevolo: Mydevolo) -> None:
        """Test getting gateway details."""
        details = mydevolo.get_gateway(self.gateway["id"])
        assert details.get("gatewayId") == self.gateway["id"]

    @pytest.mark.usefixtures("mock_mydevolo__call_raise_WrongUrlError")
    def test_get_gateway_invalid(self, mydevolo: Mydevolo) -> None:
        """Test raising on wrong gateway serial number."""
        with pytest.raises(WrongUrlError):
            mydevolo.get_gateway(self.gateway["id"])

    @pytest.mark.usefixtures("mock_mydevolo__call")
    def test_get_zwave_products(self, mydevolo: Mydevolo) -> None:
        """Test getting Z-Wave product information."""
        device_info = mydevolo.get_zwave_products(manufacturer="0x0060", product_type="0x0001", product="0x000")
        assert device_info.get("name") == "Everspring PIR Sensor SP814"

    @pytest.mark.usefixtures("mock_mydevolo__call_raise_WrongUrlError")
    def test_get_zwave_products_invalid(self, mydevolo: Mydevolo) -> None:
        """Test handling unknown Z-wave products."""
        device_info = mydevolo.get_zwave_products(manufacturer="0x0070", product_type="0x0001", product="0x000")
        assert device_info.get("name") == "Unknown"

    @pytest.mark.usefixtures("mock_mydevolo__call")
    @pytest.mark.parametrize("result", [True, False])
    def test_maintenance(self, mydevolo: Mydevolo, result: bool) -> None:
        """Test checking for maintenance mode."""
        assert mydevolo.maintenance() == result

    def test_set_password(self, mydevolo: Mydevolo) -> None:
        """Test setting a new password."""
        mydevolo._gateway_ids = [self.gateway["id"]]
        mydevolo.password = self.user["password"]
        assert mydevolo.uuid.cache_clear.call_count == 1
        assert mydevolo._gateway_ids == []

    def test_set_user(self, mydevolo: Mydevolo) -> None:
        """Test setting a new username."""
        mydevolo._gateway_ids = [self.gateway["id"]]
        mydevolo.user = self.user["username"]
        assert mydevolo.uuid.cache_clear.call_count == 1
        assert mydevolo._gateway_ids == []

    def test_get_user(self, mydevolo: Mydevolo) -> None:
        """Test getting the username."""
        mydevolo.user = self.user["username"]
        assert mydevolo.user == self.user["username"]

    def test_get_password(self, mydevolo: Mydevolo) -> None:
        """Test getting the password."""
        mydevolo.password = self.user["password"]
        assert mydevolo.password == self.user["password"]

    @pytest.mark.usefixtures("mock_mydevolo__call")
    def test_uuid(self) -> None:
        """Test getting the uuid."""
        mydevolo = Mydevolo()
        assert mydevolo.uuid() == self.user["uuid"]
        assert mydevolo.uuid() == self.user["uuid"]
        assert mydevolo.uuid.cache_info().hits == 1

    @pytest.mark.usefixtures("mock_response_wrong_credentials_error")
    def test_call_WrongCredentialsError(self) -> None:
        """Test raising on wrong credentials."""
        mydevolo = Mydevolo()
        with pytest.raises(WrongCredentialsError):
            mydevolo._call("test")

    @pytest.mark.usefixtures("mock_response_wrong_url_error")
    def test_call_WrongUrlError(self) -> None:
        """Test raising on wrong URL."""
        mydevolo = Mydevolo()
        with pytest.raises(WrongUrlError):
            mydevolo._call("test")

    @pytest.mark.usefixtures("mock_response_gateway_offline")
    def test_call_GatewayOfflineError(self, mydevolo: Mydevolo) -> None:
        """Test raising on offline gateway."""
        with pytest.raises(GatewayOfflineError):
            mydevolo._call("test")

    @pytest.mark.usefixtures("mock_response_valid")
    def test_call_valid(self, mydevolo: Mydevolo) -> None:
        """Test valid calls."""
        assert mydevolo._call("test").get("response") == "response"
