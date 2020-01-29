import pytest

from devolo_home_control_api.mydevolo import Mydevolo


class TestMydevolo:

    def test_gateway_ids(self, mock_mydevolo__call):
        mydevolo = Mydevolo.get_instance()
        mydevolo._uuid = self.uuid

        assert mydevolo.gateway_ids == [self.gateway_id]

    def test_gateway_ids_empty(self, mock_mydevolo__call):
        mydevolo = Mydevolo.get_instance()
        mydevolo._uuid = self.uuid

        with pytest.raises(IndexError):
            mydevolo.gateway_ids

    def test_get_full_url(self, mock_mydevolo__call):

        mydevolo = Mydevolo.get_instance()
        mydevolo._uuid = self.uuid

        full_url = mydevolo.get_full_url(self.gateway_id)

        assert full_url == self.full_url

    def test_get_gateway(self, mock_mydevolo__call):
        mydevolo = Mydevolo.get_instance()
        mydevolo._uuid = self.uuid

        details = mydevolo.get_gateway(self.gateway_id)

        assert details.get("gatewayId") == self.gateway_id

    def test_set_password(self):
        mydevolo = Mydevolo.get_instance()
        mydevolo._uuid = self.uuid
        mydevolo._gateway_ids = [self.gateway_id]

        mydevolo.password = self.password

        assert mydevolo._uuid is None
        assert mydevolo._gateway_ids == []

    def test_set_user(self):
        mydevolo = Mydevolo.get_instance()
        mydevolo._uuid = self.uuid
        mydevolo._gateway_ids = [self.gateway_id]

        mydevolo.user = self.user

        assert mydevolo._uuid is None
        assert mydevolo._gateway_ids == []

    def test_singleton_mydevolo(self):
        Mydevolo.get_instance()

        with pytest.raises(SyntaxError):
            Mydevolo()

    def test_uuid(self, mock_mydevolo__call):
        mydevolo = Mydevolo.get_instance()
        assert mydevolo.uuid == self.uuid
