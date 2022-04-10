import json
import pathlib

from devolo_home_control_api.mydevolo import Mydevolo


class MockGateway:
    def __init__(self, gateway_id: str, mydevolo: Mydevolo):
        file = pathlib.Path(__file__).parent / ".." / "test_data.json"
        with file.open("r") as fh:
            test_data = json.load(fh)

        self.id = gateway_id
        self.name = test_data.get("gateway").get("name")
        self.role = test_data.get("gateway").get("role")
        self.local_user = test_data.get("user").get("uuid")
        self.local_passkey = test_data.get("gateway").get("local_passkey")
        self.full_url = test_data.get("gateway").get("full_url")
        self.external_access = test_data.get("gateway").get("external_access")
        self.status = test_data.get("gateway").get("status")
        self.state = test_data.get("gateway").get("state")
        self.firmware_version = test_data.get("gateway").get("firmware_version")
        self.online = True
        self.zones = test_data.get("gateway").get("zones")

    def update_state(self, online: bool):
        self.online = online
