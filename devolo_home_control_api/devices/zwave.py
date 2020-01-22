import logging


class Zwave:
    def __init__(self, name, fim_uid):
        self._logger = logging.getLogger(self.__class__.__name__)
        self.name = name
        self.fim_uid = fim_uid
        self.subscriber = None
