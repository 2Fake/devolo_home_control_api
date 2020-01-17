from ..property_classes.binary_switch_property import BinarySwitchProperty
from ..property_classes.consumption_property import ConsumptionProperty
from .device import Device


class BinarySwitchDevice(Device):
    def __init__(self, name, fim_uid, element_uids):
        super().__init__(name=name, fim_uid=fim_uid)
        self.consumption_property = {}
        self.binary_switch_property = {}

        for element_uid in element_uids:
            self._logger.debug(f"Handling element UID: {element_uid}")
            if element_uid.startswith('devolo.Meter'):
                self.consumption_property[element_uid] = ConsumptionProperty(element_uid=element_uid)
            elif element_uid.startswith('devolo.BinarySwitch'):
                self.binary_switch_property[element_uid] = BinarySwitchProperty(element_uid=element_uid)
            else:
                self._logger.info(f"Found an unexpected element UID: {element_uid}")
                self._logger.info("This element UID will be ignored for now.")

        if len(self.consumption_property) == 0:
            del self.consumption_property
        if len(self.binary_switch_property) == 0:
            raise TypeError("Created a binary switch device without binary switch.")
