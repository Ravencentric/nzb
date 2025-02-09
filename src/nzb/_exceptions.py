from __future__ import annotations

from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from typing_extensions import Self


class InvalidNzbError(Exception):
    """Invalid NZB."""

    def __init__(self, message: str) -> None:
        self.message = message
        """Human readable error message."""
        super().__init__(message)

    @classmethod
    def _from_preset(cls, preset: Literal["groups", "segments", "file"]) -> Self:
        """
        Create an InvalidNzbError from a predefined error preset.

        Parameters
        ----------
        preset : Literal["groups", "segments", "file"]
            Preset identifier.

        Returns
        -------
        InvalidNzbError
            InvalidNzbError instance with the corresponding preset message.

        Raises
        ------
        ValueError
            If `preset` is not a valid identifier.

        """
        match preset:
            case "file":
                return cls(
                    "Invalid or missing 'file' element in the NZB document. "
                    + "The NZB document must contain at least one valid 'file' element, "
                    + "and each 'file' must have at least one valid 'groups' and 'segments' element."
                )
            case "groups":
                return cls(
                    "Invalid or missing 'groups' element within the 'file' element. "
                    + "Each 'file' element must contain at least one valid 'groups' element."
                )
            case "segments":
                return cls(
                    "Invalid or missing 'segments' element within the 'file' element. "
                    + "Each 'file' element must contain at least one valid 'segments' element."
                )
            case _:
                raise ValueError(f"Invalid preset: {preset}")

    def __str__(self) -> str:
        """Equivalent to accessing the .message attribute."""
        return self.message

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}("{self.message}")'

    def __hash__(self) -> int:
        return hash(self.message)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, InvalidNzbError):
            return False
        return self.message == other.message
