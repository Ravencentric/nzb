from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import ParamSpec, TypeVar

    T = TypeVar("T")
    P = ParamSpec("P")

    def cache(_: Callable[P, T], /) -> Callable[P, T]: ...
else:
    from functools import cache


@cache
def extract_filename_from_subject(subject: str) -> str | None:
    """
    Extract the complete name of the file with it's extension from the subject.
    May return `None` if it fails to extract the name.

    Parameters
    ----------
    subject : str
        The subject string.

    Returns
    -------
    str | None

    """
    # The order of regular expressions is deliberate; patterns are arranged
    # from most specific to most general to avoid broader patterns incorrectly matching.

    # Case 1: Filename is in quotes.
    # https://github.com/sabnzbd/sabnzbd/blob/02b4a116dd4b46b2d2f33f7bbf249f2294458f2e/sabnzbd/nzbstuff.py#L104-L106
    if parsed := re.search(r'"([^"]*)"', subject):
        return parsed.group(1).strip()

    # Case 2: Subject follows a specific pattern.
    # https://regex101.com/r/B03qZs/2
    # [011/116] - [AC-FFF] Highschool DxD BorN - 02 [BD][1080p-Hi10p] FLAC][Dual-Audio][442E5446].mkv yEnc (1/2401) 1720916370  # noqa: E501
    if parsed := re.fullmatch(
        r"^(?:\[|\()(?:\d+/\d+)(?:\]|\))\s-\s(.*)\syEnc\s(?:\[|\()(?:\d+/\d+)(?:\]|\))\s\d+", subject
    ):
        return parsed.group(1).strip()

    # Case 3: Something that might look like a filename.
    # # https://github.com/sabnzbd/sabnzbd/blob/02b4a116dd4b46b2d2f33f7bbf249f2294458f2e/sabnzbd/nzbstuff.py#L104-L106
    if parsed := re.search(r"\b([\w\-+()' .,]+(?:\[[\w\-/+()' .,]*][\w\-+()' .,]*)*\.[A-Za-z0-9]{2,4})\b", subject):
        return parsed.group(1).strip()

    return None


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
