"""Helper functions for converting strings

The information we get from the gateway is often returned in a way, that does not fit to our naming convention. This helper
function make names fit in nicely.
"""

import re


def camel_case_to_snake_case(expression: str) -> str:
    """
    Turn CamelCaseStrings to snake_case_strings. This is used where the original Java names should by more pythonic.

    :param: expression: Expression, that should be converted to snake case
    :return: Expression in snake case
    """
    return re.sub("([a-z])([A-Z]+)", r"\1_\2", expression).lower()
