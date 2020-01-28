import pytest

from devolo_home_control_api.mprm_rest import MprmRest
from .mock_gateway import Gateway


class TestMprmRest:
    def test_binary_switch_devices(self, mocker):
        mocker.patch('devolo_home_control_api.devices.gateway.Gateway.__init__', Gateway.__init__)
        mprm = MprmRest("1409301750000598")
        print(mprm._gateway)