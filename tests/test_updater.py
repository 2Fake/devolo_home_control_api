# import pytest
# from devolo_home_control_api.publisher.updater import Updater
#
# @pytest.mark.usefixtures("home_control_instance")
# @pytest.mark.usefixtures("mock_mprmrest__extract_data_from_element_uid")
# @pytest.mark.usefixtures("mock_mydevolo__call")
# class TestUpdater:
#     def test_update_binary_switch_state_valid(self, fill_device_data):
#         binary_switch_property = self.homecontrol.devices.get(self.devices.get("mains").get("uid")).binary_switch_property
#         state = binary_switch_property.get(f"devolo.BinarySwitch:{self.devices.get('mains').get('uid')}").state
#         self.mprm.update_binary_switch_state(f"devolo.BinarySwitch:{self.devices.get('mains').get('uid')}", value=True)
#         assert state != binary_switch_property.get(f"devolo.BinarySwitch:{self.devices.get('mains').get('uid')}").state
