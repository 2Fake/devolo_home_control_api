from device_classes.device import Device
from property_classes.binary_switch_property import BinarySwitchProperty
from property_classes.consumption_property import ConsumptionProperty


class BinarySwitchDevice(Device):
    def __init__(self, name, fim_uid, element_uids):
        super().__init__(name=name, fim_uid=fim_uid)
        self.consumption_property = []
        self.binary_switch_property = []

        for element_uid in element_uids:
            if element_uid.startswith('devolo.Meter'):
                self.consumption_property.append(ConsumptionProperty(element_uid=element_uid))
            elif element_uid.startswith('devolo.BinarySwitch'):
                self.binary_switch_property.append(BinarySwitchProperty(element_uid=element_uid))
            else:
                pass
                # TODO: Log this!
