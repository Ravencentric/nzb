from __future__ import annotations

import gzip
from pathlib import Path
from typing import TYPE_CHECKING
from xml.parsers.expat import ExpatError

import xmltodict

from nzb._exceptions import InvalidNzbError

if TYPE_CHECKING:
    from collections.abc import Iterable
    from typing import Any

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
                raise InvalidNzbError(f"Gzip decompression error for file '{file}': {e}") from None
        else:
            data = file.read_text(encoding=encoding, errors=errors)
    except (OSError, UnicodeError) as e:
        raise InvalidNzbError(f"I/O error while reading file '{file}': {e}") from None

    return data


def nzb_to_dict(nzb: str) -> dict[str, Any]:
    """
    xmltodict.parse() raises ExpatError if there's a newline at the start,
    so we use this wrapper that calls .strip() before passing it on to xmltodict.
    """
    try:
        return xmltodict.parse(nzb.strip())
    except ExpatError as e:
        raise InvalidNzbError(f"The NZB document is not valid XML and could not be parsed: {e.args[0]}") from None


def construct_meta(
    title: str | None = None,
    passwords: Iterable[str] | str | None = None,
    tags: Iterable[str] | str | None = None,
    category: str | None = None,
) -> list[dict[str, str]]:
    """
    Construct `<meta> .. </meta>` fields.
    """

    meta = []

    if title:
        meta.append({"@type": "title", "#text": title})

    if passwords:
        if isinstance(passwords, str):
            meta.append({"@type": "password", "#text": passwords})
        else:
            for password in passwords:
                meta.append({"@type": "password", "#text": password})  # noqa: PERF401

    if tags:
        if isinstance(tags, str):
            meta.append({"@type": "tag", "#text": tags})
        else:
            for tag in tags:
                meta.append({"@type": "tag", "#text": tag})  # noqa: PERF401

    if category:
        meta.append({"@type": "category", "#text": category})

    return meta


def sort_meta(meta: list[dict[str, str]]) -> list[dict[str, str]]:
    """
    Sort meta list elements based on predefined hierarchy.

    This function provides a sorting key for meta elements, prioritizing them in the following order:
    title (0) > category (1) > password (2) > tag (3) > everything else (-1)

    Parameters
    ----------
    meta : list[dict[str, str]]
        List of metadata dictionaries, where each dictionary contains '@type' and '#text' keys

    Returns
    -------
    list[dict[str, str]]
        Sorted list of meta dicts

    Examples
    --------
    >>> meta = [
    ...     {"@type": "title", "#text": "Big Buck Bunny - S01E01.mkv"},
    ...     {"@type": "password", "#text": "secret"},
    ...     {"@type": "tag", "#text": "HD"},
    ...     {"@type": "category", "#text": "TV"},
    ... ]
    >>> sort_meta(meta)

    """

    def key(k: dict[str, str]) -> int:
        sort_keys = {"title": 0, "category": 1, "password": 2, "tag": 3}
        typ = k["@type"].strip().casefold()
        return sort_keys.get(typ, -1)

    return sorted(meta, key=key)


def remove_meta_fields(
    meta: list[dict[str, str]],
    fields: Iterable[str] | None = None,
) -> list[dict[str, str]]:
    """
    Remove specified fields from meta list.

    Parameters
    ----------
    meta : list[dict[str, str]]
        List of metadata dictionaries
    fields : Iterable[str]] | None
        Fields to remove from meta list. If None, return original meta list.

    Returns
    -------
    list[dict[str, str]]
        Meta list with specified fields removed

    """
    if fields is None:
        return meta

    fields_set = {field.strip().casefold() for field in fields}
    return [item for item in meta if item["@type"].strip().casefold() not in fields_set]
