"""General exceptions."""


class WrongCredentialsError(Exception):
    """Wrong credentials were used."""

    def __init__(self) -> None:
        """Initialize error."""
        super().__init__("Wrong username or password.")


class WrongUrlError(Exception):
    """Wrong URL was used."""

    def __init__(self, url: str) -> None:
        """Initialize error."""
        super().__init__(f"Wrong URL: {url}")
