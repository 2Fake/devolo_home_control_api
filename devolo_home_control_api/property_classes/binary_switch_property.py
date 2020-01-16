from property_classes.property import Property


class BinarySwitchProperty(Property):
    def __init__(self, element_uid):
        super().__init__(element_uid=element_uid)
        self._state = None

    def get_state(self):
        return self._state

    def set_state(self, state: bool):
        self._state = state
