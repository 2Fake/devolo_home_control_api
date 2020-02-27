import json


with open('test_data.json') as file:
    test_data = json.load(file)


def try_local_connection(self, mdns_name):
    self._local_ip = test_data.get("gateway").get("local_ip")
