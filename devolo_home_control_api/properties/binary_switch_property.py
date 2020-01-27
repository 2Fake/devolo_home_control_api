from .property import Property, WrongElementError


class BinarySwitchProperty(Property):
    """
    Object for binary switches. It stores the binary switch state.

    :param element_uid: Element UID, something like devolo.BinarySwitch:hdm:ZWave:CBC56091/24#2
    """

    def __init__(self, element_uid):
        if not element_uid.startswith("devolo.BinarySwitch:"):
            raise WrongElementError(f"{element_uid} is not a Binary Switch.")

        super().__init__(element_uid=element_uid)
        self.state = None
