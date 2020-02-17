from devolo_home_control_api.publisher.publisher import Publisher
import pytest


@pytest.mark.usefixtures("mock_inspect_devices_metering_plug")
@pytest.mark.usefixtures("home_control_instance")
class TestPublisher:

    def test_register_unregister(self):
        for device in self.homecontrol.devices:
            self.homecontrol.devices[device].subscriber = Subscriber(device)
            self.homecontrol.mprm.publisher.register(device, self.homecontrol.devices[device].subscriber)
            assert len(self.homecontrol.publisher._get_subscribers_for_specific_event(device)) == 1
        for device in self.homecontrol.devices:
            self.homecontrol.mprm.publisher.unregister(device, self.homecontrol.devices[device].subscriber)
            assert len(self.homecontrol.publisher._get_subscribers_for_specific_event(device)) == 0


class Subscriber:
    def __init__(self, name):
        self.name = name

    def update(self, message):
        print(f'{self.name} got message "{message}"')