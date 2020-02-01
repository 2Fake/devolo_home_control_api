import json


class Gateway:
    """ Represent a gateway in tests """

    def __init__(self, gateway_id: str):
        with open('test_data.json') as file:
            test_data = json.load(file)

        self.id = gateway_id
        self.name = test_data.get("gateway").get("name")
        self.role = test_data.get("gateway").get("role")
        self.local_user = test_data.get("user").get("uuid")
        self.local_passkey = test_data.get("gateway").get("local_passkey")
        self._full_url = test_data.get("gateway").get("full_url")
        self.external_access = test_data.get("gateway").get("external_access")
        self.status = test_data.get("gateway").get("status")
        self.state = test_data.get("gateway").get("state")
        self.firmware_version = test_data.get("gateway").get("firmware_version")
