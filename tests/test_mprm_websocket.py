import pytest


@pytest.mark.usefixtures("mprm_instance")
@pytest.mark.usefixtures("mock_mprmrest__extract_data_from_element_uid")
class TestMprmWebsocket:
    def test_get_consumption_invalid(self):
        with pytest.raises(ValueError):
            self.mprm.get_consumption("invalid", "invalid")
        with pytest.raises(ValueError):
            self.mprm.get_consumption("devolo.Meter:", "invalid")
