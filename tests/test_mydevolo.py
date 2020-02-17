import pytest

from devolo_home_control_api.mydevolo import Mydevolo, WrongUrlError, WrongCredentialsError


class TestMydevolo:

    def test_gateway_ids(self, mock_mydevolo__call):
        mydevolo = Mydevolo()
        mydevolo._uuid = self.user.get("uuid")

        assert mydevolo.gateway_ids == [self.gateway.get("id")]

    def test_gateway_ids_empty(self, mock_mydevolo__call):
        mydevolo = Mydevolo()
        mydevolo._uuid = self.user.get("uuid")

        with pytest.raises(IndexError):
            mydevolo.gateway_ids

    def test_get_full_url(self, mock_mydevolo__call):

        mydevolo = Mydevolo()
        mydevolo._uuid = self.user.get("uuid")

        full_url = mydevolo.get_full_url(self.gateway.get("id"))

        assert full_url == self.gateway.get("full_url")

    def test_get_gateway(self, mock_mydevolo__call):
        mydevolo = Mydevolo()
        mydevolo._uuid = self.user.get("uuid")

        details = mydevolo.get_gateway(self.gateway.get("id"))

        assert details.get("gatewayId") == self.gateway.get("id")

    @pytest.mark.usefixtures("mock_mydevolo__call")
    def test_get_zwave_products(self):
        mydevolo = Mydevolo()
        mydevolo._uuid = self.user.get("uuid")

        product = mydevolo.get_zwave_products(manufacturer="0x0060", product_type="0x0001", product="0x000")

        assert product.get("name") == "Everspring PIR Sensor SP814"

    @pytest.mark.usefixtures("mock_mydevolo__call_raise_WrongUrlError")
    def test_get_zwave_products_invalid(self):
        mydevolo = Mydevolo()
        mydevolo._uuid = self.user.get("uuid")
        device_infos = mydevolo.get_zwave_products(manufacturer="0x0070", product_type="0x0001", product="0x000")
        assert len(device_infos) == 0

    def test_maintenance_on(self, mock_mydevolo__call):
        mydevolo = Mydevolo()
        assert not mydevolo.maintenance

    def test_maintenance_off(self, mock_mydevolo__call):
        mydevolo = Mydevolo()
        assert mydevolo.maintenance

    def test_set_password(self):
        mydevolo = Mydevolo()
        mydevolo._uuid = self.user.get("uuid")
        mydevolo._gateway_ids = [self.gateway.get("id")]

        mydevolo.password = self.user.get("password")

        assert mydevolo._uuid is None
        assert mydevolo._gateway_ids == []

    def test_set_user(self):
        mydevolo = Mydevolo()
        mydevolo._uuid = self.user.get("uuid")
        mydevolo._gateway_ids = [self.gateway.get("id")]

        mydevolo.user = self.user.get("username")

        assert mydevolo._uuid is None
        assert mydevolo._gateway_ids == []

    def test_get_user(self):
        mydevolo = Mydevolo()
        mydevolo.user = "test_user"
        assert mydevolo.user == "test_user"

    def test_get_password(self):
        mydevolo = Mydevolo()
        mydevolo.password = "test_password"
        assert mydevolo.password == "test_password"

    def test_singleton_mydevolo(self):
        with pytest.raises(SyntaxError):
            Mydevolo.get_instance()

        first = Mydevolo()
        with pytest.raises(SyntaxError):
            Mydevolo()

        second = Mydevolo.get_instance()
        assert first is second

    def test_uuid(self, mock_mydevolo__call):
        mydevolo = Mydevolo()
        assert mydevolo.uuid == self.user.get("uuid")

    @pytest.mark.usefixtures("mock_response_wrong_credentials_error")
    def test_call_WrongCredentialsError(self):
        mydevolo = Mydevolo()
        with pytest.raises(WrongCredentialsError):
            mydevolo._call("test")

    @pytest.mark.usefixtures("mock_response_wrong_url_error")
    def test_call_WrongUrlError(self):
        mydevolo = Mydevolo()
        with pytest.raises(WrongUrlError):
            mydevolo._call("test")


    @pytest.mark.usefixtures("mock_response_valid")
    def test_call_valid(self):
        mydevolo = Mydevolo()
        assert mydevolo._call("test").get("response") == "response"



