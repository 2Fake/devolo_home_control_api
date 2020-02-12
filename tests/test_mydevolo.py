import pytest

from devolo_home_control_api.mydevolo import Mydevolo


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
