class MprmDeviceCommunicationError(Exception):
    """ Communicating to a device via mPRM failed """


class MprmDeviceNotFoundError(Exception):
    """ A device like this was not found """


class WrongElementError(Exception):
    """ This element was not meant for this property. """
