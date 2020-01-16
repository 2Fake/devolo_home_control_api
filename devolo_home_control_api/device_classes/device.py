"""
This class is intended to be inherited by every other device class
"""


class Device:
    def __init__(self, name, fim_uid):
        self._name = name
        self._fim_uid = fim_uid

    def get_name(self):
        """Returns the name of the device"""
        return self._name

    def get_fim_uid(self):
        """Returns the FIM UID of the device"""
        return self._fim_uid

    def set_name(self, name):
        """Sets the name of the device"""
        self._name = name

    def set_fim_uid(self, fim_uid):
        """"Sets the FIM UID of the device"""
        self._fim_uid = fim_uid
