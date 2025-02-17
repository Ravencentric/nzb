from __future__ import annotations

import gzip
import re
from functools import cache
from pathlib import Path
from typing import TYPE_CHECKING
from xml.parsers.expat import ExpatError

import xmltodict

from nzb._exceptions import InvalidNzbError

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable
    from typing import Any, ParamSpec, TypeVar

    from nzb._types import StrPath

    T = TypeVar("T")
    P = ParamSpec("P")

    def cache(user_function: Callable[P, T], /) -> Callable[P, T]:  # type: ignore[misc]
        return user_function


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

    # TODO: reject large files?

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


@cache
def name_is_par2(filename: str) -> bool:
    """
    Determine if a given file is likely a par2 file.

    Parameters
    ----------
    filename : str
        Name of the file with it's extension, i.e., the final component in a path.

    Returns
    -------
    bool

    """
    if not filename:
        return False
    else:
        parsed = re.search(r"\.par2$", filename, re.IGNORECASE)
        return True if parsed else False


@cache
def name_is_rar(filename: str) -> bool:
    """
    Determine if a given file is likely a rar file.

    Parameters
    ----------
    filename : str
        Name of the file with it's extension, i.e., the final component in a path.

    Returns
    -------
    bool

    Notes
    -----
    The regex used here was copy-pasted from SABnzbd:
    https://github.com/sabnzbd/sabnzbd/blob/02b4a116dd4b46b2d2f33f7bbf249f2294458f2e/sabnzbd/nzbstuff.py#L107

    """
    if not filename:
        return False
    else:
        parsed = re.search(r"(\.rar|\.r\d\d|\.s\d\d|\.t\d\d|\.u\d\d|\.v\d\d)$", filename, re.IGNORECASE)
        return True if parsed else False


@cache
def stem_is_obfuscated(filestem: str) -> bool:  # pragma: no cover
    """
    Determine if a given file stem is likely obfuscated.

    Parameters
    ----------
    filestem : str
        The filestem (i.e., the name of the file without the extension)

    Returns
    -------
    bool
        True if the filestem is considered obfuscated, False otherwise.

    Notes
    -----
    This function was copy-pasted from SABnzbd:
    https://github.com/sabnzbd/sabnzbd/blob/297455cd35c71962d39a36b7f99622f905d2234e/sabnzbd/deobfuscate_filenames.py#L104

    """
    if not filestem:
        return True

    # First: the patterns that are certainly obfuscated:

    # ...blabla.H.264/b082fa0beaa644d3aa01045d5b8d0b36.mkv is certainly obfuscated
    if re.findall(r"^[a-f0-9]{32}$", filestem):
        # exactly 32 hex digits, so:
        return True

    # 0675e29e9abfd2.f7d069dab0b853283cc1b069a25f82.6547
    if re.findall(r"^[a-f0-9.]{40,}$", filestem):
        return True

    # "[BlaBla] something [More] something 5937bc5e32146e.bef89a622e4a23f07b0d3757ad5e8a.a02b264e [Brrr]"
    # So: square brackets plus 30+ hex digit
    if re.findall(r"[a-f0-9]{30}", filestem) and len(re.findall(r"\[\w+\]", filestem)) >= 2:
        return True

    # /some/thing/abc.xyz.a4c567edbcbf27.BLA is certainly obfuscated
    if re.findall(r"^abc\.xyz", filestem):
        # ... which we consider as obfuscated:
        return True

    # Then: patterns that are not obfuscated but typical, clear names:

    # these are signals for the obfuscation versus non-obfuscation
    decimals = sum(1 for c in filestem if c.isnumeric())
    upperchars = sum(1 for c in filestem if c.isupper())
    lowerchars = sum(1 for c in filestem if c.islower())
    spacesdots = sum(1 for c in filestem if c == " " or c == "." or c == "_")  # space-like symbols

    # Example: "Great Distro"
    if upperchars >= 2 and lowerchars >= 2 and spacesdots >= 1:
        return False

    # Example: "this is a download"
    if spacesdots >= 3:
        return False

    # Example: "Beast 2020"
    if (upperchars + lowerchars >= 4) and decimals >= 4 and spacesdots >= 1:
        return False

    # Example: "Catullus", starts with a capital, and most letters are lower case
    if filestem[0].isupper() and lowerchars > 2 and upperchars / lowerchars <= 0.25:
        return False

    # Finally: default to obfuscated:
    return True  # default is obfuscated
