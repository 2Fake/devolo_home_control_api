import pytest


@pytest.mark.usefixtures("mock_inspect_devices_metering_plug")
@pytest.mark.usefixtures("home_control_instance")
class TestPublisher:

    def test_register_unregister(self):
        for device in self.homecontrol.devices:
            self.homecontrol.devices[device].subscriber = Subscriber(device)
            self.homecontrol.publisher.register(device, self.homecontrol.devices[device].subscriber)
            assert len(self.homecontrol.publisher._get_subscribers_for_specific_event(device)) == 1
        for device in self.homecontrol.devices:
            self.homecontrol.publisher.unregister(device, self.homecontrol.devices[device].subscriber)
            assert len(self.homecontrol.publisher._get_subscribers_for_specific_event(device)) == 0

    def test_dispatch(self):
        for device in self.homecontrol.devices:
            self.homecontrol.devices[device].subscriber = Subscriber(device)
            self.homecontrol.publisher.register(device, self.homecontrol.devices[device].subscriber)
        with pytest.raises(FileExistsError):
            self.homecontrol.publisher.dispatch(event="hdm:ZWave:F6BF9812/4", message=())



class Subscriber:
    def __init__(self, name):
        self.name = name

    def update(self, message):
        # We raise an error here so we can check for it in the test case.
        raise FileExistsError
