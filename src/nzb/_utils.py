from __future__ import annotations

from typing import Iterable


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
