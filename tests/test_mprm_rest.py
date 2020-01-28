import pytest

from devolo_home_control_api.mprm_rest import MprmRest
from .mock_gateway import Gateway


class TestMprmRest:
    def test_binary_switch_devices(self, mock_gateway):
        mprm = MprmRest("1409301750000598")
        print(mprm._gateway)