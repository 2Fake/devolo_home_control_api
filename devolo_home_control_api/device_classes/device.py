"""
This class is intended to be inherited by every other device class
"""


class Device:
    def __init__(self, name, fim_uid):
        self.name = name
        self.fim_uid = fim_uid


