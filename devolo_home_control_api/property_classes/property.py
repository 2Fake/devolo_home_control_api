"""
This class is intended to be inherited by every other property class
"""


class Property:
    def __init__(self, element_uid):
        self._element_uid = element_uid

    def get_element_uid(self):
        return self._element_uid
