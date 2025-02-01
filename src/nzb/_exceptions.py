from __future__ import annotations


class InvalidNzbError(Exception):
    """Invalid NZB."""

    def __init__(self, message: str) -> None:
        self.message = message
        """Human readable error message."""
        super().__init__(message)

    def __str__(self) -> str:
        """Equivalent to accessing the .message attribute."""
        return self.message

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}("{self.message}")'
