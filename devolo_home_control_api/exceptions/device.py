"""Exceptions occuring when talking to a Z-Wave device."""
import re


class WrongElementError(Exception):
    """The element was not meant for this property."""

    def __init__(self, element_uid: str, property_class: str) -> None:
        """Initialize error."""
        property_name = " ".join(re.findall("[A-Z][^A-Z]*", property_class)).lower()
        super().__init__(f"{element_uid} is not a {property_name}.")


class SwitchingProtected(Exception):
    """The device is protected against remote switching."""

    def __init__(self) -> None:
        """Initialize error."""
        super().__init__("This device is protected against remote switching.")
