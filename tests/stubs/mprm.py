import json
import pathlib

from requests import Session

from devolo_home_control_api.backend.mprm import Mprm
from devolo_home_control_api.mydevolo import Mydevolo

from ..mocks.mock_gateway import MockGateway


class StubMprm(Mprm):
    def __init__(self):
        file = pathlib.Path(__file__).parent / ".." / "test_data.json"
        with file.open("r") as fh:
            test_data = json.load(fh)

        self._mydevolo = Mydevolo()
        self._session = Session()
        self._zeroconf = None
        self.gateway = MockGateway(test_data["gateway"]["id"], self._mydevolo)
        super().__init__()

    def on_update(self, message):
        pass
