"""
This class is intended to be inherited by every other property class
"""


class Property:
    def __init__(self, element_uid):
        self.element_uid = element_uid
