import json
import pathlib

file = pathlib.Path(__file__).parent / ".." / "test_data.json"
with file.open("r") as fh:
    test_data = json.load(fh)


def try_local_connection(self, mdns_name):
    self._local_ip = test_data["gateway"]["local_ip"]


def mock_get_data_from_uid_list(self, uids):
    if len(uids) == 1:
        return [test_data["devices"]["mains"]]
    else:
        return [
            {
                "UID": test_data["devices"]["mains"]["settingUIDs"][0],
                "properties": {"settings": test_data["devices"]["mains"]["properties"]},
            }
        ]
