from __future__ import annotations

import gzip
from collections.abc import Iterable
from pathlib import Path
from typing import TYPE_CHECKING

from nzb._exceptions import InvalidNzbError

if TYPE_CHECKING:
    from typing import TypeVar

    T = TypeVar("T")
    T2 = TypeVar("T2")

    from _typeshed import StrPath


def realpath(path: StrPath, /) -> Path:
    """
    Canonicalize a given path.
    """
    return Path(path).expanduser().resolve()


def read_nzb_file(path: StrPath, /) -> str:
    """
    Read a text file and return its content as a string.
    Handles both plain text and gzipped (.gz) files.
    """
    file = realpath(path)
    encoding = "utf-8"
    errors = "strict"

    if not file.is_file():
        raise FileNotFoundError(file)

    try:
        if file.suffix.casefold() == ".gz":
            # gzipped nzbs are fairly common (e.g., all of AnimeTosho)
            try:
                with gzip.open(file) as f:
                    data = f.read().decode(encoding=encoding, errors=errors).strip()
            except gzip.BadGzipFile as e:
                msg = f"Gzip decompression error for file '{file}': {e}"
                raise InvalidNzbError(msg) from None
        else:
            data = file.read_text(encoding=encoding, errors=errors)
    except (OSError, UnicodeError) as e:
        msg = f"I/O error while reading file '{file}': {e}"
        raise InvalidNzbError(msg) from None

    return data


def to_iterable(obj: str | Iterable[str] | None) -> Iterable[str]:
    if obj is None:
        return ()
    if isinstance(obj, str):
        return (obj,)
    if isinstance(obj, Iterable):
        return obj
    msg = f"Expected a string, an iterable of strings, or None, got {type(obj).__name__}"
    raise TypeError(msg)
