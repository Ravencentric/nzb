from __future__ import annotations

import gzip
from collections.abc import Iterable
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
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

    if file.suffix.casefold() == ".gz":
        # gzipped nzbs are fairly common (e.g., all of AnimeTosho)
        with gzip.open(file) as f:
            data = f.read().decode(encoding=encoding, errors=errors).strip()

    else:
        data = file.read_text(encoding=encoding, errors=errors)

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
