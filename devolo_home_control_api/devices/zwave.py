import logging


class Zwave:
    def __init__(self, name, device_uid):
        self._logger = logging.getLogger(self.__class__.__name__)
        self.name = name
        self.device_uid = device_uid
        self.subscriber = None
