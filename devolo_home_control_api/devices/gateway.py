import logging


class Gateway:
    def __init__(self, details: str):
        self._logger = logging.getLogger(self.__class__.__name__)
        self.id = details['gatewayId']
        self.name = details['name']
        self.role = details['role']
        self.local_passkey = details['localPasskey']
        self.external_access = details['externalAccess']
        self.status = details['status']
        self.state = details['state']
        self.firmware_version = details['firmwareVersion']
