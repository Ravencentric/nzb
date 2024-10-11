from __future__ import annotations

import re
from functools import cache
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable
    from typing import Callable, ParamSpec, TypeVar

    from nzb._types import StrPath

    T = TypeVar("T")
    P = ParamSpec("P")

    def cache(user_function: Callable[P, T], /) -> Callable[P, T]:  # type: ignore
        return user_function


def realpath(path: StrPath, /) -> Path:
    """
    Canonicalize a given path.
    """
    return Path(path).expanduser().resolve()


def meta_constructor(
    title: str | None = None,
    passwords: Iterable[str] | str | None = None,
    tags: Iterable[str] | str | None = None,
    category: str | None = None,
) -> list[dict[str, str]]:
    """
    Constructor that constructs valid `<meta> .. </meta>` fields
    """

    meta = []

    if title:
        meta.append({"@type": "title", "#text": title})

    if passwords:
        if isinstance(passwords, str):
            meta.append({"@type": "password", "#text": passwords})
        else:
            for password in passwords:
                meta.append({"@type": "password", "#text": password})

    if tags:
        if isinstance(tags, str):
            meta.append({"@type": "tag", "#text": tags})
        else:
            for tag in tags:
                meta.append({"@type": "tag", "#text": tag})

    if category:
        meta.append({"@type": "category", "#text": category})

    return meta


@cache
def name_is_par2(filename: str) -> bool:
    """
    Determine if a given file is likely a par2 file.

    Parameters
    ----------
    filename : str

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
