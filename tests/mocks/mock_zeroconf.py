import json
import pathlib

from zeroconf import ServiceInfo

file = pathlib.Path(__file__).parent / ".." / "test_data.json"
with file.open("r") as fh:
    test_data = json.load(fh)


class Zeroconf:
    def get_service_info(self, service_type, name):
        service_info = ServiceInfo(service_type, name)
        service_info.server = "devolo-homecontrol.local"
        return service_info
