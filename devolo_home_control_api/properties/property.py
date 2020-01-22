import logging


class Property:
    def __init__(self, element_uid):
        self._logger = logging.getLogger(self.__class__.__name__)
        self.element_uid = element_uid
