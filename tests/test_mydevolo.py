import pytest

from devolo_home_control_api.mydevolo import Mydevolo, WrongUrlError, WrongCredentialsError


class TestMydevolo:
    def test_gateway_ids(self, mydevolo, mock_mydevolo__call):
        assert mydevolo.gateway_ids == [self.gateway.get("id")]

    def test_gateway_ids_empty(self, mydevolo, mock_mydevolo__call):
        with pytest.raises(IndexError):
            mydevolo.gateway_ids

    def test_get_full_url(self, mydevolo, mock_mydevolo__call):
        full_url = mydevolo.get_full_url(self.gateway.get("id"))
        assert full_url == self.gateway.get("full_url")

    def test_get_gateway(self, mydevolo, mock_mydevolo__call):
        details = mydevolo.get_gateway(self.gateway.get("id"))
        assert details.get("gatewayId") == self.gateway.get("id")

    def test_get_gateway_invalid(self, mydevolo, mock_mydevolo__call_raise_WrongUrlError):
        with pytest.raises(WrongUrlError):
            mydevolo.get_gateway(self.gateway.get("id"))

    def test_get_zwave_products(self, mydevolo, mock_mydevolo__call):
        product = mydevolo.get_zwave_products(manufacturer="0x0060", product_type="0x0001", product="0x000")
        assert product.get("name") == "Everspring PIR Sensor SP814"

    def test_get_zwave_products_invalid(self, mydevolo, mock_mydevolo__call_raise_WrongUrlError):
        device_infos = mydevolo.get_zwave_products(manufacturer="0x0070", product_type="0x0001", product="0x000")
        assert len(device_infos) == 0

    def test_maintenance_on(self, mydevolo, mock_mydevolo__call):
        assert not mydevolo.maintenance

    def test_maintenance_off(self, mydevolo, mock_mydevolo__call):
        assert mydevolo.maintenance

    def test_set_password(self, mydevolo):
        mydevolo._gateway_ids = [self.gateway.get("id")]

        mydevolo.password = self.user.get("password")

        assert mydevolo._uuid is None
        assert mydevolo._gateway_ids == []

    def test_set_user(self, mydevolo):
        mydevolo._gateway_ids = [self.gateway.get("id")]

        mydevolo.user = self.user.get("username")

        assert mydevolo._uuid is None
        assert mydevolo._gateway_ids == []

    def test_get_user(self, mydevolo):
        mydevolo.user = self.user.get("username")
        assert mydevolo.user == self.user.get("username")

    def test_get_password(self, mydevolo):
        mydevolo.password = self.user.get("password")
        assert mydevolo.password == self.user.get("password")

    def test_singleton_mydevolo(self):
        with pytest.raises(SyntaxError):
            Mydevolo.get_instance()

        first = Mydevolo()
        with pytest.raises(SyntaxError):
            Mydevolo()

        second = Mydevolo.get_instance()
        assert first is second
        Mydevolo.del_instance()

    def test_uuid(self, mydevolo, mock_mydevolo__call):
        mydevolo._uuid = None
        assert mydevolo.uuid == self.user.get("uuid")

    def test_call_WrongCredentialsError(self, mock_response_wrong_credentials_error):
        mydevolo = Mydevolo()
        with pytest.raises(WrongCredentialsError):
            mydevolo._call("test")
        Mydevolo.del_instance()

    def test_call_WrongUrlError(self, mock_response_wrong_url_error):
        mydevolo = Mydevolo()
        with pytest.raises(WrongUrlError):
            mydevolo._call("test")
        Mydevolo.del_instance()

    def test_call_valid(self, mydevolo, mock_response_valid):
        assert mydevolo._call("test").get("response") == "response"
